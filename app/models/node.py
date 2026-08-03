from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Float, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.sensor_log import SensorLog
    from app.models.emergency_event import EmergencyEvent


class Node(Base):
    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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

    latitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    longitude: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rssi: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    snr: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    current_emergency: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    packet_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="HEARTBEAT",
    )

    sensor_logs: Mapped[list["SensorLog"]] = relationship(
        "SensorLog", back_populates="node", cascade="all, delete-orphan"
    )
    emergency_events: Mapped[list["EmergencyEvent"]] = relationship(
        "EmergencyEvent", back_populates="node", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Node id={self.node_id} status={self.status} battery={self.battery}% last_seen={self.last_seen}>"
