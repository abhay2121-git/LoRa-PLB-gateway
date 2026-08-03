from datetime import datetime, UTC
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app import models


def utc_now() -> datetime:
    return datetime.now(UTC)


def create_outbound_message(
    db: Session,
    message_id: str,
    destination_node: str,
    message_type: str,
    payload: dict[str, Any],
) -> models.OutboundMessage:
    outbound = models.OutboundMessage(
        message_id=message_id,
        destination_node=destination_node,
        message_type=message_type,
        payload=payload,
        status="QUEUED",
    )
    db.add(outbound)
    db.commit()
    db.refresh(outbound)
    return outbound


def update_outbound_status(
    db: Session,
    message_id: str,
    status: str,
    sent: bool = False,
) -> models.OutboundMessage | None:
    statement = select(models.OutboundMessage).where(
        models.OutboundMessage.message_id == message_id
    )
    outbound = db.scalar(statement)
    if outbound:
        outbound.status = status
        if sent:
            outbound.sent_at = utc_now()
        db.commit()
        db.refresh(outbound)
    return outbound


def mark_outbound_ack_received(
    db: Session, message_id: str
) -> models.OutboundMessage | None:
    statement = select(models.OutboundMessage).where(
        models.OutboundMessage.message_id == message_id
    )
    outbound = db.scalar(statement)
    if outbound:
        outbound.ack_received = True
        outbound.status = "DELIVERED"
        db.commit()
        db.refresh(outbound)
    return outbound


def get_all_outbound_messages(
    db: Session, limit: int = 100, offset: int = 0
) -> list[models.OutboundMessage]:
    statement = (
        select(models.OutboundMessage)
        .order_by(models.OutboundMessage.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(statement).all())


def get_outbound_messages_sent_count(db: Session) -> int:
    return (
        db.scalar(
            select(func.count(models.OutboundMessage.id)).where(
                models.OutboundMessage.status == "SENT"
            )
        )
        or 0
    )
