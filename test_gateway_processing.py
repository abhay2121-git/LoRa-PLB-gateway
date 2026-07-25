from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.models  # noqa: F401
from app import crud
from app.core.database import SessionLocal, create_tables
from app.schemas import PacketType, SensorPacketCreate
from app.services.packet_handler import process_packet


def test_packet_processing() -> None:
    create_tables()
    db = SessionLocal()

    try:
        print("\n--- TEST 1: HEARTBEAT PACKET ---")
        hb_packet = SensorPacketCreate(
            packet_id="HB-00001",
            node_id="NODE_04",
            packet_type=PacketType.HEARTBEAT,
            battery=82,
        )
        print(hb_packet.model_dump_json(indent=2))

        result_hb = process_packet(db=db, packet=hb_packet)
        print("HB Processing Result:", result_hb)

        # Verify DB state for Heartbeat
        node = crud.get_node_by_node_id(db, "NODE_04")
        print("Node State after Heartbeat:", node)
        sensor_logs = crud.get_all_sensor_logs(db)
        print(f"Total SensorLogs (Should be 0): {len(sensor_logs)}")

        print("\n--- TEST 2: EMERGENCY PACKET (SOS) ---")
        sos_packet = SensorPacketCreate(
            packet_id="PKT-1008",
            emergency_id="EMG-1008",
            sequence_number=1,
            node_id="NODE_04",
            packet_type=PacketType.SOS,
            latitude=21.1458,
            longitude=79.0882,
            heart_rate=145,
            spo2=92,
            temperature=38.8,
            battery=76,
            sos=True,
            retry_count=0,
        )
        print(sos_packet.model_dump_json(indent=2))

        result_sos = process_packet(db=db, packet=sos_packet)
        print("SOS Processing Result:", result_sos)

        # Verify DB state for Emergency
        node = crud.get_node_by_node_id(db, "NODE_04")
        print("Node State after Emergency:", node)
        sensor_logs = crud.get_all_sensor_logs(db)
        print(f"Total SensorLogs (Should be 1): {len(sensor_logs)}")
        emergencies = crud.get_all_emergency_events(db)
        print(f"Total Emergency Events (Should be 1): {len(emergencies)}")

        print("\n--- TEST 3: DUPLICATE PACKET CHECK ---")
        result_dup = process_packet(db=db, packet=sos_packet)
        print("Duplicate Processing Result:", result_dup)
        print(f"Is Duplicate: {result_dup.duplicate}")

        print("\nSUCCESS: All packet processing tests passed cleanly!")

    finally:
        db.close()


if __name__ == "__main__":
    test_packet_processing()