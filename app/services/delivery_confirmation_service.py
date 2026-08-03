import json
import logging
from datetime import datetime, UTC
from sqlalchemy.orm import Session

from app import crud
from app.core.config import settings
from app.queues.outbound_queue import outbound_queue
from app.schemas import SensorPacketCreate

logger = logging.getLogger("gateway.delivery_confirmation_service")


class DeliveryConfirmationService:
    """
    Delivery Confirmation Service (Requirement 3 & 17):
    After the gateway processes an emergency packet:
    1. Updates packet_logs.delivery_confirmed = True, delivery_confirmation_time = now (Requirement 3)
    2. Generates a DELIVERY_CONFIRMATION packet and enqueues it into Outbound Queue for transmission (Requirement 17)
    """

    @staticmethod
    async def process_and_send_delivery_confirmation(
        db: Session,
        packet: SensorPacketCreate,
    ) -> bool:
        node_id = packet.source_node_id or packet.node_id
        now = datetime.now(UTC)

        # 1. Update packet_logs table (Requirement 3)
        crud.mark_delivery_confirmed(db=db, packet_id=packet.packet_id)

        # 2. Build DELIVERY_CONFIRMATION payload (Requirement 17)
        confirm_id = f"DEL-CONF-{packet.packet_id}"
        payload_dict = {
            "packet_type": "DELIVERY_CONFIRMATION",
            "packet_id": confirm_id,
            "ref_packet_id": packet.packet_id,
            "emergency_id": packet.emergency_id,
            "gateway_id": settings.gateway_id,
            "destination_id": node_id,
            "status": "EMERGENCY_RECVD_AND_STORED",
            "timestamp": now.isoformat(),
        }

        payload_bytes = json.dumps(payload_dict).encode("utf-8")

        # 3. Enqueue to Outbound Queue (Requirement 8 & 17)
        await outbound_queue.enqueue(message_id=confirm_id, payload_bytes=payload_bytes)

        logger.info(
            f"DeliveryConfirmationService: Enqueued confirmation {confirm_id} for Node {node_id}."
        )
        return True
