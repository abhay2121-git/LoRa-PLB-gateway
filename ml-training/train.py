"""Train and export the priority model outside the deployed app package."""

import argparse
import pickle
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

FEATURES = ["packet_type", "heart_rate", "spo2", "battery", "retry_count", "hop_count"]
NUMERIC_FEATURES = FEATURES[1:]
PACKET_TYPES = ["SOS", "HAZARD", "MESSAGE"]
PACKET_TYPE_CODES = {"SOS": 1, "HAZARD": 2, "MESSAGE": 3}


def prototype_data() -> pd.DataFrame:
    """Create clearly synthetic development data; never used as validation evidence."""
    rows = []
    for packet_index in range(300):
        packet_type = PACKET_TYPES[packet_index % 3]
        heart_rate = [72, 118, 145][packet_index % 3] + (packet_index % 5)
        spo2 = [98, 94, 88][packet_index % 3] - (packet_index % 3)
        battery = 95 - (packet_index % 80)
        retry_count = packet_index % 4
        hop_count = 1 + (packet_index % 3)
        priority = 4 if packet_type == "SOS" else 3 if packet_type == "HAZARD" else 2 if retry_count > 1 else 1
        rows.append([packet_type, heart_rate, spo2, battery, retry_count, hop_count, priority])
    return pd.DataFrame(rows, columns=FEATURES + ["priority"])


def load_dataset(path: Path | None, use_synthetic: bool) -> pd.DataFrame:
    if use_synthetic:
        data = prototype_data()
    else:
        if path is None:
            raise ValueError("Provide --dataset or explicitly pass --synthetic for prototype data.")
        data = pd.read_excel(path)
    missing = set(FEATURES + ["priority"]) - set(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    data = data[FEATURES + ["priority"]].dropna().copy()
    data["packet_type"] = data["packet_type"].map(
        lambda value: str(PACKET_TYPE_CODES.get(str(value).upper(), value))
    )
    if not data["packet_type"].isin(["1", "2", "3"]).all():
        raise ValueError("packet_type must contain SOS/HAZARD/MESSAGE or codes 1/2/3")
    return data


def train(data: pd.DataFrame):
    data = data.copy()
    data["packet_type"] = data["packet_type"].map(
        lambda value: str(PACKET_TYPE_CODES.get(str(value).upper(), value))
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("packet_type", OneHotEncoder(categories=[["1", "2", "3"]], handle_unknown="ignore"), ["packet_type"]),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ],
        verbose_feature_names_out=False,
    )
    transformed = preprocessor.fit_transform(data[FEATURES])
    model = RandomForestClassifier(n_estimators=80, max_depth=8, random_state=42, n_jobs=1)
    model.fit(transformed, data["priority"].astype(int))
    return model, preprocessor


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--synthetic", action="store_true", help="Use prototype-only synthetic data.")
    args = parser.parse_args()
    data = load_dataset(args.dataset, args.synthetic)
    model, preprocessor = train(data)
    model_path = args.output_dir / "app" / "ml" / "model" / "priority_model.pkl"
    preprocessor_path = args.output_dir / "app" / "ml" / "preprocessing" / "preprocessor.pkl"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    preprocessor_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as model_file:
        pickle.dump(model, model_file)
    with preprocessor_path.open("wb") as preprocessor_file:
        pickle.dump(preprocessor, preprocessor_file)
    print(f"Exported model to {model_path}")
    print(f"Exported preprocessor to {preprocessor_path}")


if __name__ == "__main__":
    main()