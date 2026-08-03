from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import models
from app.schemas import SensorPacketCreate


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_packet_by_packet_id(
    db: Session, packet_id: str
) -> models.PacketLog | None:
    statement = select(models.PacketLog).where(
        models.PacketLog.packet_id == packet_id
    )
    return db.scalar(statement)


def packet_exists(db: Session, packet_id: str) -> bool:
    return get_packet_by_packet_id(db=db, packet_id=packet_id) is not None


def create_packet_log(
    db: Session,
    packet: SensorPacketCreate,
    rssi: int | None = None,
    snr: float | None = None,
) -> models.PacketLog:
    """
    Created for EMERGENCY packets.
    """
    node_id = packet.source_node_id or packet.node_id
    packet_log = models.PacketLog(
        packet_id=packet.packet_id,
        emergency_id=packet.emergency_id or f"EMG-{node_id}-{packet.packet_id}",
        sequence_number=packet.sequence_number or 1,
        source_node_id=node_id,
        previous_hop_id=packet.previous_hop_id or node_id,
        destination_id=packet.destination_id or "GATEWAY",
        packet_type=packet.packet_type.value,
        ack_status=True,
        retry_count=packet.retry_count,
        rssi=rssi,
        snr=snr,
        delivery_confirmed=False,
    )
    db.add(packet_log)
    db.flush()
    return packet_log


def mark_delivery_confirmed(db: Session, packet_id: str) -> models.PacketLog | None:
    """
    Updates packet_logs: delivery_confirmed = True, delivery_confirmation_time = now (per requirement 3).
    """
    packet_log = get_packet_by_packet_id(db=db, packet_id=packet_id)
    if packet_log:
        packet_log.delivery_confirmed = True
        packet_log.delivery_confirmation_time = utc_now()
        db.flush()
    return packet_log


def get_all_packet_logs(
    db: Session, limit: int = 100, offset: int = 0
) -> list[models.PacketLog]:
    statement = (
        select(models.PacketLog)
        .order_by(models.PacketLog.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def get_total_packets_count(db: Session) -> int:
    return db.scalar(select(func.count(models.PacketLog.id))) or 0


def get_delivery_confirmations_count(db: Session) -> int:
    return (
        db.scalar(
            select(func.count(models.PacketLog.id)).where(
                models.PacketLog.delivery_confirmed == True
            )
        )
        or 0
    )
