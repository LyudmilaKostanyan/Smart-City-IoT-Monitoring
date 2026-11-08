# Smart City Environmental Monitoring System

Educational IoT project that simulates environmental sensors across Yerevan districts, transfers readings over MQTT, stores them in SQLite, and visualizes them in a Streamlit dashboard.

## Architecture

```text
Sensor Simulator → MQTT Publisher → Mosquitto Broker
                                          ↓
                                   MQTT Subscriber
                                          ↓
                                      SQLite DB
                                          ↓
                                 Streamlit Dashboard
```

Districts: **Kentron**, **Erebuni**, **Nor Nork**, **Malatsia**

Each reading contains:

- `sensor_id`
- `location`
- `timestamp`
- `temperature`
- `humidity`
- `air_quality`

## Requirements

- Ubuntu / Linux
- Python 3.12+
- Project virtual environment (already prepared in `.venv`)

Python packages are listed in `requirements.txt`:

- `paho-mqtt`
- `streamlit`
- `pandas`
- `plotly`

SQLite is included in Python’s standard library. Eclipse Mosquitto is bundled locally under `tools/mosquitto/` (no `sudo` install required).

## First-time setup

```bash
cd /home/lyudmila/Desktop/tt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick start (one script)

Starts broker, subscriber, publisher, dashboard, and opens the browser:

```bash
cd /home/lyudmila/Desktop/tt
./start_demo.sh
```

Stop everything with `Ctrl+C`.

## How to run (4 terminals)

Activate the virtual environment in every terminal:

```bash
cd /home/lyudmila/Desktop/tt
source .venv/bin/activate
```

### 1. Start MQTT Broker

```bash
./tools/mosquitto/start_broker.sh
```

Expected output: broker listening on `localhost:1883`.

Stop later with:

```bash
./tools/mosquitto/stop_broker.sh
```

> Do **not** run broker scripts with `source`. Use `./tools/mosquitto/start_broker.sh`.

### 2. Start MQTT Subscriber (saves to SQLite)

```bash
cd subscriber
python run_subscriber.py
```

Database file: `data/smartcity.db`

### 3. Start MQTT Publisher (sensor simulator)

```bash
cd simulator
python run_publisher.py --cycles 0 --interval 2
```

- `--cycles 0` — run forever (stop with `Ctrl+C`)
- `--cycles 3` — run 3 cycles only
- each cycle publishes **4** sensor messages (one per district)

Optional console-only simulator (no MQTT):

```bash
cd simulator
python run_simulator.py --cycles 5 --interval 2
```

### 4. Start Streamlit Dashboard

```bash
cd dashboard
streamlit run app.py
```

Open in browser: [http://localhost:8501](http://localhost:8501)

## Useful checks

Inspect stored readings:

```bash
cd database
python check_db.py --limit 50
```

Manual MQTT test (optional):

```bash
source tools/mosquitto/env.sh
mosquitto_sub -h localhost -t 'smartcity/sensors'
```

In another terminal:

```bash
source tools/mosquitto/env.sh
mosquitto_pub -h localhost -t 'smartcity/sensors' -m '{"hello":"test"}'
```

## Project structure

```text
tt/
├── simulator/          # virtual sensors + MQTT publisher
├── subscriber/         # MQTT subscriber + validation
├── database/           # SQLite helpers
├── dashboard/          # Streamlit UI
├── data/               # smartcity.db
├── tools/mosquitto/    # local Mosquitto broker
├── requirements.txt
└── README.md
```

## MQTT topic

All sensor readings are published to:

```text
smartcity/sensors
```

## Notes for demo

1. Start components in this order: **Broker → Subscriber → Publisher → Dashboard**.
2. If the dashboard is empty, check that Subscriber is running and Publisher is sending data.
3. `--cycles 3` means 3 rounds × 4 sensors = **12 rows**, not 3 rows.
4. Do not open `data/smartcity.db` as a text file; use `check_db.py`.
