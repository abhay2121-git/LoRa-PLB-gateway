from enum import Enum

from pydantic import BaseModel, Field, model_validator


class PacketType(str, Enum):
    SOS = "SOS"
    FALL = "FALL"
    HAZARD = "HAZARD"


class SensorPacketCreate(BaseModel):
    packet_id: str = Field(min_length=1, max_length=100)
    emergency_id: str = Field(min_length=1, max_length=100)
    sequence_number: int = Field(ge=1)

    packet_type: PacketType
    node_id: str = Field(min_length=1, max_length=100)

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    heart_rate: int | None = Field(default=None, ge=0, le=250)
    spo2: float | None = Field(default=None, ge=0, le=100)
    temperature: float | None = Field(
        default=None,
        ge=20,
        le=50,
    )

    fall_detected: bool = False
    sos: bool = False

    battery: float = Field(ge=0, le=100)
    retry_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_emergency_packet(self):
        if self.packet_type == PacketType.SOS and not self.sos:
            raise ValueError(
                "SOS packet must have sos=true."
            )

        if (
            self.packet_type == PacketType.FALL
            and not self.fall_detected
        ):
            raise ValueError(
                "FALL packet must have fall_detected=true."
            )

        return self