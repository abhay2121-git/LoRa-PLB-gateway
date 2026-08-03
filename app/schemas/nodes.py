from datetime import datetime
from pydantic import BaseModel


class NodeResponse(BaseModel):
    id: int
    node_id: str
    status: str  # ONLINE / OFFLINE / EMERGENCY
    battery: float
    last_seen: datetime
    latitude: float | None = None
    longitude: float | None = None
    rssi: int | None = None
    snr: float | None = None
    current_emergency: str | None = None
    packet_type: str | None = None

    class Config:
        from_attributes = True
