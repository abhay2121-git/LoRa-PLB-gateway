from sqlalchemy import inspect
from app.core.database import create_tables, engine


def test_database_tables():
    create_tables()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    assert "nodes" in tables
    assert "sensor_logs" in tables
    assert "emergency_events" in tables
    assert "packet_logs" in tables
    print(f"Database schema verified. Active tables: {tables}")


if __name__ == "__main__":
    test_database_tables()
