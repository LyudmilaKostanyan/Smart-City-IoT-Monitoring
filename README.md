# Smart City IoT Monitoring — Digital Twin

Educational Smart City project that simulates environmental sensors for Yerevan districts, streams measurements through **MQTT (Mosquitto)** into **SQLite**, and exposes a **Digital Twin** dashboard in **Streamlit**.

This branch (`digital-twin`) extends the original MQTT monitoring system with a conceptual Digital Twin workflow:

```text
Real City (simulated) → Sensors → Data Platform → Digital Twin → Simulation → Decision
```

## Overview

The application demonstrates how changes in a simulated city appear in a digital model, how hypothetical scenarios can be tested without overwriting live sensor data, and how simple rule-based recommendations can be generated.

Virtual districts:

- **Kentron** (`sensor_01`)
- **Arabkir** (`sensor_02`)
- **Shengavit** (`sensor_03`)

## Problem Description

A city monitoring system collects environmental telemetry, but decision makers also need:

1. a current digital state of each district;
2. a way to explore “what if” scenarios;
3. clear warnings and recommendations.

This prototype keeps the existing IoT pipeline and adds a Digital Twin layer on top of SQLite.

Important: the “real city” in this project is **simulated**. The application is not connected to actual city infrastructure.

## Digital Twin Concepts

| Concept | Meaning in this project |
|---|---|
| **Real City (simulated)** | Virtual sensors generate environmental readings |
| **Sensors** | `sensor_simulator.py` |
| **Data Platform** | Mosquitto + MQTT subscriber + SQLite |
| **Digital Twin** | Latest known state of each district + freshness |
| **Simulation** | Hypothetical temperature/humidity/air-quality values |
| **Decision** | Rule-based warnings and recommendations |

Difference between raw measurements and twin state:

- SQLite stores a history of sensor readings.
- The Digital Twin stores the **latest known state** of each district and whether that state is `current`, `stale`, or `no_data`.

## System Architecture

```text
Sensor Simulator
      |
      v
MQTT Publisher  --->  Mosquitto Broker (topic: smartcity/sensors)
      |
      v
MQTT Subscriber + validator
      |
      v
SQLite (data/smartcity.db)
      |
      v
Digital Twin State Manager
      |
      +----------------------+
      |                      |
      v                      v
District Model         Simulation Engine
      |                      |
      +----------+-----------+
                 |
                 v
          Decision Engine
                 |
                 v
       Streamlit Digital Twin UI
```

## Existing Components Reused

- `simulator/sensor_simulator.py` — environmental data generation
- `simulator/mqtt_publisher.py`, `simulator/run_publisher.py` — MQTT publish path
- `subscriber/*` — MQTT subscribe, validation, SQLite write
- `database/db.py` — SQLite schema and queries
- `tools/mosquitto/*` — local Mosquitto broker
- Streamlit runtime and pandas tables for the UI

## New Components

```text
digital_twin/
  models.py            # district definitions, state, freshness
  state_manager.py     # sync twin state from SQLite
  simulation.py        # hypothetical scenarios (no SQLite writes)
  decision_engine.py   # warnings and recommendations
dashboard/app.py       # Digital Twin UI only
tests/                 # unit tests for twin modules
```

## Example Output

### Live sensor measurement

```json
{
  "sensor_id": "sensor_01",
  "location": "Kentron",
  "timestamp": "2026-11-09T02:41:31.169010+00:00",
  "temperature": 3.8,
  "humidity": 79.75,
  "air_quality": 45.63
}
```

### Decision result after hypothetical simulation

```json
{
  "district": "Kentron",
  "status": "warning",
  "warnings": [
    "High temperature detected",
    "Elevated air pollution detected",
    "Multiple environmental parameters exceed demo thresholds"
  ],
  "recommendations": [
    "Increase heat-stress monitoring frequency for this district",
    "Increase environmental monitoring and investigate possible sources",
    "Treat this as a combined risk scenario and review all parameters together"
  ]
}
```

### Explanation of output

- Baseline values come from MQTT sensor data stored in SQLite.
- Simulated values are entered in the UI and never overwrite SQLite.
- `status=warning` means one or more demo thresholds were exceeded.
- `status=uncertain` means data is missing or stale.
- `status=normal` means evaluated values are inside configured demo ranges.

## How to Install and Run

### Requirements

- Ubuntu / Linux
- Python 3.12+

```bash
git clone git@github.com:LyudmilaKostanyan/Smart-City-IoT-Monitoring.git
cd Smart-City-IoT-Monitoring
git checkout digital-twin

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Quick start

```bash
./start_demo.sh
```

Opens [http://localhost:8501](http://localhost:8501)

This starts:

1. Mosquitto
2. MQTT subscriber
3. MQTT publisher (continuous sensor simulation)
4. Streamlit Digital Twin dashboard

Stop with `Ctrl+C`.

### Manual start (4 terminals)

```bash
# Terminal 1
./tools/mosquitto/start_broker.sh

# Terminal 2
source .venv/bin/activate
cd subscriber
python run_subscriber.py

# Terminal 3
source .venv/bin/activate
cd simulator
python run_publisher.py --cycles 0 --interval 2

# Terminal 4
source .venv/bin/activate
cd dashboard
streamlit run app.py
```

### Run tests

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Latest verification on this branch:

```text
Ran 13 tests in 0.030s
OK
```

## Simulation Parameters

| Parameter | UI range | Notes |
|---|---|---|
| Temperature | -10 … 50 °C | Demo Celsius values |
| Humidity | 0 … 100 % | Relative humidity |
| Air quality | 0 … 150 | Project index (not official AQI) |

Decision demo thresholds (configurable in code):

- high temperature: `> 35 °C`
- elevated air quality index: `> 70`
- humidity outside: `20 … 90 %`
- stale data: older than `60` seconds

These thresholds are for university demonstration only. They are not official environmental standards.

## How to Stop the Application

- If started with `./start_demo.sh`: press `Ctrl+C`
- Or stop publisher/subscriber/dashboard with `Ctrl+C` and run:

```bash
./tools/mosquitto/stop_broker.sh
```

## Branch Map

```text
master           Original MQTT monitoring system
kafka-pipeline   Apache Kafka data pipeline
digital-twin     MQTT monitoring + Digital Twin (this branch)
```

Switch branches:

```bash
git checkout master
git checkout kafka-pipeline
git checkout digital-twin
```

## Limitations and Assumptions

- The city and sensors are simulated; there is no live municipal integration.
- Air-quality values use a simple 0..150 demonstration index.
- Decision rules are educational heuristics, not certified risk models.
- Simulation is hypothetical and does not forecast weather or pollution scientifically.
- Historical rows from older district names (for example `Erebuni`) are ignored by the twin synchronizer.
- Freshness threshold of 60 seconds is a demo SLA, not a city operations requirement.
