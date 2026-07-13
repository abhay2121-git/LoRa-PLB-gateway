from datetime import datetime, UTC
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.emergency_detector import EmergencyResult
from app.schemas import SensorPacketCreate


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_packet_by_packet_id(
    db: Session,
    packet_id: str,
) -> models.PacketLog | None:
    statement = select(models.PacketLog).where(
        models.PacketLog.packet_id == packet_id
    )

    return db.scalar(statement)


def packet_exists(
    db: Session,
    packet_id: str,
) -> bool:
    return get_packet_by_packet_id(
        db=db,
        packet_id=packet_id,
    ) is not None


def get_node_by_node_id(
    db: Session,
    node_id: str,
) -> models.Node | None:
    statement = select(models.Node).where(
        models.Node.node_id == node_id
    )

    return db.scalar(statement)


def get_emergency_by_emergency_id(
    db: Session,
    emergency_id: str,
) -> models.EmergencyEvent | None:
    statement = select(models.EmergencyEvent).where(
        models.EmergencyEvent.emergency_id == emergency_id
    )

    return db.scalar(statement)


def create_or_update_node(
    db: Session,
    packet: SensorPacketCreate,
) -> models.Node:
    node = get_node_by_node_id(
        db=db,
        node_id=packet.node_id,
    )

    current_time = utc_now()

    if node is None:
        node = models.Node(
            node_id=packet.node_id,
            status="ONLINE",
            battery=packet.battery,
            last_seen=current_time,
        )

        db.add(node)

    else:
        node.status = "ONLINE"
        node.battery = packet.battery
        node.last_seen = current_time

    db.flush()

    return node


def create_sensor_log(
    db: Session,
    packet: SensorPacketCreate,
) -> models.SensorLog:
    sensor_log = models.SensorLog(
        emergency_id=packet.emergency_id,
        node_id=packet.node_id,
        sequence_number=packet.sequence_number,
        latitude=packet.latitude,
        longitude=packet.longitude,
        heart_rate=packet.heart_rate,
        spo2=packet.spo2,
        temperature=packet.temperature,
        fall_detected=packet.fall_detected,
        sos=packet.sos,
        battery=packet.battery,
    )

    db.add(sensor_log)
    db.flush()

    return sensor_log


def create_or_update_emergency_event(
    db: Session,
    packet: SensorPacketCreate,
    emergency: EmergencyResult,
) -> models.EmergencyEvent:
    if not emergency.is_emergency:
        raise ValueError(
            "Cannot process a non-emergency event."
        )

    emergency_event = get_emergency_by_emergency_id(
        db=db,
        emergency_id=packet.emergency_id,
    )

    if emergency_event is None:
        emergency_event = models.EmergencyEvent(
            emergency_id=packet.emergency_id,
            node_id=packet.node_id,
            event_type=emergency.event_type,
            latitude=packet.latitude,
            longitude=packet.longitude,
            last_sequence_number=packet.sequence_number,
            resolved=False,
            remarks=emergency.remarks,
        )

        db.add(emergency_event)

    elif packet.sequence_number > emergency_event.last_sequence_number:
        emergency_event.latitude = packet.latitude
        emergency_event.longitude = packet.longitude
        emergency_event.last_sequence_number = (
            packet.sequence_number
        )
        emergency_event.updated_at = utc_now()

    db.flush()

    return emergency_event


def create_packet_log(
    db: Session,
    packet: SensorPacketCreate,
) -> models.PacketLog:
    packet_log = models.PacketLog(
        packet_id=packet.packet_id,
        emergency_id=packet.emergency_id,
        sequence_number=packet.sequence_number,
        sender_node_id=packet.node_id,
        receiver_id=settings.gateway_id,
        packet_type=packet.packet_type.value,
        ack_status=False,
        retry_count=packet.retry_count,
    )

    db.add(packet_log)
    db.flush()

    return packet_log


def get_all_nodes(
    db: Session,
) -> list[models.Node]:
    statement = select(models.Node).order_by(
        models.Node.node_id
    )

    return list(db.scalars(statement).all())


def get_all_sensor_logs(
    db: Session,
) -> list[models.SensorLog]:
    statement = select(models.SensorLog).order_by(
        models.SensorLog.timestamp.desc()
    )

    return list(db.scalars(statement).all())


def get_all_emergency_events(
    db: Session,
) -> list[models.EmergencyEvent]:
    statement = select(models.EmergencyEvent).order_by(
        models.EmergencyEvent.timestamp.desc()
    )

    return list(db.scalars(statement).all())


def get_all_packet_logs(
    db: Session,
) -> list[models.PacketLog]:
    statement = select(models.PacketLog).order_by(
        models.PacketLog.timestamp.desc()
    )

    return list(db.scalars(statement).all())