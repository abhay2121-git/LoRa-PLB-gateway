from datetime import datetime
from typing import Any
from sqlalchemy import Boolean, DateTime, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class OutboundMessage(Base):
    __tablename__ = "outbound_messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    message_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    destination_node: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    message_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="QUEUED",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    ack_received: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<OutboundMessage message_id={self.message_id} dest={self.destination_node} type={self.message_type} status={self.status}>"
