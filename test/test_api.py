import unittest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_endpoints():
    print("\n--- TESTING API ENDPOINTS ---")

    # 1. Health Check
    res = client.get("/health")
    print("GET /health status:", res.status_code)
    assert res.status_code == 200

    # 2. Render Dashboard HTML
    res = client.get("/")
    print("GET / (Dashboard UI) status:", res.status_code)
    assert res.status_code == 200
    assert "LoRa PLB Gateway" in res.text

    # 3. Post Heartbeat Packet
    hb_payload = {
        "packet_id": "HB-TEST-99",
        "node_id": "NODE_99",
        "battery": 95,
        "packet_type": "HEARTBEAT"
    }
    res = client.post("/api/packets/", json=hb_payload)
    print("POST /api/packets/ (HEARTBEAT) status:", res.status_code)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["emergency_detected"] is False

    # 4. Post Emergency Packet (SOS)
    sos_payload = {
        "packet_id": "PKT-SOS-99",
        "emergency_id": "EMG-SOS-99",
        "sequence_number": 1,
        "node_id": "NODE_99",
        "packet_type": "SOS",
        "latitude": 21.1458,
        "longitude": 79.0882,
        "heart_rate": 140,
        "spo2": 96,
        "temperature": 37.2,
        "battery": 90,
        "sos": True
    }
    res = client.post("/api/packets/", json=sos_payload)
    print("POST /api/packets/ (SOS) status:", res.status_code)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["emergency_detected"] is True

    # 5. Duplicate Check
    res = client.post("/api/packets/", json=sos_payload)
    print("POST /api/packets/ (Duplicate SOS) status:", res.status_code)
    assert res.status_code == 200
    data = res.json()
    assert data["duplicate"] is True

    # 6. GET /api/nodes/
    res = client.get("/api/nodes/")
    print("GET /api/nodes/ status:", res.status_code)
    assert res.status_code == 200
    nodes = res.json()
    assert any(n["node_id"] == "NODE_99" for n in nodes)

    # 7. GET /api/emergencies/
    res = client.get("/api/emergencies/")
    print("GET /api/emergencies/ status:", res.status_code)
    assert res.status_code == 200

    # 8. GET /api/stats/dashboard
    res = client.get("/api/stats/dashboard")
    print("GET /api/stats/dashboard status:", res.status_code)
    assert res.status_code == 200

    # 9. POST Resolve Emergency
    res = client.post("/api/emergencies/EMG-SOS-99/resolve", json={"remarks": "Test resolution success"})
    print("POST /api/emergencies/EMG-SOS-99/resolve status:", res.status_code)
    assert res.status_code == 200
    assert res.json()["resolved"] is True

    print("\nALL API ENDPOINTS TESTED AND PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_api_endpoints()
