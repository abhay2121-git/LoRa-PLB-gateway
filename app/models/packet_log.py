from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class PacketLog(Base):
    __tablename__ = "packet_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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

    source_node_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    previous_hop_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    destination_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    packet_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    ack_status: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    retry_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    rssi: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    snr: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    delivery_confirmed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    delivery_confirmation_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<PacketLog packet_id={self.packet_id} source={self.source_node_id} type={self.packet_type} confirmed={self.delivery_confirmed}>"
