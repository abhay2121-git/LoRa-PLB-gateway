from datetime import datetime, timedelta, UTC
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select, update, func
from sqlalchemy.orm import Session

from app import models
from app.core.config import settings
from app.schemas import SensorPacketCreate
from app.services.emergency_detector import EmergencyResult


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
    return get_packet_by_packet_id(db=db, packet_id=packet_id) is not None


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


def update_node_heartbeat(
    db: Session,
    packet: SensorPacketCreate,
) -> models.Node:
    """
    Updates existing Node or creates a new one for HEARTBEAT packets.
    Sets status=ONLINE, updates battery, last_seen, packet_type.
    Does NOT touch SensorLog, PacketLog, or EmergencyEvent.
    """
    node = get_node_by_node_id(db=db, node_id=packet.node_id)
    current_time = utc_now()

    if node is None:
        node = models.Node(
            node_id=packet.node_id,
            status="ONLINE",
            battery=packet.battery,
            last_seen=current_time,
            packet_type=packet.packet_type.value,
        )
        db.add(node)
    else:
        # Keep status as EMERGENCY if node is currently in active emergency, else ONLINE
        if node.status != "EMERGENCY":
            node.status = "ONLINE"
        node.battery = packet.battery
        node.last_seen = current_time
        node.packet_type = packet.packet_type.value

    db.flush()
    return node


def create_or_update_node(
    db: Session,
    packet: SensorPacketCreate,
) -> models.Node:
    """
    Updates existing Node or creates a new one for EMERGENCY packets.
    Sets status=EMERGENCY, updates battery, last_seen, packet_type.
    """
    node = get_node_by_node_id(db=db, node_id=packet.node_id)
    current_time = utc_now()

    if node is None:
        node = models.Node(
            node_id=packet.node_id,
            status="EMERGENCY",
            battery=packet.battery,
            last_seen=current_time,
            packet_type=packet.packet_type.value,
        )
        db.add(node)
    else:
        node.status = "EMERGENCY"
        node.battery = packet.battery
        node.last_seen = current_time
        node.packet_type = packet.packet_type.value

    db.flush()
    return node


def create_sensor_log(
    db: Session,
    packet: SensorPacketCreate,
) -> models.SensorLog:
    """
    Created ONLY for EMERGENCY packets.
    """
    sensor_log = models.SensorLog(
        emergency_id=packet.emergency_id or f"EMG-{packet.node_id}-{packet.packet_id}",
        node_id=packet.node_id,
        sequence_number=packet.sequence_number or 1,
        latitude=packet.latitude or 0.0,
        longitude=packet.longitude or 0.0,
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
    """
    Created or updated ONLY for EMERGENCY packets.
    """
    if not emergency.is_emergency:
        raise ValueError("Cannot create an emergency event for non-emergency packet.")

    emergency_id = packet.emergency_id or f"EMG-{packet.node_id}-{packet.packet_id}"
    emergency_event = get_emergency_by_emergency_id(db=db, emergency_id=emergency_id)

    seq_num = packet.sequence_number or 1

    if emergency_event is None:
        emergency_event = models.EmergencyEvent(
            emergency_id=emergency_id,
            node_id=packet.node_id,
            event_type=emergency.event_type or packet.packet_type.value,
            latitude=packet.latitude or 0.0,
            longitude=packet.longitude or 0.0,
            last_sequence_number=seq_num,
            resolved=False,
            remarks=emergency.remarks,
        )
        db.add(emergency_event)
    elif seq_num >= emergency_event.last_sequence_number:
        emergency_event.latitude = packet.latitude or emergency_event.latitude
        emergency_event.longitude = packet.longitude or emergency_event.longitude
        emergency_event.last_sequence_number = seq_num
        emergency_event.updated_at = utc_now()

    db.flush()
    return emergency_event


def create_packet_log(
    db: Session,
    packet: SensorPacketCreate,
) -> models.PacketLog:
    """
    Created ONLY for EMERGENCY packets.
    """
    packet_log = models.PacketLog(
        packet_id=packet.packet_id,
        emergency_id=packet.emergency_id or f"EMG-{packet.node_id}-{packet.packet_id}",
        sequence_number=packet.sequence_number or 1,
        sender_node_id=packet.node_id,
        receiver_id=settings.gateway_id,
        packet_type=packet.packet_type.value,
        ack_status=True,
        retry_count=packet.retry_count,
    )
    db.add(packet_log)
    db.flush()
    return packet_log


def mark_offline_nodes(
    db: Session,
    timeout_seconds: int = 900,
) -> int:
    """
    Marks nodes as OFFLINE if no heartbeat/packet received for > timeout_seconds (15 mins).
    Returns count of updated nodes.
    """
    cutoff = utc_now() - timedelta(seconds=timeout_seconds)
    statement = (
        update(models.Node)
        .where(models.Node.last_seen < cutoff, models.Node.status != "OFFLINE")
        .values(status="OFFLINE")
    )
    result = db.execute(statement)
    db.commit()
    return result.rowcount


def get_all_nodes(db: Session) -> list[models.Node]:
    statement = select(models.Node).order_by(models.Node.node_id)
    return list(db.scalars(statement).all())


def get_all_sensor_logs(db: Session, limit: int = 100, offset: int = 0) -> list[models.SensorLog]:
    statement = select(models.SensorLog).order_by(models.SensorLog.timestamp.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


def get_all_emergency_events(db: Session, limit: int = 100, offset: int = 0) -> list[models.EmergencyEvent]:
    statement = select(models.EmergencyEvent).order_by(models.EmergencyEvent.timestamp.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement).all())


def get_active_emergency_events(db: Session) -> list[models.EmergencyEvent]:
    statement = select(models.EmergencyEvent).where(models.EmergencyEvent.resolved == False).order_by(models.EmergencyEvent.timestamp.desc())
    return list(db.scalars(statement).all())


def resolve_emergency_event(db: Session, emergency_id: str, remarks: str) -> models.EmergencyEvent | None:
    emergency = get_emergency_by_emergency_id(db, emergency_id)
    if emergency:
        emergency.resolved = True
        emergency.remarks = remarks
        emergency.updated_at = utc_now()
        
        # Check if node has any other active emergencies
        other_active = db.scalar(
            select(func.count(models.EmergencyEvent.id))
            .where(models.EmergencyEvent.node_id == emergency.node_id, models.EmergencyEvent.resolved == False, models.EmergencyEvent.emergency_id != emergency_id)
        )
        if (other_active or 0) == 0:
            node = get_node_by_node_id(db, emergency.node_id)
            if node:
                node.status = "ONLINE"

        db.commit()
        db.refresh(emergency)
    return emergency


def get_all_packet_logs(db: Session, limit: int = 100, offset: int = 0) -> list[models.PacketLog]:
    statement = select(models.PacketLog).order_by(models.PacketLog.timestamp.desc()).limit(limit).offset(offset)
    return list(db.scalars(statement).all())