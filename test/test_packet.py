from app.schemas import PacketType, SensorPacketCreate


def test_heartbeat_schema_validation():
    hb = SensorPacketCreate(
        packet_id="HB-0001",
        node_id="NODE_01",
        packet_type=PacketType.HEARTBEAT,
        battery=88.5,
    )
    assert hb.packet_type == PacketType.HEARTBEAT
    assert hb.battery == 88.5
    assert hb.latitude is None


def test_sos_schema_validation():
    sos = SensorPacketCreate(
        packet_id="PKT-0001",
        node_id="NODE_01",
        packet_type=PacketType.SOS,
        battery=75.0,
        latitude=21.14,
        longitude=79.08,
    )
    assert sos.sos is True  # Auto enforced by validator
    assert sos.emergency_id is not None


def test_message_schema_validation():
    message_packet = SensorPacketCreate(
        packet_id="PKT-0002",
        node_id="NODE_01",
        packet_type=PacketType.MESSAGE,
        battery=61.0,
        message="hazard at checkpoint 3",
    )
    assert message_packet.packet_type == PacketType.MESSAGE
    assert message_packet.message == "hazard at checkpoint 3"
    assert not hasattr(message_packet, "fall_detected")


if __name__ == "__main__":
    test_heartbeat_schema_validation()
    test_sos_schema_validation()
    test_message_schema_validation()
    print("Packet schema unit tests passed.")
