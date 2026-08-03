from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
from app.schemas.enums import OutboundMessageType


class StatusMessageCreate(BaseModel):
    destination_node: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=255)


class HazardBroadcastRequest(BaseModel):
    message: str = Field(min_length=1, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ConfigUpdateRequest(BaseModel):
    destination_node: str = Field(min_length=1, max_length=100)
    config: dict[str, Any]


class OutboundMessageResponse(BaseModel):
    id: int
    message_id: str
    destination_node: str
    message_type: OutboundMessageType
    payload: dict[str, Any]
    status: str
    created_at: datetime
    sent_at: datetime | None = None
    ack_received: bool

    class Config:
        from_attributes = True
