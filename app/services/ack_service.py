import json
import logging
from datetime import datetime, UTC

from app.schemas import ACKResponse, PacketType
from app.queues.ack_queue import ack_queue

logger = logging.getLogger("gateway.ack_service")


class AckService:
    """
    ACK Service (Requirement 7):
    Generates ACK packets and enqueues them into ACK Queue.
    Flow: ACK Generation -> ACK Queue -> LoRaManager -> SX1278.
    """

    @staticmethod
    async def generate_and_enqueue_ack(
        packet_id: str,
        node_id: str,
        packet_type: PacketType,
    ) -> ACKResponse:
        now = datetime.now(UTC)
        if packet_type == PacketType.HEARTBEAT:
            msg = f"Heartbeat ACK for Node {node_id}"
        else:
            msg = f"Emergency {packet_type.value} ACK for packet {packet_id}"

        ack_response = ACKResponse(
            status="ACK",
            packet_id=packet_id,
            node_id=node_id,
            packet_type=packet_type,
            received_at=now,
            message=msg,
        )

        # Serialize ACK packet to JSON bytes for LoRa transmission
        ack_payload = json.dumps(
            {
                "packet_type": "ACK",
                "packet_id": f"ACK-{packet_id}",
                "ref_packet_id": packet_id,
                "destination_id": node_id,
                "status": "SUCCESS",
                "timestamp": now.isoformat(),
            }
        ).encode("utf-8")

        # Enqueue into ACK Queue (Requirement 7: Do not transmit immediately)
        await ack_queue.enqueue(ack_payload)

        return ack_response
