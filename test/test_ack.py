from app.schemas import PacketType
from app.services.ack_services import generate_ack


def test_ack_generation():
    hb_ack = generate_ack("HB-100", "NODE_01", PacketType.HEARTBEAT)
    assert hb_ack.status == "ACK"
    assert hb_ack.packet_type == PacketType.HEARTBEAT
    assert "ONLINE" in hb_ack.message

    sos_ack = generate_ack("PKT-200", "NODE_01", PacketType.SOS)
    assert sos_ack.status == "ACK"
    assert sos_ack.packet_type == PacketType.SOS
    assert "processed" in sos_ack.message


if __name__ == "__main__":
    test_ack_generation()
    print("ACK Service unit tests passed.")
