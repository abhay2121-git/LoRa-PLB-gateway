from datetime import datetime, timedelta, UTC
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app import models
from app.schemas import SensorPacketCreate


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_node_by_node_id(db: Session, node_id: str) -> models.Node | None:
    statement = select(models.Node).where(models.Node.node_id == node_id)
    return db.scalar(statement)


def get_all_nodes(db: Session) -> list[models.Node]:
    statement = select(models.Node).order_by(models.Node.node_id)
    return list(db.scalars(statement).all())


def update_node_heartbeat(
    db: Session,
    packet: SensorPacketCreate,
    rssi: int | None = None,
    snr: float | None = None,
) -> models.Node:
    """
    Updates Node state for HEARTBEAT packets.
    Sets status=ONLINE (if not currently EMERGENCY), updates battery, last_seen, lat/lng, rssi, snr.
    Does NOT touch SensorLog, PacketLog, or EmergencyEvent (per requirement 10).
    """
    node = get_node_by_node_id(db=db, node_id=packet.source_node_id or packet.node_id)
    current_time = utc_now()
    target_node_id = packet.source_node_id or packet.node_id

    if node is None:
        node = models.Node(
            node_id=target_node_id,
            status="ONLINE",
            battery=packet.battery,
            last_seen=current_time,
            latitude=packet.latitude,
            longitude=packet.longitude,
            rssi=rssi,
            snr=snr,
            packet_type=packet.packet_type.value,
        )
        db.add(node)
    else:
        if node.status != "EMERGENCY":
            node.status = "ONLINE"
        node.battery = packet.battery
        node.last_seen = current_time
        if packet.latitude is not None:
            node.latitude = packet.latitude
        if packet.longitude is not None:
            node.longitude = packet.longitude
        if rssi is not None:
            node.rssi = rssi
        if snr is not None:
            node.snr = snr
        node.packet_type = packet.packet_type.value

    db.flush()
    return node


def create_or_update_node_emergency(
    db: Session,
    packet: SensorPacketCreate,
    rssi: int | None = None,
    snr: float | None = None,
) -> models.Node:
    """
    Updates Node state for EMERGENCY packets.
    Sets status=EMERGENCY, updates battery, last_seen, lat/lng, rssi, snr, current_emergency.
    """
    target_node_id = packet.source_node_id or packet.node_id
    node = get_node_by_node_id(db=db, node_id=target_node_id)
    current_time = utc_now()
    emg_id = packet.emergency_id or f"EMG-{target_node_id}-{packet.packet_id}"

    if node is None:
        node = models.Node(
            node_id=target_node_id,
            status="EMERGENCY",
            battery=packet.battery,
            last_seen=current_time,
            latitude=packet.latitude,
            longitude=packet.longitude,
            rssi=rssi,
            snr=snr,
            current_emergency=emg_id,
            packet_type=packet.packet_type.value,
        )
        db.add(node)
    else:
        node.status = "EMERGENCY"
        node.battery = packet.battery
        node.last_seen = current_time
        if packet.latitude is not None:
            node.latitude = packet.latitude
        if packet.longitude is not None:
            node.longitude = packet.longitude
        if rssi is not None:
            node.rssi = rssi
        if snr is not None:
            node.snr = snr
        node.current_emergency = emg_id
        node.packet_type = packet.packet_type.value

    db.flush()
    return node


def mark_offline_nodes(db: Session, timeout_seconds: int = 900) -> int:
    """
    Marks nodes as OFFLINE if no packet received for > timeout_seconds.
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
