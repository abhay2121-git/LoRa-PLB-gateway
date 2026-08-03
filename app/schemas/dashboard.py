from pydantic import BaseModel


class DashboardStatsResponse(BaseModel):
    total_nodes: int
    online_nodes: int
    offline_nodes: int
    active_emergencies: int
    total_emergencies: int
    total_packets_processed: int
    delivery_confirmations_sent: int
    outbound_messages_sent: int
    ack_success_rate: float
    delivery_success_rate: float


class GatewayStatusResponse(BaseModel):
    gateway_id: str
    status: str
    frequency_mhz: float
    bandwidth_hz: int
    spreading_factor: int
    tx_power_dbm: int
    current_rssi: int
    current_snr: float
    packets_per_second: float
    ack_success_rate: float
    delivery_success_rate: float
    online_nodes_count: int
    offline_nodes_count: int
    uptime_seconds: float
