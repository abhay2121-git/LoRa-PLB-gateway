from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import app.models  # noqa: F401

from app.database import SessionLocal, create_tables
from app.schemas import SensorPacketCreate
from app.services.packet_handler import process_packet


def test_packet_processing() -> None:
    create_tables()

    packet = SensorPacketCreate(
        packet_id="PKT-1003",
        node_id="NODE_04",
        latitude=21.1458,
        longitude=79.0882,
        heart_rate=148,
        spo2=92,
        temperature=38.9,
        fall_detected=True,
        sos=False,
        battery=67,
        retry_count=0,
    )

    db = SessionLocal()

    try:
        print("\n--- PACKET RECEIVED ---")
        print(packet.model_dump_json(indent=2))

        result = process_packet(
            db=db,
            packet=packet,
        )

        print("\n--- PROCESSING RESULT ---")

        print(f"Success: {result.success}")
        print(f"Duplicate: {result.duplicate}")
        print(f"Packet ID: {result.packet_id}")
        print(f"Node ID: {result.node_id}")

        print(
            f"Emergency Detected: "
            f"{result.emergency_detected}"
        )

        print(
            f"Emergency Type: "
            f"{result.emergency_type}"
        )

        print(f"ACK Status: {result.ack_status}")
        print(f"Message: {result.message}")

    finally:
        db.close()


if __name__ == "__main__":
    test_packet_processing()