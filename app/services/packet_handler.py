import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud
from app.schemas import PacketProcessingResult, PacketType, SensorPacketCreate
from app.services.emergency_detector import detect_emergency
from app.services.websocket_manager import manager as ws_manager

logger = logging.getLogger("gateway.packet_handler")


def process_packet(
    db: Session,
    packet: SensorPacketCreate,
) -> PacketProcessingResult:
    """
    Main packet processing engine.
    - HEARTBEAT packets update Node state only. No logs/events created.
    - EMERGENCY packets (SOS, FALL, HAZARD) perform duplicate checks,
      update Node, create SensorLog, PacketLog, EmergencyEvent.
    """
    try:
        # CATEGORY 1: HEARTBEAT PACKETS
        if packet.packet_type == PacketType.HEARTBEAT:
            node = crud.update_node_heartbeat(db=db, packet=packet)
            db.commit()
            logger.info(f"[HEARTBEAT] Processed for Node {packet.node_id}. Battery: {packet.battery}%")

            return PacketProcessingResult(
                success=True,
                duplicate=False,
                packet_id=packet.packet_id,
                node_id=packet.node_id,
                packet_type=packet.packet_type,
                emergency_detected=False,
                ack_status=True,
                message=f"Heartbeat received for Node {packet.node_id}. Status updated to ONLINE.",
            )

        # CATEGORY 2: EMERGENCY PACKETS (SOS, FALL, HAZARD)
        # Duplicate check for emergency packets
        if crud.packet_exists(db=db, packet_id=packet.packet_id):
            logger.warning(f"[DUPLICATE] Emergency packet {packet.packet_id} already processed.")
            return PacketProcessingResult(
                success=True,
                duplicate=True,
                packet_id=packet.packet_id,
                node_id=packet.node_id,
                packet_type=packet.packet_type,
                emergency_id=packet.emergency_id,
                sequence_number=packet.sequence_number,
                emergency_detected=True,
                ack_status=True,
                message="Duplicate emergency packet detected and ignored.",
            )

        emergency = detect_emergency(packet)

        # Emergency DB Pipeline
        crud.create_or_update_node(db=db, packet=packet)
        crud.create_sensor_log(db=db, packet=packet)
        crud.create_or_update_emergency_event(db=db, packet=packet, emergency=emergency)
        packet_log = crud.create_packet_log(db=db, packet=packet)

        db.commit()

        logger.info(f"[EMERGENCY] {packet.packet_type.value} processed for Node {packet.node_id}. PacketID: {packet.packet_id}")

        return PacketProcessingResult(
            success=True,
            duplicate=False,
            packet_id=packet.packet_id,
            node_id=packet.node_id,
            packet_type=packet.packet_type,
            emergency_id=packet.emergency_id,
            sequence_number=packet.sequence_number,
            emergency_detected=True,
            emergency_type=emergency.event_type,
            ack_status=packet_log.ack_status,
            message=f"Emergency packet {packet.packet_type.value} processed successfully.",
        )

    except SQLAlchemyError as exc:
        db.rollback()
        logger.error(f"Database processing failed for packet {packet.packet_id}: {exc}")
        return PacketProcessingResult(
            success=False,
            duplicate=False,
            packet_id=packet.packet_id,
            node_id=packet.node_id,
            packet_type=packet.packet_type,
            emergency_detected=False,
            ack_status=False,
            message=f"Database processing error: {exc}",
        )

    except Exception as exc:
        db.rollback()
        logger.exception(f"Unexpected error processing packet {packet.packet_id}: {exc}")
        return PacketProcessingResult(
            success=False,
            duplicate=False,
            packet_id=packet.packet_id,
            node_id=packet.node_id,
            packet_type=packet.packet_type,
            emergency_detected=False,
            ack_status=False,
            message=f"Packet processing failed: {exc}",
        )