# Smart City IoT Monitoring — Kafka Data Pipeline

Educational Smart City project that simulates environmental sensors in Yerevan districts, streams readings through **Apache Kafka**, stores them in **SQLite**, and visualizes them with **Streamlit**.

This branch (`kafka-pipeline`) replaces the MQTT transport from `master` with Apache Kafka.

## Overview

The system demonstrates a complete data flow:

```text
Sensor Simulator
       ↓
Kafka Producer
       ↓
Apache Kafka Broker + Topic (smart-city-sensor-data)
       ↓
Kafka Consumer
       ↓
Data Processing (validation + range checks + air-quality category)
       ↓
SQLite Database
       ↓
Streamlit Dashboard
```

Districts: **Kentron**, **Erebuni**, **Nor Nork**, **Malatsia**

## Problem Description

A smart city needs reliable delivery of sensor telemetry from many locations to storage and dashboards.

In the first assignment we used MQTT (Mosquitto).  
In this assignment we redesign the same pipeline around **Apache Kafka** to practice:

- durable topic storage
- producers and consumers
- consumer groups and offsets
- JSON serialization
- restart-safe consumption

## Apache Kafka Concepts Used in This Project

| Concept | How it appears here |
|---|---|
| **Broker** | Local single-node Kafka on `localhost:9092` (KRaft mode, no ZooKeeper) |
| **Topic** | `smart-city-sensor-data` |
| **Partition** | 1 partition (enough for a local academic demo) |
| **Producer** | `simulator/kafka_publisher.py` |
| **Consumer** | `subscriber/kafka_consumer.py` |
| **Consumer group** | `smartcity-sensor-consumers` |
| **Offset** | Kafka remembers how far the group has read |
| **Serialization** | Python dict → JSON UTF-8 bytes |
| **Deserialization** | UTF-8 bytes → JSON → validated dict |

## Architecture

```text
sensor_simulator.py
        │
        ▼
run_kafka_publisher.py  ──publish──►  Kafka topic: smart-city-sensor-data
                                              │
                                              ▼
                               run_kafka_consumer.py
                                      │
                          validate + process_reading()
                                      │
                                      ▼
                               data/smartcity.db
                                      │
                                      ▼
                               dashboard/app.py
```

## Example Message

```json
{
  "sensor_id": "sensor_01",
  "location": "Kentron",
  "timestamp": "2026-11-08T20:51:51.651139+00:00",
  "temperature": 4.4,
  "humidity": 79.38,
  "air_quality": 46.72
}
```

### Explanation of output

- `sensor_id` / `location` — which virtual sensor and Yerevan district
- `timestamp` — measurement time (UTC ISO-8601)
- `temperature` — Celsius
- `humidity` — relative humidity, percent
- `air_quality` — unitless index on a **0..150** scale used by the simulator  
  Processing classifies it as `good` (≤50), `moderate` (≤100), or `unhealthy` (>100)

## Project Structure

```text
.
├── simulator/
│   ├── sensor_simulator.py      # reusable sensor generator
│   ├── kafka_publisher.py       # Kafka producer
│   └── run_kafka_publisher.py
├── subscriber/
│   ├── message_validator.py     # JSON schema/field checks
│   ├── processing.py            # range checks + air-quality category
│   ├── kafka_consumer.py        # Kafka consumer
│   └── run_kafka_consumer.py    # consume → process → SQLite
├── database/
│   ├── db.py
│   └── check_db.py
├── dashboard/
│   └── app.py
├── tools/
│   ├── setup_kafka.sh           # download + format Kafka (first time)
│   ├── start_kafka.sh
│   ├── stop_kafka.sh
│   └── kafka-config/            # KRaft server.properties
├── data/                        # smartcity.db (local, gitignored)
├── start_demo.sh                # one-command Kafka demo
├── requirements.txt
└── README.md
```

> Note: the Kafka binary distribution is **not** committed (`tools/kafka/` is gitignored, ~130MB).  
> Run `./tools/setup_kafka.sh` once after cloning.

## Requirements

- Ubuntu / Linux
- Python 3.12+
- Java 17+ (required by Kafka)

Install Java if needed:

```bash
sudo apt update
sudo apt install -y openjdk-17-jre-headless
java -version
```

## How to Install and Run

### 1. Clone and enter the Kafka branch

```bash
git clone git@github.com:LyudmilaKostanyan/Smart-City-IoT-Monitoring.git
cd Smart-City-IoT-Monitoring
git checkout kafka-pipeline
```

### 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Download and prepare Kafka (first time only)

```bash
./tools/setup_kafka.sh
```

This downloads Apache Kafka **4.1.2**, formats local KRaft storage, and creates topic `smart-city-sensor-data`.

### 4. Quick start (recommended)

```bash
./start_demo.sh
```

Opens the dashboard at [http://localhost:8501](http://localhost:8501).  
Stop everything with `Ctrl+C`.

### 5. Manual start (4 terminals)

```bash
# Terminal 1 — Kafka
./tools/start_kafka.sh

# Terminal 2 — Consumer
source .venv/bin/activate
cd subscriber
python run_kafka_consumer.py

# Terminal 3 — Publisher
source .venv/bin/activate
cd simulator
python run_kafka_publisher.py --cycles 0 --interval 2

# Terminal 4 — Dashboard
source .venv/bin/activate
cd dashboard
streamlit run app.py
```

Inspect database:

```bash
source .venv/bin/activate
cd database
python check_db.py --limit 20
```

## How to Stop the System

- If using `./start_demo.sh`: press `Ctrl+C`
- Or stop components manually:

```bash
# stop publisher/consumer/dashboard with Ctrl+C in their terminals
./tools/stop_kafka.sh
```

## Differences Between MQTT and Kafka

| | MQTT branch (`master`) | Kafka branch (`kafka-pipeline`) |
|---|---|---|
| Transport | Eclipse Mosquitto | Apache Kafka (KRaft) |
| Port | `1883` | `9092` |
| Topic | `smartcity/sensors` | `smart-city-sensor-data` |
| Client library | `paho-mqtt` | `kafka-python` |
| Message durability | Primarily for live delivery | Topic retains messages; offsets track progress |
| Restart behavior | New subscriber usually sees only new messages | Same consumer group can resume from committed offset |
| Shared parts | Sensor simulator, SQLite schema, Streamlit dashboard | Same |

Switch branches:

```bash
git checkout master          # MQTT version
git checkout kafka-pipeline  # Kafka version
```

## Useful Kafka Commands

```bash
# list topics
./tools/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list

# watch messages
./tools/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic smart-city-sensor-data \
  --from-beginning
```

Important: the flag is `--bootstrap-server` (with a hyphen), not `--bootstrap=server`.
