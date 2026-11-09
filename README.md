# Smart City IoT Monitoring + Cybersecurity Risk Assessment

Educational Smart City project:

1. **MQTT environmental monitoring** — virtual sensors, Mosquitto, SQLite, Streamlit.
2. **Assignment №13 — Cybersecurity Risk Assessment** — Threat Model, risk scoring, recommendations, security dashboard, and assessment report.

Branch for this assignment: `security-risk-assessment` (created from `master`).

> Defensive analysis only. This repository does **not** include exploit code, attack scripts, or automatic hardening of Mosquitto authentication.

---

## Overview

The project models environmental monitoring across Yerevan districts and, on top of that architecture, performs an educational cybersecurity risk assessment:

- asset, entry-point, and trust-boundary analysis;
- structured Threat Model (10 threats);
- risk scoring with `Probability × Impact`;
- security control recommendations;
- interactive Streamlit security dashboard;
- Markdown report `security_assessment.md`.

Districts: **Kentron**, **Erebuni**, **Nor Nork**, **Malatsia**

Sensor reading fields: `sensor_id`, `location`, `timestamp`, `temperature`, `humidity`, `air_quality`

---

## Problem Description

A Smart City collects sensor telemetry. If the MQTT broker, transport channel, database, or dashboard is insufficiently protected, the following may occur:

- unauthorized broker access;
- spoofed sensor readings;
- message interception;
- denial of service (DDoS) against the broker;
- unauthorized SQLite access;
- data theft;
- ransomware impact on application data;
- dashboard viewing without authentication.

The goal of Assignment №13 is not to attack the system, but to **model threats**, assess risks, and propose mitigations.

---

## Threat Modeling Concepts

| Concept | Meaning |
|---|---|
| Asset | What we protect (telemetry, broker, database, UI, trust in the source) |
| Entry point | Where the system accepts external interaction |
| Trust boundary | Where trust assumptions change |
| Threat | A potential negative impact |
| Existing control | A control already confirmed in code/config |
| Proposed control | A recommendation that is not auto-applied |
| Illustrative risk | Educational P/I estimate without penetration testing |

Evidence labels:

- **Confirmed finding** — visible in code/config;
- **Hypothetical scenario** — educational attack scenario;
- **Proposed improvement** — recommended control, not an implemented fact.

---

## System Architecture

### MQTT monitoring data flow

```text
Sensor Simulator
       |
       v
MQTT Publisher ----> Mosquitto Broker (:1883, topic smartcity/sensors)
                            |
                            v
                     MQTT Subscriber + validator
                            |
                            v
                     SQLite (data/smartcity.db)
                            |
                            v
                     Streamlit Monitoring UI (:8501)
```

### Security analysis modules

```text
security/threats.py            Threat Model
security/risk_calculator.py    Risk Score = P × I
security/recommendations.py    Existing vs proposed controls
security_dashboard.py          Interactive security UI
security_assessment.md         Full assessment report
tests/                         Unit tests
```

---

## Risk Assessment Methodology

Educational formula (not an official standard):

```text
Risk Score = Probability × Impact
```

Probability / Impact ∈ {1, 2, 3, 4, 5}

| Score | Level |
|---|---|
| 1–7 | Low |
| 8–14 | Medium |
| 15–25 | High |

Thresholds are configurable through `RiskThresholds` in `security/risk_calculator.py`.

Initial scores are `illustrative_estimate` values based on the Stage 1 static review.

---

## Example Output

```text
Threat ID | P | I | Score | Level
T-01      | 4 | 4 | 16    | High   Unauthorized MQTT broker access
T-02      | 4 | 4 | 16    | High   Sensor data spoofing
T-03      | 2 | 3 | 6     | Low    MQTT message interception
T-04      | 2 | 4 | 8     | Medium DDoS against the MQTT broker
T-05      | 3 | 3 | 9     | Medium Unauthorized database access
T-06      | 3 | 4 | 12    | Medium Data theft
T-07      | 2 | 5 | 10    | Medium Ransomware affecting application data
T-08      | 4 | 3 | 12    | Medium Unauthorized dashboard access
T-09      | 3 | 2 | 6     | Low    Malicious or malformed sensor messages
T-10      | 2 | 4 | 8     | Medium IoT device or sensor compromise

Summary: total=10, high=2, medium=6, low=2, highest_score=16
```

Programmatically:

```bash
source .venv/bin/activate
python - <<'PY'
from security.risk_calculator import assess_all, summarize_assessments
rows = assess_all()
print(summarize_assessments(rows))
for row in rows:
    print(row.threat_id, row.risk_score, row.risk_level, row.threat_name)
PY
```

---

## Explanation of Output

- **T-01 / T-02 = High** because `tools/mosquitto/mosquitto.conf` confirms `allow_anonymous true`, while the validator checks message schema but not publisher identity.
- **T-09 = Low** because malformed payloads are already rejected by `message_validator.py`.
- **T-03 = Low** in the localhost demo context: TLS is absent, but practical interception on loopback is less likely.
- Values can be changed in `security_dashboard.py` (session what-if); that is not a new penetration test.

---

## How to Install and Run

### Requirements

- Ubuntu / Linux
- Python 3.12+
- Packages from `requirements.txt`: `paho-mqtt`, `streamlit`, `pandas`, `plotly`
- Local Mosquitto under `tools/mosquitto/` (no `sudo` install required)

### First-time setup

```bash
cd /home/lyudmila/Desktop/tt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### A) Environmental monitoring (original system)

Quick demo:

```bash
cd /home/lyudmila/Desktop/tt
./start_demo.sh
```

Or 4 terminals (`source .venv/bin/activate` in each):

```bash
# 1) Broker
./tools/mosquitto/start_broker.sh

# 2) Subscriber
cd subscriber
python run_subscriber.py

# 3) Publisher
cd simulator
python run_publisher.py --cycles 0 --interval 2

# 4) Monitoring dashboard
cd dashboard
streamlit run app.py
```

Monitoring UI: [http://localhost:8501](http://localhost:8501)

### B) Security risk assessment

```bash
cd /home/lyudmila/Desktop/tt
source .venv/bin/activate

# Unit tests
python -m unittest discover -s tests -v

# Security dashboard
streamlit run security_dashboard.py
```

Report:

```bash
less security_assessment.md
```

---

## Supported Parameters

### Publisher (`simulator/run_publisher.py`)

| Parameter | Default | Meaning |
|---|---|---|
| `--host` | `localhost` | MQTT broker host |
| `--port` | `1883` | MQTT broker port |
| `--topic` | `smartcity/sensors` | Publish topic |
| `--interval` | `2.0` | Seconds between cycles |
| `--cycles` | `5` | Number of cycles; `0` = infinite |

### Subscriber (`subscriber/run_subscriber.py`)

| Parameter | Default | Meaning |
|---|---|---|
| `--host` | `localhost` | MQTT broker host |
| `--port` | `1883` | MQTT broker port |
| `--topic` | `smartcity/sensors` | Subscribe topic |
| `--db` | `data/smartcity.db` | SQLite path |
| `--max-messages` | `0` | Stop after N valid messages; `0` = until Ctrl+C |

### Console simulator only (`simulator/run_simulator.py`)

| Parameter | Default | Meaning |
|---|---|---|
| `--cycles` | (see script help) | Number of local cycles |
| `--interval` | (see script help) | Delay between cycles |

### Risk engine (`security/risk_calculator.py`)

| Parameter / API | Range / Default | Meaning |
|---|---|---|
| `probability` | `1..5` | Likelihood factor |
| `impact` | `1..5` | Impact factor |
| `RiskThresholds.low_max` | `7` | Max score for Low |
| `RiskThresholds.medium_max` | `14` | Max score for Medium |
| `RiskThresholds.high_max` | `25` | Max score for High |
| `assess_all(overrides=...)` | optional `(P, I)` map | What-if overrides per threat |

### Security dashboard (UI)

- Select threat `T-01`…`T-10`
- Change Probability / Impact sliders
- Recalculate score/level
- Apply to session / Reset threat / Reset all
- View recommendations for the selected threat

No CLI flags are required for `security_dashboard.py` beyond Streamlit’s own options, for example:

```bash
streamlit run security_dashboard.py --server.port 8502
```

---

## Security Recommendations

### Already present (confirmed)

- Default MQTT client host `localhost`
- Sensor JSON schema validation
- Parameterized SQL queries
- Invalid MQTT payloads ignored by subscriber
- `*.db` ignored by Git

### Proposed (not auto-applied)

- Disable anonymous MQTT (`allow_anonymous false`) + authentication
- MQTT ACLs for publish/subscribe
- TLS for MQTT
- Network filtering / loopback binding
- Connection / rate limits
- Restrict OS permissions on `data/smartcity.db`
- Protected backups + recovery procedure
- Dashboard authentication / reverse-proxy access control
- Stronger semantic validation and anomaly monitoring
- Per-device credentials for real IoT deployments

Details: `security/recommendations.py` and section 10 of `security_assessment.md`.

---

## Limitations

1. This is **not** a penetration test and not a red-team exercise.
2. Probability/Impact values are illustrative estimates.
3. OS firewall, exact bind address, and database file mode were not audited dynamically.
4. Branches `kafka-pipeline` and `digital-twin` are not the primary scope of this assessment.
5. The security dashboard does not change Mosquitto configuration.
6. Recommendations are not applied automatically without explicit permission.

---

## Project structure

```text
tt/
├── simulator/                 # virtual sensors + MQTT publisher
├── subscriber/                # MQTT subscriber + validation
├── database/                  # SQLite helpers
├── dashboard/                 # environmental Streamlit UI
├── data/                      # smartcity.db (gitignored)
├── tools/mosquitto/           # local Mosquitto broker
├── security/                  # threat model, risk engine, recommendations
├── tests/                     # unit tests
├── security_dashboard.py      # security Streamlit UI
├── security_assessment.md     # assessment report (Russian)
├── requirements.txt
├── start_demo.sh
└── README.md
```

## MQTT topic

```text
smartcity/sensors
```

## Useful checks

```bash
cd database
python check_db.py --limit 50
```

Manual MQTT test:

```bash
source tools/mosquitto/env.sh
mosquitto_sub -h localhost -t 'smartcity/sensors'
```

```bash
source tools/mosquitto/env.sh
mosquitto_pub -h localhost -t 'smartcity/sensors' -m '{"hello":"test"}'
```

## Notes for demo

1. Start monitoring components in order: **Broker → Subscriber → Publisher → Dashboard**.
2. If the monitoring dashboard is empty, check Subscriber + Publisher.
3. `--cycles 3` means 3 rounds × 4 sensors = **12 rows**.
4. Do not open `data/smartcity.db` as a text file; use `check_db.py`.
5. Keep `dashboard/app.py` for environment monitoring and `security_dashboard.py` for risk assessment.
