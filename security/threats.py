"""Structured Threat Model for the Smart City MQTT IoT monitoring system.

This module documents assets, entry points, trust boundaries, and threats
based on a static review of the repository (Stage 1). It does not perform
penetration testing or active exploitation.

Evidence labels used in fields:
- confirmed: observed in project source or configuration files
- unverified: plausible, but not dynamically verified in this assessment
- hypothetical: illustrative attack scenario for teaching / modelling
- none_verified: no matching control found in the reviewed files
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProtectedAsset:
    """Something the Smart City system needs to protect."""

    asset_id: str
    name: str
    description: str
    data_classification: str
    related_components: tuple[str, ...]


@dataclass(frozen=True)
class EntryPoint:
    """A place where an actor can interact with the system."""

    entry_id: str
    name: str
    component: str
    interface: str
    notes: str


@dataclass(frozen=True)
class TrustBoundary:
    """A boundary where trust assumptions change."""

    boundary_id: str
    name: str
    from_zone: str
    to_zone: str
    description: str


@dataclass(frozen=True)
class Threat:
    """One modelled threat against the IoT architecture."""

    threat_id: str
    name: str
    affected_component: str
    description: str
    attack_scenario: str
    attack_scenario_type: str  # hypothetical | based_on_confirmed_config
    potential_consequences: str
    existing_controls: tuple[str, ...]
    existing_controls_status: str  # confirmed | unverified | none_verified
    recommended_mitigations: tuple[str, ...]
    related_assets: tuple[str, ...] = field(default_factory=tuple)
    related_entry_points: tuple[str, ...] = field(default_factory=tuple)
    stride_categories: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Architecture context derived from Stage 1 static review
# ---------------------------------------------------------------------------

PROTECTED_ASSETS: tuple[ProtectedAsset, ...] = (
    ProtectedAsset(
        asset_id="A-01",
        name="Sensor telemetry integrity",
        description=(
            "Environmental readings (temperature, humidity, air_quality) "
            "published on topic smartcity/sensors and stored in SQLite."
        ),
        data_classification="operational / integrity-sensitive",
        related_components=(
            "sensor_simulator",
            "mqtt_publisher",
            "mosquitto",
            "mqtt_subscriber",
            "sqlite",
        ),
    ),
    ProtectedAsset(
        asset_id="A-02",
        name="MQTT broker availability",
        description="Local Mosquitto process listening on port 1883.",
        data_classification="availability-critical (demo)",
        related_components=("mosquitto",),
    ),
    ProtectedAsset(
        asset_id="A-03",
        name="SQLite database file",
        description="File data/smartcity.db with table sensor_readings.",
        data_classification="confidentiality + integrity + availability",
        related_components=("sqlite", "subscriber", "dashboard"),
    ),
    ProtectedAsset(
        asset_id="A-04",
        name="Streamlit monitoring dashboard",
        description="UI at localhost:8501 that visualises stored readings.",
        data_classification="confidentiality + availability",
        related_components=("dashboard",),
    ),
    ProtectedAsset(
        asset_id="A-05",
        name="Trust in virtual IoT sensors",
        description=(
            "Assumption that readings originate from the project simulator "
            "rather than an arbitrary MQTT publisher."
        ),
        data_classification="integrity / authenticity",
        related_components=("sensor_simulator", "mqtt_publisher", "mosquitto"),
    ),
)


ENTRY_POINTS: tuple[EntryPoint, ...] = (
    EntryPoint(
        entry_id="E-01",
        name="MQTT broker TCP listener",
        component="mosquitto",
        interface="TCP localhost:1883 (configured listener 1883)",
        notes=(
            "Confirmed: tools/mosquitto/mosquitto.conf enables anonymous access. "
            "Whether the OS binds only to loopback was not dynamically verified."
        ),
    ),
    EntryPoint(
        entry_id="E-02",
        name="MQTT topic smartcity/sensors",
        component="mosquitto / publisher / subscriber",
        interface="MQTT publish/subscribe",
        notes="Any client that can reach the broker can publish or subscribe if auth remains disabled.",
    ),
    EntryPoint(
        entry_id="E-03",
        name="SQLite database file path",
        component="sqlite",
        interface="Filesystem path data/smartcity.db",
        notes="Confirmed: dashboard and subscriber open the file directly; no DB password.",
    ),
    EntryPoint(
        entry_id="E-04",
        name="Streamlit HTTP UI",
        component="dashboard",
        interface="HTTP localhost:8501",
        notes="Confirmed: dashboard/app.py has no authentication code.",
    ),
    EntryPoint(
        entry_id="E-05",
        name="Local process / CLI controls",
        component="publisher / subscriber / start scripts",
        interface="Local shell / Python processes",
        notes="Operator can start/stop components; host compromise is out of deep scope but relevant.",
    ),
)


TRUST_BOUNDARIES: tuple[TrustBoundary, ...] = (
    TrustBoundary(
        boundary_id="B-01",
        name="Host network ↔ MQTT broker",
        from_zone="unauthenticated network clients",
        to_zone="Mosquitto broker process",
        description=(
            "Crossing this boundary currently requires only network reachability "
            "because allow_anonymous true is confirmed in mosquitto.conf."
        ),
    ),
    TrustBoundary(
        boundary_id="B-02",
        name="MQTT messages ↔ Subscriber validation",
        from_zone="any MQTT publisher on the topic",
        to_zone="validated readings accepted by subscriber",
        description=(
            "message_validator.py checks JSON schema/types (confirmed control) "
            "but does not authenticate the publisher identity."
        ),
    ),
    TrustBoundary(
        boundary_id="B-03",
        name="Subscriber process ↔ SQLite file",
        from_zone="application process",
        to_zone="persistent database file",
        description="OS file permissions are the main barrier; not verified dynamically in Stage 1.",
    ),
    TrustBoundary(
        boundary_id="B-04",
        name="Browser user ↔ Streamlit dashboard",
        from_zone="HTTP client",
        to_zone="monitoring UI and DB read path",
        description="No application-level authentication was found in dashboard/app.py.",
    ),
)


# ---------------------------------------------------------------------------
# Threat catalog (minimum set required by the assignment)
# ---------------------------------------------------------------------------

THREAT_CATALOG: tuple[Threat, ...] = (
    Threat(
        threat_id="T-01",
        name="Unauthorized MQTT broker access",
        affected_component="Mosquitto broker (tools/mosquitto)",
        description=(
            "An actor connects to the MQTT broker and publishes or subscribes "
            "without credentials."
        ),
        attack_scenario=(
            "HYPOTHETICAL scenario grounded in CONFIRMED config: "
            "mosquitto.conf sets allow_anonymous true and listens on 1883. "
            "If a client can reach that port, it can connect without a password "
            "and interact with topic smartcity/sensors."
        ),
        attack_scenario_type="based_on_confirmed_config",
        potential_consequences=(
            "Loss of confidentiality of live telemetry; injection of false "
            "readings; disruption of legitimate publishers/subscribers."
        ),
        existing_controls=(
            "Default host in clients is localhost (reduces remote exposure in the default demo).",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Enable MQTT username/password authentication",
            "Configure Mosquitto ACLs per client/topic",
            "Bind broker to loopback or place behind network filtering",
            "Disable anonymous access (allow_anonymous false)",
        ),
        related_assets=("A-01", "A-02", "A-05"),
        related_entry_points=("E-01", "E-02"),
        stride_categories=("Spoofing", "Information Disclosure", "Elevation of Privilege"),
    ),
    Threat(
        threat_id="T-02",
        name="Sensor data spoofing",
        affected_component="MQTT topic smartcity/sensors / subscriber / SQLite",
        description=(
            "An actor publishes syntactically valid sensor JSON that does not "
            "come from the legitimate simulator."
        ),
        attack_scenario=(
            "HYPOTHETICAL: after connecting to the anonymous broker, an attacker "
            "publishes JSON with required fields (sensor_id, location, timestamp, "
            "temperature, humidity, air_quality). The subscriber validator accepts "
            "structurally valid messages and stores them."
        ),
        attack_scenario_type="hypothetical",
        potential_consequences=(
            "Operators make decisions on falsified environmental data; "
            "pollution of historical charts and analytics."
        ),
        existing_controls=(
            "message_validator.py enforces required fields and numeric types (confirmed).",
            "No publisher authentication or message signing was found (confirmed absence).",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Authenticate publishers and restrict publish ACL to known client IDs",
            "Add device identity / HMAC or signed payloads where feasible",
            "Monitor for unexpected sensor_id or location values",
            "Separate demo credentials from any production deployment",
        ),
        related_assets=("A-01", "A-05"),
        related_entry_points=("E-02",),
        stride_categories=("Spoofing", "Tampering"),
    ),
    Threat(
        threat_id="T-03",
        name="MQTT message interception",
        affected_component="MQTT transport (publisher ↔ broker ↔ subscriber)",
        description=(
            "An on-path observer reads plaintext MQTT payloads in transit."
        ),
        attack_scenario=(
            "HYPOTHETICAL: if MQTT traffic leaves a trusted host segment without TLS, "
            "a network sniffer on the path could observe JSON telemetry. "
            "In the default localhost demo the practical risk is lower, but the "
            "reviewed mosquitto.conf does not enable TLS listeners."
        ),
        attack_scenario_type="hypothetical",
        potential_consequences=(
            "Disclosure of environmental readings and operational patterns; "
            "information useful for later spoofing."
        ),
        existing_controls=(
            "Default demo uses localhost endpoints (confirmed in client defaults).",
            "No TLS configuration in tools/mosquitto/mosquitto.conf (confirmed absence).",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Enable MQTT over TLS",
            "Keep broker off untrusted networks",
            "Use network segmentation for IoT traffic",
            "Manage certificates/credentials outside source code",
        ),
        related_assets=("A-01",),
        related_entry_points=("E-01", "E-02"),
        stride_categories=("Information Disclosure",),
    ),
    Threat(
        threat_id="T-04",
        name="DDoS against the MQTT broker",
        affected_component="Mosquitto broker availability",
        description=(
            "An actor floods the broker with connections or publish traffic "
            "to degrade or deny service."
        ),
        attack_scenario=(
            "HYPOTHETICAL: many anonymous clients connect to port 1883 and "
            "publish high-rate messages. Without connection limits or auth, "
            "broker CPU/memory or subscriber processing may be exhausted."
        ),
        attack_scenario_type="hypothetical",
        potential_consequences=(
            "Loss of live monitoring; delayed or missing database updates; "
            "demo / operational outage."
        ),
        existing_controls=(
            "Local educational deployment reduces internet exposure by default.",
            "No connection_limit / rate-limiting settings found in the project mosquitto.conf "
            "(confirmed absence in reviewed file).",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Configure Mosquitto connection limits where supported",
            "Apply host firewall / rate filtering",
            "Require authentication before accept",
            "Monitor broker logs and resource usage",
        ),
        related_assets=("A-02", "A-01"),
        related_entry_points=("E-01",),
        stride_categories=("Denial of Service",),
    ),
    Threat(
        threat_id="T-05",
        name="Unauthorized database access",
        affected_component="SQLite file data/smartcity.db",
        description=(
            "An actor with filesystem access opens or copies the SQLite database "
            "outside the intended subscriber/dashboard processes."
        ),
        attack_scenario=(
            "HYPOTHETICAL: a local user or malware reads data/smartcity.db directly. "
            "Confirmed: SQLite is a local file without application-level DB credentials; "
            "OS permission hardening was not verified in this assessment."
        ),
        attack_scenario_type="hypothetical",
        potential_consequences=(
            "Confidentiality loss of historical readings; offline tampering "
            "if write access is available."
        ),
        existing_controls=(
            "*.db is listed in .gitignore (reduces accidental git leakage) — confirmed.",
            "SQL statements use parameterized queries (reduces injection risk) — confirmed.",
            "File permission lockdown — unverified.",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Restrict OS permissions on data/ to the service account",
            "Run components with least privilege",
            "Encrypt backups and limit who can copy the DB file",
            "Keep the database path off shared/world-readable directories",
        ),
        related_assets=("A-03",),
        related_entry_points=("E-03", "E-05"),
        stride_categories=("Information Disclosure", "Tampering"),
    ),
    Threat(
        threat_id="T-06",
        name="Data theft",
        affected_component="MQTT path, SQLite storage, Streamlit UI",
        description=(
            "Sensitive operational telemetry is exfiltrated through any readable "
            "channel: MQTT subscribe, DB file copy, or dashboard access."
        ),
        attack_scenario=(
            "HYPOTHETICAL composite scenario: an unauthorized MQTT subscriber "
            "listens to smartcity/sensors, or an unauthorized browser session "
            "opens the Streamlit UI, or the DB file is copied from disk."
        ),
        attack_scenario_type="hypothetical",
        potential_consequences=(
            "Loss of confidentiality; potential misuse of city environmental data; "
            "reputational / academic integrity impact for a production-like deployment."
        ),
        existing_controls=(
            "No TLS and anonymous MQTT confirmed in broker config.",
            "No dashboard authentication found in dashboard/app.py.",
            "Default localhost deployment reduces remote exposure for the classroom demo.",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Encrypt data in transit (MQTT TLS) and restrict subscribers via ACL",
            "Add dashboard authentication / reverse-proxy access control",
            "Protect database files and backups",
            "Log and alert on unexpected clients or UI access patterns",
        ),
        related_assets=("A-01", "A-03", "A-04"),
        related_entry_points=("E-01", "E-02", "E-03", "E-04"),
        stride_categories=("Information Disclosure",),
    ),
    Threat(
        threat_id="T-07",
        name="Ransomware affecting application data",
        affected_component="SQLite database and host filesystem",
        description=(
            "Malware encrypts or deletes application data files, including "
            "smartcity.db, disrupting monitoring continuity."
        ),
        attack_scenario=(
            "HYPOTHETICAL / out-of-band host threat: ransomware on the lab machine "
            "encrypts files under data/. This assessment did not observe ransomware "
            "controls in the application code; recovery depends on host backups."
        ),
        attack_scenario_type="hypothetical",
        potential_consequences=(
            "Loss of historical sensor data; dashboard outage; recovery time and cost."
        ),
        existing_controls=(
            "No application-level backup/restore automation found in reviewed project files.",
            "Database file is local and replaceable for a demo, but durable backups are unverified.",
        ),
        existing_controls_status="none_verified",
        recommended_mitigations=(
            "Maintain offline or immutable backups of data/smartcity.db",
            "Restrict write access to the data directory",
            "Keep OS and Python dependencies updated",
            "Document and rehearse recovery procedures",
        ),
        related_assets=("A-03", "A-04"),
        related_entry_points=("E-03", "E-05"),
        stride_categories=("Denial of Service", "Tampering"),
    ),
    Threat(
        threat_id="T-08",
        name="Unauthorized dashboard access",
        affected_component="Streamlit dashboard (dashboard/app.py)",
        description=(
            "An actor opens the monitoring UI and views live/historical readings "
            "without authenticating."
        ),
        attack_scenario=(
            "HYPOTHETICAL scenario grounded in CONFIRMED code review: "
            "dashboard/app.py contains no login flow. If port 8501 is reachable, "
            "a browser can load environmental charts and tables."
        ),
        attack_scenario_type="based_on_confirmed_config",
        potential_consequences=(
            "Confidentiality loss of monitoring data; information gathering "
            "for further attacks."
        ),
        existing_controls=(
            "Default Streamlit bind for the demo is local (start_demo.sh uses localhost URL).",
            "No application authentication implemented (confirmed absence).",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Add authentication (Streamlit auth, SSO, or reverse proxy basic/OIDC auth)",
            "Bind Streamlit to localhost and require SSH tunnel / VPN for remote use",
            "Place the UI behind an access-controlled reverse proxy",
            "Avoid exposing port 8501 to untrusted networks",
        ),
        related_assets=("A-04", "A-01"),
        related_entry_points=("E-04",),
        stride_categories=("Information Disclosure", "Elevation of Privilege"),
    ),
    Threat(
        threat_id="T-09",
        name="Malicious or malformed sensor messages",
        affected_component="MQTT subscriber / validator / database path",
        description=(
            "An actor sends malformed JSON or unexpected values to disrupt "
            "parsing, flood logs, or probe for weak validation."
        ),
        attack_scenario=(
            "HYPOTHETICAL: publish non-JSON blobs, missing fields, or wrong types "
            "to topic smartcity/sensors. Confirmed control: subscriber catches "
            "JSONDecodeError and InvalidSensorMessage and increments invalid_count "
            "without writing those payloads to SQLite."
        ),
        attack_scenario_type="based_on_confirmed_config",
        potential_consequences=(
            "Log noise; wasted CPU; if validation were weaker, risk of bad rows "
            "or application exceptions. Residual risk remains for valid-but-false data (T-02)."
        ),
        existing_controls=(
            "message_validator.py rejects missing fields and non-numeric metrics (confirmed).",
            "mqtt_subscriber.py ignores invalid payloads and continues running (confirmed).",
            "Parameterized SQL insert reduces injection impact of string fields (confirmed).",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "Keep and extend schema validation (ranges, allowed sensor_id set)",
            "Rate-limit accepts per client after authentication",
            "Alert when invalid_count rises abnormally",
            "Still authenticate publishers so only trusted devices can send traffic",
        ),
        related_assets=("A-01", "A-02"),
        related_entry_points=("E-02",),
        stride_categories=("Tampering", "Denial of Service"),
    ),
    Threat(
        threat_id="T-10",
        name="IoT device or sensor compromise",
        affected_component="Virtual sensors / publisher identity (educational stand-in for field devices)",
        description=(
            "Compromise of a sensor endpoint or its publishing credentials would "
            "allow continuous injection of attacker-controlled telemetry."
        ),
        attack_scenario=(
            "HYPOTHETICAL teaching scenario: in a real Smart City deployment, "
            "a physical/firmware-compromised sensor publishes forged values. "
            "In this repository, sensors are a Python simulator without device "
            "attestation; the closest analogue is takeover of the publisher process "
            "or reuse of an open anonymous MQTT publish path."
        ),
        attack_scenario_type="hypothetical",
        potential_consequences=(
            "Long-term integrity loss; misleading city environmental situational awareness."
        ),
        existing_controls=(
            "Project uses a virtual simulator, not physical IoT firmware (confirmed architecture).",
            "No device mutual authentication found in publisher code (confirmed absence).",
        ),
        existing_controls_status="confirmed",
        recommended_mitigations=(
            "In real deployments: harden device firmware and unique per-device credentials",
            "Use mutual TLS or token-based device auth to the broker",
            "Monitor behavioural anomalies per sensor_id",
            "Apply secure update and inventory management for field devices",
        ),
        related_assets=("A-05", "A-01"),
        related_entry_points=("E-02", "E-05"),
        stride_categories=("Spoofing", "Tampering", "Repudiation"),
    ),
)


def list_protected_assets() -> tuple[ProtectedAsset, ...]:
    return PROTECTED_ASSETS


def list_entry_points() -> tuple[EntryPoint, ...]:
    return ENTRY_POINTS


def list_trust_boundaries() -> tuple[TrustBoundary, ...]:
    return TRUST_BOUNDARIES


def list_threats() -> tuple[Threat, ...]:
    return THREAT_CATALOG


def get_threat_by_id(threat_id: str) -> Threat:
    for threat in THREAT_CATALOG:
        if threat.threat_id == threat_id:
            return threat
    raise KeyError(f"Unknown threat_id: {threat_id}")


def threats_as_dicts() -> list[dict[str, Any]]:
    return [threat.to_dict() for threat in THREAT_CATALOG]
