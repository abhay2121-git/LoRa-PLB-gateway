# 📡 LoRa PLB Gateway (Personal Location Beacon)

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/PostgreSQL-15%2B-336791.svg)](https://www.postgresql.org/)
[![Hardware](https://img.shields.io/badge/Hardware-Semtech%20SX1278%20%2F%20SX1276-orange.svg)](https://www.semtech.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**LoRa PLB Gateway** is an industrial-grade, low-power, long-range telemetry and emergency signal gateway designed for Search and Rescue (SAR), remote asset tracking, and personal safety monitoring. Built with **FastAPI**, **Semtech SX1278/SX1276 SPI hardware drivers**, **PostgreSQL**, and **WebSockets**, it provides real-time packet parsing, sliding-window deduplication, automatic SOS detection, down-link ACK queuing, node health monitoring, and a live web dashboard.

---

## 📋 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Hardware & Pinout Configuration](#-hardware--pinout-configuration)
- [Project Directory Structure](#-project-directory-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Setup](#environment-setup)
  - [Database Setup](#database-setup)
  - [Running the Gateway](#running-the-gateway)
- [Docker Deployment](#-docker-deployment)
- [Packet Protocols & Data Format](#-packet-protocols--data-format)
- [API & WebSocket Documentation](#-api--websocket-documentation)
- [Testing & Verification](#-testing--verification)
- [Configuration Settings](#-configuration-settings)
- [License](#-license)

---

## ✨ Key Features

- **📡 Hardware-Direct LoRa Driver (`SX1278`)**: Full SPI transceiver register control (`spidev` & `RPi.GPIO`) with hardware CRC verification, configurable RF frequency (433/868/915 MHz), transmit power (2 to 20 dBm), spreading factor (SF7–SF12), bandwidth, and coding rate. Includes a graceful **Software Mock Mode** for non-Raspberry Pi development environments.
- **🚨 Automated Emergency SOS Triaging**: Instant parsing of SOS distress signals and abnormal vital metrics (e.g., SpO2 < 90%, Heart Rate > 140 bpm or < 40 bpm). Automatically logs active emergency events and broadcasts instant alert notifications over WebSockets.
- **🛡️ Multi-Stage Packet Pipeline**:
  - **Parser**: Decodes raw binary byte streams or structured JSON payloads into validated Pydantic models.
  - **Validator**: Enforces boundary and type checks on GPS coordinates, telemetry, battery percentage, and packet headers.
  - **Deduplicator**: In-memory TTL sliding-window duplicate filter to prevent retransmitted LoRa packets from clogging database storage.
  - **DB Persister**: Atomically writes node states, packet logs, emergency alerts, and sensor telemetry to PostgreSQL.
- **⚡ Asynchronous ACK & Outbound Queue Workers**: Dedicated background queue tasks to guarantee fast down-link delivery confirmations (ACKs) and outbound commands to field nodes without blocking packet ingestion loops.
- **💓 Node Health & Timeout Monitoring**: Automatic background thread checks node activity every 60 seconds and marks nodes as `OFFLINE` if no heartbeat or telemetry packet is received within 15 minutes (900 seconds).
- **📊 Real-time Command Center Dashboard**: Jinja2 + WebSocket dashboard displaying live node maps, signal metrics (RSSI / SNR), emergency alert popups, packet log streams, and radio statistics.
- **🗄️ Database Migrations (Alembic)**: Robust database schema management with PostgreSQL via SQLAlchemy 2.0 and Alembic migration scripts.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Field Devices
        N1[LoRa Field Node 1<br/>(PLB / Tracker)]
        N2[LoRa Field Node 2<br/>(Sensors / Vitals)]
        N3[LoRa SOS Distress Beacon]
    end

    subgraph Hardware Layer
        SX[Semtech SX1278 / SX1276<br/>LoRa Transceiver Module]
        SPI[SPI Bus 0 / GPIO Interrupts<br/>(Raspberry Pi Header)]
    end

    subgraph Gateway Core Server (FastAPI)
        RX[LoRa Receiver Service]
        PARSER[Packet Parser & Validator]
        DEDUP[Duplicate Detector<br/>(Sliding Window Cache)]
        PROC[Packet Processor Engine]
        EMG[Emergency Detection Engine]
        NODE_MGR[Node Timeout Monitor<br/>(15-min Heartbeat Checker)]
        ACK_Q[ACK Queue Worker]
        OUT_Q[Outbound Queue Worker]
    end

    subgraph Storage & Communication
        DB[(PostgreSQL Database<br/>SQLAlchemy 2.0 / Alembic)]
        WS[WebSocket Manager<br/>(/ws Live Stream)]
    end

    subgraph Operator UI & APIs
        DASH[Web Dashboard<br/>(Live Command Center)]
        REST[REST API Endpoints<br/>(/api/v1/...)]
    end

    N1 -- LoRa RF 433MHz --> SX
    N2 -- LoRa RF 433MHz --> SX
    N3 -- LoRa RF 433MHz --> SX

    SX -- SPI / GPIO --> SPI
    SPI --> RX
    RX --> PARSER
    PARSER --> DEDUP
    DEDUP --> PROC
    PROC --> EMG
    PROC --> DB
    EMG -- Broadcast Alert --> WS
    WS --> DASH

    PROC --> ACK_Q
    ACK_Q -- Downlink ACK --> SX
    OUT_Q -- Outbound Command --> SX

    NODE_MGR --> DB
    REST <--> DB
```

---

## 🔌 Hardware & Pinout Configuration

The gateway communicates with the **Semtech SX1278 / SX1276** LoRa module over the SPI bus and GPIO pins on a Raspberry Pi (or compatible SBC).

### Wiring Map (SX1278 ↔ Raspberry Pi GPIO)

| SX1278 Pin | Pin Name | Raspberry Pi Header Pin | BCM / Function | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **VCC** | 3.3V Power | Pin 1 or Pin 17 | `3V3` | **Do NOT connect to 5V!** |
| **GND** | Ground | Pin 6, 9, 14, 20, or 25 | `GND` | Common Ground |
| **SCK** | SPI Clock | Pin 23 | `GPIO 11 (SPI0_SCLK)` | SPI Bus 0 Clock |
| **MISO** | Master In Slave Out | Pin 21 | `GPIO 9 (SPI0_MISO)` | SPI Bus 0 MISO |
| **MOSI** | Master Out Slave In | Pin 19 | `GPIO 10 (SPI0_MOSI)` | SPI Bus 0 MOSI |
| **NSS / CS** | Chip Select | Pin 24 | `GPIO 8 (SPI0_CE0)` | SPI Bus 0 Chip Enable 0 |
| **RESET** | Hardware Reset | Pin 22 | `GPIO 25` | Driver controlled Reset pin |
| **DIO0** | Packet Rx/Tx Done | Pin 18 | `GPIO 24` | Interrupt pin for Packet Rx |

> 💡 **Development Note**: When running on non-Linux hardware (Windows/macOS) or systems without `spidev`/`RPi.GPIO`, the application automatically falls back to **Hardware Mock Mode**, generating synthetic LoRa signals for testing and development.

---

## 📁 Project Directory Structure

```text
lora-plb-gateway/
├── alembic/                    # Database migration scripts
│   ├── versions/               # Schema version history
│   │   └── 001_initial_schema.py
│   ├── env.py                  # Alembic environment configuration
│   └── script.py.mako
├── app/                        # Application Source Code
│   ├── api/                    # API Route implementations
│   │   └── packets.py          # Packet ingestion endpoints
│   ├── core/                   # Core configurations & setup
│   │   ├── config.py           # Pydantic BaseSettings & env loader
│   │   ├── database.py         # SQLAlchemy engine & session factory
│   │   ├── logger.py           # Centralized logging setup
│   │   └── security.py         # Security utilities
│   ├── crud/                   # Database CRUD operations
│   │   └── crud.py             # Node, Emergency, PacketLog CRUD
│   ├── drivers/                # Low-Level Hardware Drivers
│   │   ├── spi.py              # SPI bus driver (with Mock fallback)
│   │   ├── gpio.py             # GPIO pin driver (with Mock fallback)
│   │   ├── sx1278.py           # Semtech SX1278 register & RF driver
│   │   └── lora_manager.py     # Thread-safe LoRa hardware manager
│   ├── models/                 # SQLAlchemy Database Models
│   │   ├── node.py             # Field Node model
│   │   ├── emergency_event.py  # Emergency SOS event model
│   │   ├── packet_log.py       # Packet traffic log model
│   │   ├── sensor_log.py       # Sensor telemetry log model
│   │   └── outbound_message.py # Outbound queue message model
│   ├── queues/                 # Async Queue Workers
│   │   ├── ack_queue.py        # Background down-link ACK worker
│   │   └── outbound_queue.py   # Scheduled outbound message worker
│   ├── repositories/           # Data access repository layer
│   ├── routers/                # FastAPI Page & Endpoint Routers
│   │   ├── dashboard.py        # Web dashboard route
│   │   ├── emergency.py        # SOS Emergency management routes
│   │   ├── gateway.py          # Radio parameter config routes
│   │   ├── nodes.py            # Node management routes
│   │   ├── outbound.py         # Outbound message queue routes
│   │   ├── sensor.py           # Sensor telemetry routes
│   │   ├── stats.py            # System health & packet statistics
│   │   └── websocket.py        # Real-time WebSocket endpoint (/ws)
│   ├── schemas/                # Pydantic Schemas & DTOs
│   │   ├── enums.py            # Packet, Node, Outbound Enums
│   │   ├── packets.py          # Packet validation models
│   │   ├── nodes.py            # Node response schemas
│   │   ├── emergencies.py      # Emergency schemas
│   │   ├── outbound.py         # Outbound message schemas
│   │   └── dashboard.py        # Dashboard telemetry DTOs
│   ├── services/               # Core Business Logic Services
│   │   ├── lora_receiver.py    # SPI LoRa packet listener task
│   │   ├── packet_parser.py    # Binary/JSON packet parser
│   │   ├── packet_validator.py # Schema & range validation service
│   │   ├── duplicate_detector.py # Sliding window deduplicator
│   │   ├── emergency_detector.py # SOS & vital anomaly detector
│   │   ├── packet_processor.py # Main packet processing pipeline
│   │   ├── ack_service.py      # Downlink ACK packet generator
│   │   ├── node_manager.py     # Node activity & 15-min timeout checker
│   │   └── websocket_manager.py# Active WebSocket connection broker
│   ├── static/                 # Static web assets (CSS / JS)
│   ├── templates/              # Jinja2 HTML Dashboard Templates
│   │   ├── dashboard.html      # Main Emergency Command Center
│   │   ├── nodes.html          # Node management table
│   │   └── history.html        # Telemetry history log
│   └── main.py                 # FastAPI application instantiation & lifespan
├── docs/                       # Project Documentation & Architecture Guides
├── tests/                      # Unit and Integration test scripts
├── .env                        # Environment Configuration file
├── Dockerfile                  # Container deployment instructions
├── alembic.ini                 # Alembic configuration file
├── requirements.txt            # Python dependencies
├── run.py                      # Application entry point script
├── test_gateway_processing.py  # End-to-end packet processing test
└── test_setup.py               # Setup & configuration verification script
```

---

## 🚀 Getting Started

### Prerequisites

- **Python**: `3.11` or higher
- **PostgreSQL**: `15` or higher (installed locally or via Docker)
- **Git**

### Environment Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/abhay2121-git/LoRa-PLB-gateway.git
   cd LoRa-PLB-gateway
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   # On Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # On Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables (`.env`)**:
   Create or verify your `.env` file in the root directory:
   ```env
   APP_NAME="LoRa PLB Gateway"
   APP_VERSION="1.0.0"
   DEBUG=True
   LOG_LEVEL="INFO"
   HOST="0.0.0.0"
   PORT=8000

   # Database Connection String
   DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/plb_gateway"

   # Gateway Identification
   GATEWAY_ID="GATEWAY_01"

   # LoRa Transceiver Parameters
   LORA_FREQUENCY=433.0
   LORA_BANDWIDTH=125000
   LORA_CODING_RATE=5
   LORA_SPREADING_FACTOR=7
   LORA_TX_POWER=17

   # SPI / GPIO Hardware Pins
   SPI_BUS=0
   SPI_DEVICE=0
   GPIO_RESET_PIN=25
   GPIO_DIO0_PIN=24

   # Timeouts & Workers
   HEARTBEAT_TIMEOUT_SECONDS=900
   DUPLICATE_CACHE_TTL_SECONDS=3600
   ```

### Database Setup

1. **Create the PostgreSQL Database**:
   ```sql
   CREATE DATABASE plb_gateway;
   ```

2. **Run Alembic Migrations**:
   ```bash
   alembic upgrade head
   ```

### Running the Gateway

Start the server using `run.py` or `uvicorn`:

```bash
python run.py
```

Or using `uvicorn` directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Access points once running:
- 📊 **Web Dashboard**: [http://localhost:8000/](http://localhost:8000/)
- 📖 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🔍 **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- 💚 **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🐳 Docker Deployment

You can build and deploy the application in a Docker container.

### 1. Build the Docker Image
```bash
docker build -t lora-plb-gateway .
```

### 2. Run the Container
```bash
docker run -d \
  --name lora-plb-gateway \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+psycopg://postgres:postgres@host.docker.internal:5432/plb_gateway" \
  lora-plb-gateway
```

---

## 📡 Packet Protocols & Data Format

The gateway accepts both binary payloads and JSON packets sent via LoRa RF or the API ingestion endpoint.

### 1. Emergency Distress Packet (`SOS`)
Sent by personal location beacons during an emergency:
```json
{
  "packet_id": "PKT-1008",
  "node_id": "NODE_04",
  "packet_type": "SOS",
  "emergency_id": "EMG-1008",
  "sequence_number": 1,
  "latitude": 21.1458,
  "longitude": 79.0882,
  "heart_rate": 145,
  "spo2": 92.0,
  "temperature": 38.8,
  "battery": 76.0,
  "sos": true,
  "retry_count": 0
}
```

### 2. Heartbeat Packet (`HEARTBEAT`)
Periodic node keep-alive status sent every few minutes:
```json
{
  "packet_id": "HB-00042",
  "node_id": "NODE_04",
  "packet_type": "HEARTBEAT",
  "battery": 95.0
}
```

### 3. Downlink Acknowledgment (`ACK`)
Automatically returned by the gateway to confirm reception:
```json
{
  "status": "ACK",
  "packet_id": "PKT-1008",
  "node_id": "NODE_04",
  "packet_type": "SOS",
  "received_at": "2026-08-10T22:45:00Z",
  "message": "Packet PKT-1008 processed successfully"
}
```

---

## 🔌 API & WebSocket Documentation

### Main REST API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Gateway application health status |
| `POST` | `/api/v1/packets` | Submit raw/JSON packet for ingestion |
| `GET` | `/api/v1/packets/logs` | Fetch packet traffic logs with filtering |
| `GET` | `/api/v1/nodes` | List all registered nodes & statuses |
| `GET` | `/api/v1/nodes/{node_id}` | Get detailed node profile & telemetry |
| `GET` | `/api/v1/emergencies` | List active emergency SOS events |
| `POST` | `/api/v1/emergencies/{emergency_id}/resolve` | Resolve an emergency SOS event |
| `GET` | `/api/v1/stats` | Gateway radio metrics & packet stats |
| `POST` | `/api/v1/gateway/config` | Update LoRa frequency, power, SF settings |
| `POST` | `/api/v1/outbound` | Queue an outbound downlink message to a node |
| `GET` | `/ws` | WebSocket endpoint for real-time dashboard events |

---

## 🧪 Testing & Verification

The repository includes standalone validation and testing scripts to verify configuration, database tables, and packet processing pipeline logic.

### 1. Verify Gateway Configuration & Database Tables
```bash
python test_setup.py
```
*Validates `.env` variables, verifies database connections, builds schemas, and validates model instantiation.*

### 2. Run End-to-End Packet Processing Pipeline Test
```bash
python test_gateway_processing.py
```
*Simulates incoming Heartbeat packets, emergency SOS distress signals, and duplicate retransmission filtering.*

### 3. AI Priority Engine

The deployed priority engine runs in-process after packet validation, duplicate checking, and gateway interpretation. `HEARTBEAT` packets bypass inference. A `MESSAGE` whose predefined text is `SOS` or `HAZARD` is resolved before the model; ordinary messages remain `MESSAGE`.

The model receives `packet_type`, `heart_rate`, `spo2`, `battery`, `retry_count`, and `hop_count`. `packet_type` uses protocol codes SOS=`1`, HAZARD=`2`, MESSAGE=`3` and is one-hot encoded by the exported preprocessing artifact. Predictions are returned as both `priority_code` and `priority`, mapped as `1=LOW`, `2=MEDIUM`, `3=HIGH`, `4=CRITICAL`.

Training is external to `app/ml/` and does not run when the gateway starts:

```bash
python ml-training/train.py --dataset path/to/priority_dataset.xlsx --output-dir .
python ml-training/evaluate.py --dataset path/to/priority_dataset.xlsx
```

For development-only pipeline checks, synthetic data must be explicitly requested:

```bash
python ml-training/train.py --synthetic --output-dir .
python ml-training/evaluate.py --synthetic
```

Synthetic metrics are not medical, scientific, or operational validation. Replace the dataset before deployment. Copy the resulting `priority_model.pkl` and `preprocessor.pkl` together to the Raspberry Pi. The gateway caches both trusted local artifacts and reports inference errors without assigning a fake priority.

Priority is exposed in the packet-processing API response and dashboard WebSocket event. It is also persisted as nullable `priority_code` and `priority_label` fields on `emergency_events`, then displayed in the Emergency History table. Existing events created before the migration have no priority value and display `-`.

---

## ⚙️ Configuration Settings

| Setting Key | Default | Description |
| :--- | :--- | :--- |
| `APP_NAME` | `"LoRa PLB Gateway"` | Application Name |
| `DATABASE_URL` | `"postgresql+psycopg://..."` | PostgreSQL connection URI |
| `GATEWAY_ID` | `"GATEWAY_01"` | Unique identifier for this gateway |
| `LORA_FREQUENCY` | `433.0` | RF Frequency in MHz |
| `LORA_BANDWIDTH` | `125000` | Bandwidth in Hz (125 kHz) |
| `LORA_SPREADING_FACTOR` | `7` | LoRa Spreading Factor (SF7) |
| `LORA_TX_POWER` | `17` | Transmission Power in dBm |
| `HEARTBEAT_TIMEOUT_SECONDS` | `900` | Node offline timeout (15 mins) |
| `DUPLICATE_CACHE_TTL_SECONDS` | `3600` | Duplicate packet cache duration |

---

## 📄 License

This project is open-source software licensed under the [MIT License](LICENSE).

---

<p align="center">
  <b>LoRa PLB Gateway</b> — Empowering Low-Power, Long-Range Search & Rescue Communications 📡
</p>
