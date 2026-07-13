from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud
from app.emergency_detector import detect_emergency
from app.schemas import SensorPacketCreate


class PacketProcessingResult(BaseModel):
    success: bool
    duplicate: bool
    packet_id: str
    emergency_id: str
    node_id: str
    sequence_number: int
    emergency_detected: bool = False
    emergency_type: str | None = None
    ack_status: bool = False
    message: str = ""


def process_packet(
    db: Session,
    packet: SensorPacketCreate,
) -> PacketProcessingResult:

    try:
        if crud.packet_exists(
            db=db,
            packet_id=packet.packet_id,
        ):
            return PacketProcessingResult(
                success=True,
                duplicate=True,
                packet_id=packet.packet_id,
                emergency_id=packet.emergency_id,
                node_id=packet.node_id,
                sequence_number=packet.sequence_number,
                message=(
                    "Duplicate packet detected and ignored."
                ),
            )

        emergency = detect_emergency(packet)

        if not emergency.is_emergency:
            return PacketProcessingResult(
                success=False,
                duplicate=False,
                packet_id=packet.packet_id,
                emergency_id=packet.emergency_id,
                node_id=packet.node_id,
                sequence_number=packet.sequence_number,
                message="Non-emergency packet rejected.",
            )

        crud.create_or_update_node(
            db=db,
            packet=packet,
        )

        crud.create_sensor_log(
            db=db,
            packet=packet,
        )

        crud.create_or_update_emergency_event(
            db=db,
            packet=packet,
            emergency=emergency,
        )

        packet_log = crud.create_packet_log(
            db=db,
            packet=packet,
        )

        db.commit()

        return PacketProcessingResult(
            success=True,
            duplicate=False,
            packet_id=packet.packet_id,
            emergency_id=packet.emergency_id,
            node_id=packet.node_id,
            sequence_number=packet.sequence_number,
            emergency_detected=True,
            emergency_type=emergency.event_type,
            ack_status=packet_log.ack_status,
            message="Emergency packet processed successfully.",
        )

    except SQLAlchemyError as exc:
        db.rollback()

        return PacketProcessingResult(
            success=False,
            duplicate=False,
            packet_id=packet.packet_id,
            emergency_id=packet.emergency_id,
            node_id=packet.node_id,
            sequence_number=packet.sequence_number,
            message=f"Database processing failed: {exc}",
        )

    except Exception as exc:
        db.rollback()

        return PacketProcessingResult(
            success=False,
            duplicate=False,
            packet_id=packet.packet_id,
            emergency_id=packet.emergency_id,
            node_id=packet.node_id,
            sequence_number=packet.sequence_number,
            message=f"Packet processing failed: {exc}",
        )