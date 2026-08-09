from pathlib import Path
import sys

from sqlalchemy import inspect

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings
from app.core.database import create_tables, engine
import app.models  # noqa: F401
from app.schemas import SensorPacketCreate


def test_configuration() -> None:
    print("\n--- CONFIGURATION ---")

    print(f"Application: {settings.app_name}")
    print(f"Version: {settings.app_version}")
    print(f"Gateway: {settings.gateway_id}")
    print(f"Database: {settings.database_url}")


def test_database() -> None:
    print("\n--- DATABASE ---")

    create_tables()

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print("Database tables created:")

    for table in tables:
        print(f"  - {table}")


def test_schema() -> None:
    print("\n--- PACKET VALIDATION ---")

    packet = SensorPacketCreate(
        packet_id="PKT-1001",
        node_id="NODE_04",
        latitude=21.1458,
        longitude=79.0882,
        heart_rate=148,
        spo2=92,
        temperature=38.9,
        message="status update",
        sos=True,
        battery=67,
        retry_count=0,
    )

    print("Packet successfully validated.")

    print(packet.model_dump_json(indent=2))


if __name__ == "__main__":
    test_configuration()
    test_database()
    test_schema()

    print("\nGateway foundation test completed successfully.")