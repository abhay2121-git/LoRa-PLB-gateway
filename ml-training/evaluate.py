"""Evaluate a trained priority model with per-class metrics."""

import argparse
import pickle
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

from train import load_dataset, train


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    data = load_dataset(args.dataset, args.synthetic)
    train_data, test_data = train_test_split(data, test_size=0.2, random_state=42, stratify=data["priority"])
    model, preprocessor = train(train_data)
    predicted = model.predict(preprocessor.transform(test_data[["packet_type", "heart_rate", "spo2", "battery", "retry_count", "hop_count"]]))
    actual = test_data["priority"].astype(int)
    print(f"Class distribution:\n{data['priority'].value_counts().sort_index()}")
    print(f"Accuracy: {accuracy_score(actual, predicted):.4f}")
    print(f"Precision (macro): {precision_score(actual, predicted, average='macro', zero_division=0):.4f}")
    print(f"Recall (macro): {recall_score(actual, predicted, average='macro', zero_division=0):.4f}")
    print(f"F1 (macro): {f1_score(actual, predicted, average='macro', zero_division=0):.4f}")
    print("Confusion matrix (labels 1, 2, 3, 4):")
    print(confusion_matrix(actual, predicted, labels=[1, 2, 3, 4]))
    print("Classification report:")
    print(classification_report(actual, predicted, labels=[1, 2, 3, 4], zero_division=0))


if __name__ == "__main__":
    main()