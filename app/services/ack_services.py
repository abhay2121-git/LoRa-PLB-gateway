from datetime import datetime, UTC
from app.schemas import ACKResponse, PacketType


def generate_ack(
    packet_id: str,
    node_id: str,
    packet_type: PacketType,
) -> ACKResponse:
    """
    Generates a logical ACK response confirming receipt of a packet.
    """
    now = datetime.now(UTC)
    if packet_type == PacketType.HEARTBEAT:
        message = f"Heartbeat received for Node {node_id}. Node is ONLINE."
    else:
        message = f"Emergency {packet_type.value} packet {packet_id} received and processed."

    return ACKResponse(
        status="ACK",
        packet_id=packet_id,
        node_id=node_id,
        packet_type=packet_type,
        received_at=now,
        message=message,
    )
