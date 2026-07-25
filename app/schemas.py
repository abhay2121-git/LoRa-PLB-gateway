from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, model_validator


class PacketType(str, Enum):
    HEARTBEAT = "HEARTBEAT"
    SOS = "SOS"
    FALL = "FALL"
    HAZARD = "HAZARD"


class SensorPacketCreate(BaseModel):
    packet_id: str = Field(min_length=1, max_length=100)
    node_id: str = Field(min_length=1, max_length=100)
    packet_type: PacketType
    battery: float = Field(ge=0, le=100)

    # Optional fields for Heartbeat (required/used for Emergency packets)
    emergency_id: str | None = Field(default=None, max_length=100)
    sequence_number: int | None = Field(default=1, ge=0)

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    heart_rate: int | None = Field(default=None, ge=0, le=250)
    spo2: float | None = Field(default=None, ge=0, le=100)
    temperature: float | None = Field(default=None, ge=20, le=50)

    fall_detected: bool = False
    sos: bool = False
    retry_count: int = Field(default=0, ge=0)
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def validate_packet_logic(self):
        if self.packet_type == PacketType.SOS and not self.sos:
            self.sos = True

        if self.packet_type == PacketType.FALL and not self.fall_detected:
            self.fall_detected = True

        if self.packet_type != PacketType.HEARTBEAT:
            # If emergency_id is not provided, generate a fallback from packet_id or node_id
            if not self.emergency_id:
                self.emergency_id = f"EMG-{self.node_id}-{self.packet_id}"
            if self.latitude is None:
                self.latitude = 0.0
            if self.longitude is None:
                self.longitude = 0.0

        return self


class PacketProcessingResult(BaseModel):
    success: bool
    duplicate: bool = False
    packet_id: str
    node_id: str
    packet_type: PacketType
    emergency_id: str | None = None
    sequence_number: int | None = None
    emergency_detected: bool = False
    emergency_type: str | None = None
    ack_status: bool = True
    message: str = ""


class ACKResponse(BaseModel):
    status: str = "ACK"
    packet_id: str
    node_id: str
    packet_type: PacketType
    received_at: datetime
    message: str


class NodeResponse(BaseModel):
    id: int
    node_id: str
    status: str  # ONLINE / OFFLINE / EMERGENCY
    battery: float
    last_seen: datetime
    packet_type: str | None = None

    class Config:
        from_attributes = True


class SensorLogResponse(BaseModel):
    id: int
    emergency_id: str
    node_id: str
    sequence_number: int
    latitude: float
    longitude: float
    heart_rate: int | None = None
    spo2: float | None = None
    temperature: float | None = None
    fall_detected: bool
    sos: bool
    battery: float
    timestamp: datetime

    class Config:
        from_attributes = True


class EmergencyEventResponse(BaseModel):
    id: int
    emergency_id: str
    node_id: str
    event_type: str
    latitude: float
    longitude: float
    last_sequence_number: int
    resolved: bool
    remarks: str | None = None
    timestamp: datetime
    updated_at: datetime

    # Included for convenience in dashboard history table
    battery: float | None = None
    heart_rate: int | None = None
    spo2: float | None = None
    temperature: float | None = None

    class Config:
        from_attributes = True


class EmergencyResolveRequest(BaseModel):
    remarks: str = Field(min_length=1, max_length=500)


class DashboardStatsResponse(BaseModel):
    total_nodes: int
    online_nodes: int
    offline_nodes: int
    active_emergencies: int
    total_emergencies: int
    total_packets_processed: int


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int