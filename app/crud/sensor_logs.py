from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.schemas import SensorPacketCreate


def create_sensor_log(db: Session, packet: SensorPacketCreate) -> models.SensorLog:
    """
    Created ONLY for EMERGENCY packets (SOS, HAZARD, MESSAGE).
    """
    node_id = packet.source_node_id or packet.node_id
    sensor_log = models.SensorLog(
        emergency_id=packet.emergency_id or f"EMG-{node_id}-{packet.packet_id}",
        node_id=node_id,
        sequence_number=packet.sequence_number or 1,
        packet_type=packet.packet_type.value,
        latitude=packet.latitude or 0.0,
        longitude=packet.longitude or 0.0,
        heart_rate=packet.heart_rate,
        spo2=packet.spo2,
        temperature=packet.temperature,
        sos=packet.sos,
        battery=packet.battery,
    )
    db.add(sensor_log)
    db.flush()
    return sensor_log


def get_all_sensor_logs(
    db: Session, limit: int = 100, offset: int = 0
) -> list[models.SensorLog]:
    statement = (
        select(models.SensorLog)
        .order_by(models.SensorLog.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())
