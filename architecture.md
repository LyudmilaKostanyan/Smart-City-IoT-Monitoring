# Smart City Multilayer Architecture Design

**Assignment №1 — Smart City Multilayer Architecture Design**  
*(Smart City-ի բազմաշերտ ճարտարապետության նախագծում)*  
**Repository:** Smart-City-IoT-Monitoring  
**Branch:** `smart-city-architecture` (from `master`)  
**Document type:** conceptual architecture design  

> This is an **architecture design** document, not a finished city platform.  
> Components are labeled **Existing**, **Inspiration**, or **Planned / Conceptual**.  
> This document does **not** claim that Kafka, AI anomaly detection, TLS/auth, or an admin UI are already deployed in the current MQTT demo.

---

## 1. Overview

This document describes a target seven-layer Smart City architecture for city monitoring (environment + traffic), based on the educational IoT pipeline in this repository:

- Python sensor simulator  
- MQTT (Mosquitto)  
- message validation  
- SQLite  
- Streamlit dashboard  

The architecture extends that pipeline into a full multilayer model: IoT → Network → Edge/Fog → Data Platform → AI/Analytics → Application, with a cross-cutting Security Layer.

Visualization: `architecture.mmd`, `architecture.svg`, `architecture.png`.

---

## 2. Problem Description

A modern Smart City must:

1. collect data from heterogeneous sensors;  
2. deliver it reliably and securely;  
3. process data at the edge and in a data platform;  
4. detect anomalies (for example, air pollution);  
5. present clear dashboard/alert interfaces to operators;  
6. protect the whole pipeline from unauthorized access and data spoofing.

The current educational MQTT project only covers demo environmental monitoring. For university Assignment №1, a **complete architecture** is required, where each layer has a clear purpose and a justified technology stack.

---

## 3. Architecture Goals

| Goal ID | Goal |
|---|---|
| G1 | Cover all 7 mandatory assignment layers |
| G2 | Keep a clear link to the existing MQTT demo as the starting point |
| G3 | Explicitly separate Existing from Planned |
| G4 | Provide an end-to-end data flow from sensor to alert UI |
| G5 | Make Security cross-cutting, not a disconnected last box |
| G6 | Justify technology choices for educational and target city scale |

---

## 4. Multilayer Architecture

```text
1. IoT Layer
2. Network Layer
3. Edge/Fog Layer
4. Data Platform
5. AI/Analytics Layer
6. Application Layer
7. Security Layer  (cross-cutting)
```

### 4.1 IoT Layer

- **Purpose:** collect primary measurements.  
- **Components:** environmental sensors, traffic sensors, device gateways.  
- **Technologies:** Python virtual sensors (**Existing**); field IoT devices + gateways (**Planned**).  
- **Responsibilities:** sense → encode → publish.  
- **I/O:** physical phenomena → telemetry messages.  
- **Adjacent layers:** → Network Layer.  

### 4.2 Network Layer

- **Purpose:** deliver messages from devices to processing.  
- **Components:** MQTT broker, TCP/IP connectivity, TLS/auth endpoints.  
- **Technologies:** MQTT + Mosquitto (**Existing**); city Wi-Fi/Ethernet/LPWAN + MQTT TLS (**Planned**).  
- **Responsibilities:** pub/sub routing, topics, QoS policy.  
- **I/O:** device publishes → broker fan-out to edge consumers.  
- **Adjacent layers:** IoT → Edge/Fog.  

### 4.3 Edge/Fog Layer

- **Purpose:** local validation, filtering, and light preprocessing.  
- **Components:** schema validator, filter/dedup, local preprocessor.  
- **Technologies:** `message_validator.py` (**Existing** prototype); containerized fog workers (**Planned**).  
- **Responsibilities:** reject malformed data, reduce noise, raise early threshold flags.  
- **I/O:** raw MQTT payloads → cleaned events.  
- **Adjacent layers:** Network → Data Platform.  

### 4.4 Data Platform

- **Purpose:** ingest, buffer, store, and serve data.  
- **Components:** stream ingestion, persistent storage, serving access.  
- **Technologies:** Apache Kafka (**Inspiration** from `kafka-pipeline`, **Planned**); SQLite (**Existing** demo); PostgreSQL/Timescale (**Planned** city-scale).  
- **Responsibilities:** decouple producers/consumers, retain history, support replay/query.  
- **I/O:** cleaned events → streams/tables for AI and apps.  
- **Adjacent layers:** Edge/Fog → AI/Analytics & Application.  

### 4.5 AI/Analytics Layer

- **Purpose:** analytics, anomaly detection, and decision support.  
- **Components:** environmental analytics, anomaly models/rules, decision support, optional digital twin view.  
- **Technologies:** Pandas/Plotly charts (**Existing** in the dashboard); ML/rule-based anomaly detection (**Planned**); Digital Twin (**Inspiration** from `digital-twin`).  
- **Responsibilities:** trends, anomaly scores, alert candidates.  
- **I/O:** platform data → KPIs/alerts.  
- **Adjacent layers:** Data Platform → Application.  

### 4.6 Application Layer

- **Purpose:** interfaces for operators and administrators.  
- **Components:** monitoring dashboard, admin interface, alert UI.  
- **Technologies:** Streamlit monitoring (**Existing**); admin/alert applications (**Planned**).  
- **Responsibilities:** visualization, operator acknowledgment, administrative control.  
- **I/O:** curated metrics/alerts → human decisions.  
- **Adjacent layers:** AI/Analytics + Data Platform.  

### 4.7 Security Layer (cross-cutting)

- **Purpose:** protect all layers.  
- **Components:** authentication, authorization/ACL, TLS, secure data handling, security monitoring.  
- **Technologies:** MQTT auth/ACL/TLS (**Planned**; current demo is anonymous — weak **Existing** state); dashboard auth (**Planned**); risk-assessment approach (**Inspiration** from `security-risk-assessment`).  
- **Responsibilities:** identity, access control, encryption in transit, auditability.  
- **I/O:** identities/policies → enforced controls + security events.  
- **Adjacent layers:** applies across IoT…Application.  

---

## 5. Component Responsibilities

| Component | Layer | Responsibility | Status |
|---|---|---|---|
| Environmental sensors / simulator | IoT | Generate env telemetry | Existing |
| Traffic sensors | IoT | Generate traffic telemetry | Planned |
| Device gateway | IoT | Bridge devices to MQTT | Planned |
| Mosquitto MQTT broker | Network | Pub/Sub messaging | Existing |
| TCP/IP city connectivity | Network | Transport fabric | Planned |
| Message validator | Edge/Fog | Schema/type checks | Existing |
| Filter / preprocess workers | Edge/Fog | Noise reduction, local flags | Planned |
| Apache Kafka | Data Platform | Durable stream ingestion | Planned (inspiration) |
| SQLite | Data Platform | Demo persistence | Existing |
| Timescale/PostgreSQL | Data Platform | City-scale storage | Planned |
| Environmental analytics | AI/Analytics | Trends and KPIs | Planned (+ demo charts Existing) |
| Anomaly detection | AI/Analytics | Detect abnormal pollution/traffic | Planned |
| Decision support | AI/Analytics | Produce alert candidates | Planned |
| Streamlit monitoring UI | Application | Live charts/tables | Existing |
| Admin / Alert UI | Application | Operations and alerts | Planned |
| Authn / Authz / TLS / monitoring | Security | Cross-layer protection | Planned |

---

## 6. Technology Selection and Justification

| Technology | Why selected | Why not over-engineered here |
|---|---|---|
| MQTT + Mosquitto | IoT telemetry standard; already used in the educational project | A city deployment still needs auth/TLS, but MQTT remains a suitable protocol |
| TCP/IP (+ optional LPWAN) | Universal transport for city connectivity | Sensor payloads should not fall back to ad-hoc raw TCP instead of MQTT messaging |
| Edge validation (Python service) | Cheap and clear data-quality control near the source | A full fog Kubernetes cluster can be added later |
| Apache Kafka | Reliable ingestion and fan-out to analytics/apps | SQLite is not enough for city-scale stream fan-out |
| SQLite | Ideal for a local educational demo | Not positioned as a production city warehouse |
| Streamlit | Fast monitoring UI for teaching | Admin/Alert UIs can be separate services |
| Analytics + anomaly detection | Turns data into Smart City decisions | Without an AI layer, the architecture is only a chart store |
| TLS, MQTT ACL, app auth | Address spoofing and data-leak risks | They must not be described as already enabled in the current demo config |

---

## 7. Data Flow

Primary flow:

```text
Sensors → Network (MQTT/TCP/IP) → Edge/Fog → Data Platform → AI/Analytics → Applications
```

Step by step:

1. IoT devices/gateways publish JSON telemetry.  
2. Network Layer delivers messages through MQTT topics.  
3. Edge/Fog validates and filters payloads.  
4. Data Platform accepts cleaned events (Kafka target) and stores history.  
5. AI/Analytics computes metrics and looks for anomalies.  
6. Application Layer shows dashboards and alerts to the operator.

Security controls apply at each hop: device identity, broker auth/ACL/TLS, restricted platform access, and authenticated UI.

---

## 8. Security Architecture

Security is designed as a **cross-cutting concern**:

| Control | Where it applies | Status in this design |
|---|---|---|
| Device authentication | IoT → Network | Planned |
| MQTT username/ACL | Network / topics | Planned (demo currently anonymous) |
| TLS for MQTT and UI | Network / Application | Planned |
| Schema validation | Edge/Fog | Existing prototype |
| Storage access control + backups | Data Platform | Planned |
| Controlled access to models/alerts | AI / Application | Planned |
| Security monitoring / risk review | All layers | Inspiration → Planned process |

The current `tools/mosquitto/mosquitto.conf` with `allow_anonymous true` is an educational weak state, not the target security architecture.

---

## 9. Example Smart City Scenario

### Detecting abnormal air pollution in Kentron and showing an alert

1. **IoT:** an environmental sensor in Kentron publishes elevated `air_quality`.  
2. **Network:** MQTT delivers the message to topic `smartcity/sensors` (or a future district topic).  
3. **Edge/Fog:** the validator accepts the schema; the preprocessor marks the value above a local threshold.  
4. **Data Platform:** the event is ingested (Kafka target) and stored for history.  
5. **AI/Analytics:** anomaly detection compares against the district baseline and confirms an anomaly.  
6. **Application:** Alert UI / monitoring dashboard shows “Abnormal air pollution — Kentron”.  
7. **Security:** only an authenticated publisher could write; only an authorized operator can view/ack the alert; transport is protected by TLS in the target design.

This scenario shows why all layers are needed, not only a sensor→dashboard shortcut.

---

## 10. Limitations and Future Improvements

### Limitations

1. This document describes a **conceptual** architecture; the full platform is not implemented.  
2. Traffic sensors, Kafka, ML anomaly service, admin UI, and TLS/auth remain Planned.  
3. The existing MQTT demo uses a localhost anonymous broker — not a city production profile.  
4. Digital Twin is listed as optional inspiration, not a mandatory runtime dependency.  
5. No claim is made that a completed security audit or penetration test was performed.

### Future improvements

1. Harden MQTT (auth, ACL, TLS) on the demo path.  
2. Introduce Kafka ingestion beside/instead of direct SQLite writes.  
3. Add fog workers for filtering and local thresholding.  
4. Implement an anomaly detection service and alert UI.  
5. Add a traffic sensor stream and a unified district ontology.  
6. Formalize Zero Trust policies across layers.

---

## Appendix A. Mapping from repository branches

| Branch / artifact | Role in this architecture document |
|---|---|
| `master` MQTT monitoring | Existing baseline for IoT/Network/Edge-lite/Data-lite/App |
| `kafka-pipeline` | Inspiration for Data Platform ingestion |
| `digital-twin` | Inspiration for Analytics/twin presentation |
| `security-risk-assessment` | Inspiration for Security Layer thinking |
| `architecture.mmd` / `.svg` / `.png` | Diagram deliverables for Assignment №1 |

## Appendix B. How to view the diagram

```bash
cd /home/lyudmila/Desktop/tt
xdg-open architecture.png
# or
xdg-open architecture.svg
# or open architecture.mmd in any Mermaid-compatible viewer
```
