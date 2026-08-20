from pathlib import Path

import pytest

from app.ml import predictor
from app.ml.config import PRIORITY_LABELS
from app.ml.inference import infer_priority, resolve_packet_type
from app.ml.predictor import PriorityPredictionError
from app.schemas import PacketType, SensorPacketCreate


def packet(packet_type: PacketType, message: str | None = None) -> SensorPacketCreate:
    return SensorPacketCreate(
        packet_id=f"TEST-{packet_type.value}-{message or 'NORMAL'}",
        node_id="NODE_TEST",
        packet_type=packet_type,
        battery=75,
        heart_rate=80,
        spo2=98,
        retry_count=0,
        hop_count=1,
        message=message,
    )


def test_model_and_preprocessor_load_once():
    predictor._model = None
    predictor._preprocessor = None
    assert predictor.load_model() is predictor.load_model()
    assert predictor.load_preprocessor() is predictor.load_preprocessor()


@pytest.mark.parametrize("packet_type", [PacketType.SOS, PacketType.HAZARD, PacketType.MESSAGE])
def test_supported_packet_prediction_contract(packet_type):
    result = infer_priority(packet(packet_type))
    assert set(result) == {"priority_code", "priority"}
    assert result["priority_code"] in PRIORITY_LABELS
    assert result["priority"] == PRIORITY_LABELS[result["priority_code"]]


def test_message_sos_is_resolved_before_prediction():
    resolved = resolve_packet_type(packet(PacketType.MESSAGE, " sos "))
    assert resolved.packet_type == PacketType.SOS
    assert infer_priority(resolved)["priority"] in PRIORITY_LABELS.values()


def test_message_hazard_is_resolved_before_prediction():
    resolved = resolve_packet_type(packet(PacketType.MESSAGE, "HAZARD"))
    assert resolved.packet_type == PacketType.HAZARD


def test_normal_message_remains_message():
    assert resolve_packet_type(packet(PacketType.MESSAGE, "Need water")).packet_type == PacketType.MESSAGE


def test_heartbeat_is_excluded():
    with pytest.raises(PriorityPredictionError, match="excluded"):
        infer_priority(packet(PacketType.HEARTBEAT))


def test_missing_feature_is_rejected():
    values = packet(PacketType.SOS).model_dump()
    values.pop("spo2")
    with pytest.raises(PriorityPredictionError, match="spo2"):
        infer_priority(values)


def test_invalid_packet_type_is_rejected():
    values = packet(PacketType.SOS).model_dump()
    values["packet_type"] = "HEARTBEAT"
    with pytest.raises(PriorityPredictionError, match="Unsupported"):
        infer_priority(values)


def test_missing_model_is_controlled(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(predictor, "MODEL_PATH", tmp_path / "missing.pkl")
    predictor._model = None
    with pytest.raises(PriorityPredictionError, match="not found"):
        predictor.load_model()
    predictor._model = None


def test_missing_preprocessor_is_controlled(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(predictor, "PREPROCESSOR_PATH", tmp_path / "missing.pkl")
    predictor._preprocessor = None
    with pytest.raises(PriorityPredictionError, match="not found"):
        predictor.load_preprocessor()
    predictor._preprocessor = None