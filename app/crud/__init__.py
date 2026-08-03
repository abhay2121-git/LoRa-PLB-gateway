from app.crud.nodes import (
    get_node_by_node_id,
    get_all_nodes,
    update_node_heartbeat,
    create_or_update_node_emergency,
    mark_offline_nodes,
)
from app.crud.sensor_logs import (
    create_sensor_log,
    get_all_sensor_logs,
)
from app.crud.packet_logs import (
    get_packet_by_packet_id,
    packet_exists,
    create_packet_log,
    mark_delivery_confirmed,
    get_all_packet_logs,
    get_total_packets_count,
    get_delivery_confirmations_count,
)
from app.crud.emergency_events import (
    get_emergency_by_emergency_id,
    create_or_update_emergency_event,
    get_all_emergency_events,
    get_active_emergency_events,
    resolve_emergency_event,
)
from app.crud.outbound_messages import (
    create_outbound_message,
    update_outbound_status,
    mark_outbound_ack_received,
    get_all_outbound_messages,
    get_outbound_messages_sent_count,
)

# Aliases for backward compatibility
create_or_update_node = create_or_update_node_emergency

__all__ = [
    "get_node_by_node_id",
    "get_all_nodes",
    "update_node_heartbeat",
    "create_or_update_node_emergency",
    "create_or_update_node",
    "mark_offline_nodes",
    "create_sensor_log",
    "get_all_sensor_logs",
    "get_packet_by_packet_id",
    "packet_exists",
    "create_packet_log",
    "mark_delivery_confirmed",
    "get_all_packet_logs",
    "get_total_packets_count",
    "get_delivery_confirmations_count",
    "get_emergency_by_emergency_id",
    "create_or_update_emergency_event",
    "get_all_emergency_events",
    "get_active_emergency_events",
    "resolve_emergency_event",
    "create_outbound_message",
    "update_outbound_status",
    "mark_outbound_ack_received",
    "get_all_outbound_messages",
    "get_outbound_messages_sent_count",
]
