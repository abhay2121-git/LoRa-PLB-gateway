import logging
import pickle
from numbers import Real
from typing import Any, Mapping

import pandas as pd

from app.ml.config import (
    MODEL_PATH,
    PACKET_TYPE_CODES,
    PREPROCESSOR_PATH,
    PRIORITY_LABELS,
    REQUIRED_FEATURES,
    SUPPORTED_PACKET_TYPES,
)

logger = logging.getLogger("gateway.ml.predictor")


class PriorityPredictionError(ValueError):
    """Raised when priority inference cannot be completed safely."""


_model: Any | None = None
_preprocessor: Any | None = None


def _load_artifact(path):
    if not path.is_file():
        raise PriorityPredictionError(f"ML artifact not found: {path}")
    try:
        with path.open("rb") as artifact_file:
            return pickle.load(artifact_file)
    except Exception as exc:
        raise PriorityPredictionError(f"Could not load ML artifact {path}: {exc}") from exc


def load_model():
    global _model
    if _model is None:
        _model = _load_artifact(MODEL_PATH)
        logger.info("Priority model loaded successfully from %s", MODEL_PATH)
    return _model


def load_preprocessor():
    global _preprocessor
    if _preprocessor is None:
        _preprocessor = _load_artifact(PREPROCESSOR_PATH)
        logger.info("Priority preprocessor loaded successfully from %s", PREPROCESSOR_PATH)
    return _preprocessor


def _extract_features(packet: Mapping[str, Any]) -> dict[str, Any]:
    packet_type = packet.get("packet_type")
    if hasattr(packet_type, "value"):
        packet_type = packet_type.value
    packet_type = str(packet_type).upper() if packet_type is not None else None
    if packet_type not in SUPPORTED_PACKET_TYPES:
        raise PriorityPredictionError(f"Unsupported packet type for priority inference: {packet_type}")

    features = {name: packet.get(name) for name in REQUIRED_FEATURES}
    features["packet_type"] = str(PACKET_TYPE_CODES[packet_type])
    missing = [name for name, value in features.items() if value is None]
    if missing:
        raise PriorityPredictionError(f"Missing required priority features: {', '.join(missing)}")
    for name in REQUIRED_FEATURES[1:]:
        if not isinstance(features[name], Real) or isinstance(features[name], bool):
            raise PriorityPredictionError(f"Invalid numeric priority feature: {name}")
    return features


def predict_priority(packet: Mapping[str, Any]) -> dict[str, int | str]:
    features = _extract_features(packet)
    try:
        transformed = load_preprocessor().transform(pd.DataFrame([features], columns=REQUIRED_FEATURES))
        prediction = int(load_model().predict(transformed)[0])
    except PriorityPredictionError:
        raise
    except Exception as exc:
        raise PriorityPredictionError(f"Priority prediction failed: {exc}") from exc

    label = PRIORITY_LABELS.get(prediction)
    if label is None:
        raise PriorityPredictionError(f"Model returned unsupported priority code: {prediction}")
    logger.info("Priority prediction completed for packet type %s: %s", features["packet_type"], label)
    return {"priority_code": prediction, "priority": label}