from datetime import datetime, UTC
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import models
from app.schemas import SensorPacketCreate


def utc_now() -> datetime:
    return datetime.now(UTC)


def get_emergency_by_emergency_id(
    db: Session, emergency_id: str
) -> models.EmergencyEvent | None:
    statement = select(models.EmergencyEvent).where(
        models.EmergencyEvent.emergency_id == emergency_id
    )
    return db.scalar(statement)


def create_or_update_emergency_event(
    db: Session,
    packet: SensorPacketCreate,
    event_type: str,
    remarks: str | None = None,
) -> models.EmergencyEvent:
    node_id = packet.source_node_id or packet.node_id
    emergency_id = packet.emergency_id or f"EMG-{node_id}-{packet.packet_id}"
    emergency_event = get_emergency_by_emergency_id(db=db, emergency_id=emergency_id)

    seq_num = packet.sequence_number or 1

    if emergency_event is None:
        emergency_event = models.EmergencyEvent(
            emergency_id=emergency_id,
            node_id=node_id,
            event_type=event_type,
            latitude=packet.latitude or 0.0,
            longitude=packet.longitude or 0.0,
            last_sequence_number=seq_num,
            resolved=False,
            remarks=remarks,
        )
        db.add(emergency_event)
    elif seq_num >= emergency_event.last_sequence_number:
        emergency_event.latitude = packet.latitude or emergency_event.latitude
        emergency_event.longitude = packet.longitude or emergency_event.longitude
        emergency_event.last_sequence_number = seq_num
        emergency_event.updated_at = utc_now()

    db.flush()
    return emergency_event


def get_all_emergency_events(
    db: Session, limit: int = 100, offset: int = 0
) -> list[models.EmergencyEvent]:
    statement = (
        select(models.EmergencyEvent)
        .order_by(models.EmergencyEvent.timestamp.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def get_active_emergency_events(db: Session) -> list[models.EmergencyEvent]:
    statement = (
        select(models.EmergencyEvent)
        .where(models.EmergencyEvent.resolved == False)
        .order_by(models.EmergencyEvent.timestamp.desc())
    )
    return list(db.scalars(statement).all())


def resolve_emergency_event(
    db: Session, emergency_id: str, remarks: str
) -> models.EmergencyEvent | None:
    emergency = get_emergency_by_emergency_id(db, emergency_id)
    if emergency:
        emergency.resolved = True
        emergency.remarks = remarks
        emergency.updated_at = utc_now()

        # Check if node has any other active emergencies
        other_active = db.scalar(
            select(func.count(models.EmergencyEvent.id)).where(
                models.EmergencyEvent.node_id == emergency.node_id,
                models.EmergencyEvent.resolved == False,
                models.EmergencyEvent.emergency_id != emergency_id,
            )
        )
        if (other_active or 0) == 0:
            node = db.scalar(
                select(models.Node).where(models.Node.node_id == emergency.node_id)
            )
            if node:
                node.status = "ONLINE"
                node.current_emergency = None

        db.commit()
        db.refresh(emergency)
    return emergency
