from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import BaseModel

from app.schemas import PacketType, SensorPacketCreate


class EmergencyResult(BaseModel):
    is_emergency: bool
    event_type: str | None = None
    remarks: str | None = None


def detect_emergency(
    packet: SensorPacketCreate,
) -> EmergencyResult:
    if packet.packet_type == PacketType.HEARTBEAT:
        return EmergencyResult(
            is_emergency=False,
            remarks="Heartbeat packet received.",
        )

    if packet.packet_type == PacketType.SOS:
        return EmergencyResult(
            is_emergency=True,
            event_type="SOS",
            remarks="Manual SOS distress button activated.",
        )

    if packet.packet_type == PacketType.FALL:
        return EmergencyResult(
            is_emergency=True,
            event_type="FALL",
            remarks="Automatic fall detection triggered by wearable node.",
        )

    if packet.packet_type == PacketType.HAZARD:
        return EmergencyResult(
            is_emergency=True,
            event_type="HAZARD",
            remarks="Hazard / vital threshold warning reported.",
        )

    return EmergencyResult(
        is_emergency=False,
        remarks="Standard non-emergency transmission.",
    )