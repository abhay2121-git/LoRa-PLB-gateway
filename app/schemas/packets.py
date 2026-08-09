from datetime import datetime
from pydantic import BaseModel, Field, model_validator
from app.schemas.enums import PacketType


class SensorPacketCreate(BaseModel):
    packet_id: str = Field(min_length=1, max_length=100)
    node_id: str | None = Field(default=None, max_length=100)
    source_node_id: str | None = Field(default=None, max_length=100)
    previous_hop_id: str | None = Field(default=None, max_length=100)
    destination_id: str | None = Field(default=None, max_length=100)
    packet_type: PacketType
    battery: float = Field(ge=0, le=100)

    emergency_id: str | None = Field(default=None, max_length=100)
    sequence_number: int | None = Field(default=1, ge=0)

    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    heart_rate: int | None = Field(default=None, ge=0, le=250)
    spo2: float | None = Field(default=None, ge=0, le=100)
    temperature: float | None = Field(default=None, ge=20, le=50)

    message: str | None = Field(default=None, max_length=255)
    sos: bool = False
    retry_count: int = Field(default=0, ge=0)
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def validate_packet_ids_and_logic(self):
        # Sync source_node_id and node_id
        if not self.source_node_id and self.node_id:
            self.source_node_id = self.node_id
        elif not self.node_id and self.source_node_id:
            self.node_id = self.source_node_id
        elif not self.source_node_id and not self.node_id:
            self.source_node_id = "UNKNOWN_NODE"
            self.node_id = "UNKNOWN_NODE"

        if not self.previous_hop_id:
            self.previous_hop_id = self.source_node_id

        if not self.destination_id:
            self.destination_id = "GATEWAY"

        if self.packet_type == PacketType.SOS and not self.sos:
            self.sos = True

        if self.packet_type in (PacketType.SOS, PacketType.HAZARD):
            if not self.emergency_id:
                self.emergency_id = f"EMG-{self.source_node_id}-{self.packet_id}"
            if self.latitude is None:
                self.latitude = 0.0
            if self.longitude is None:
                self.longitude = 0.0

        if self.packet_type == PacketType.MESSAGE and not self.message:
            self.message = ""

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
    delivery_confirmation_sent: bool = False
    message: str = ""


class ACKResponse(BaseModel):
    status: str = "ACK"
    packet_id: str
    node_id: str
    packet_type: PacketType
    received_at: datetime
    message: str


class PacketLogResponse(BaseModel):
    id: int
    packet_id: str
    emergency_id: str
    sequence_number: int
    source_node_id: str
    previous_hop_id: str | None = None
    destination_id: str | None = None
    packet_type: str
    ack_status: bool
    retry_count: int
    rssi: int | None = None
    snr: float | None = None
    delivery_confirmed: bool
    delivery_confirmation_time: datetime | None = None
    timestamp: datetime

    class Config:
        from_attributes = True
