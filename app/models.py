from datetime import datetime, UTC
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    node_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="ONLINE",
        nullable=False,
    )

    battery: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class SensorLog(Base):
    __tablename__ = "sensor_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    emergency_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    node_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("nodes.node_id"),
        nullable=False,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    heart_rate: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    spo2: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    fall_detected: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    sos: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    battery: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    emergency_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    node_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("nodes.node_id"),
        nullable=False,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    last_sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    remarks: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )


class PacketLog(Base):
    __tablename__ = "packet_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    packet_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    emergency_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sender_node_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    receiver_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    packet_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    ack_status: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )