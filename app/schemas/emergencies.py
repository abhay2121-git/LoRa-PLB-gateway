from datetime import datetime
from pydantic import BaseModel, Field


class SensorLogResponse(BaseModel):
    id: int
    emergency_id: str
    node_id: str
    sequence_number: int
    packet_type: str | None = None
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

    battery: float | None = None
    heart_rate: int | None = None
    spo2: float | None = None
    temperature: float | None = None

    class Config:
        from_attributes = True


class EmergencyResolveRequest(BaseModel):
    remarks: str = Field(min_length=1, max_length=500)
