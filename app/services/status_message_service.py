import json
import logging
import uuid
from datetime import datetime, UTC
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.queues.outbound_queue import outbound_queue
from app.schemas import OutboundMessageType

logger = logging.getLogger("gateway.status_message_service")

PREDEFINED_STATUS_MESSAGES = [
    "Rescue Team Dispatched",
    "Medical Team Arriving",
    "Stay Calm",
    "Hazard Cleared",
    "Evacuate Area",
]


class StatusMessageService:
    """
    Status Message Service (Requirement 4 & 18):
    Converts dashboard operator commands into STATUS_MESSAGE / HAZARD / CONFIG_UPDATE packets,
    stores them in outbound_messages table (Requirement 4), and enqueues to Outbound Queue (Requirement 8).
    """

    @staticmethod
    async def create_and_enqueue_status_message(
        db: Session,
        destination_node: str,
        message_text: str,
    ) -> str:
        msg_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
        payload_dict = {
            "packet_type": "STATUS_MESSAGE",
            "message_id": msg_id,
            "gateway_id": settings.gateway_id,
            "destination_id": destination_node,
            "message": message_text,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # 1. Store in outbound_messages table (Requirement 4)
        crud.create_outbound_message(
            db=db,
            message_id=msg_id,
            destination_node=destination_node,
            message_type=OutboundMessageType.STATUS_MESSAGE.value,
            payload=payload_dict,
        )

        # 2. Enqueue to Outbound Queue (Requirement 8)
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        await outbound_queue.enqueue(message_id=msg_id, payload_bytes=payload_bytes)

        logger.info(
            f"StatusMessageService: Enqueued STATUS_MESSAGE {msg_id} to Node {destination_node}: '{message_text}'"
        )
        return msg_id

    @staticmethod
    async def create_and_enqueue_hazard_broadcast(
        db: Session,
        message_text: str,
        latitude: float,
        longitude: float,
    ) -> str:
        msg_id = f"HAZARD-{uuid.uuid4().hex[:8].upper()}"
        payload_dict = {
            "packet_type": "HAZARD",
            "message_id": msg_id,
            "gateway_id": settings.gateway_id,
            "destination_id": "BROADCAST",
            "message": message_text,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # 1. Store in outbound_messages table (Requirement 4)
        crud.create_outbound_message(
            db=db,
            message_id=msg_id,
            destination_node="BROADCAST",
            message_type=OutboundMessageType.HAZARD.value,
            payload=payload_dict,
        )

        # 2. Enqueue to Outbound Queue (Requirement 8)
        payload_bytes = json.dumps(payload_dict).encode("utf-8")
        await outbound_queue.enqueue(message_id=msg_id, payload_bytes=payload_bytes)

        logger.info(f"StatusMessageService: Enqueued HAZARD broadcast {msg_id}: '{message_text}'")
        return msg_id
