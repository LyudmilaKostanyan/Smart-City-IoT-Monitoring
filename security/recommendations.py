"""Security recommendations mapped to Smart City IoT threats.

Distinguishes:
- existing controls observed during Stage 1 static review
- proposed controls that are NOT claimed as already implemented

Recommendations are defensive guidance only. This module does not change
Mosquitto authentication, firewall rules, or any live security configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .threats import THREAT_CATALOG, Threat, get_threat_by_id


@dataclass(frozen=True)
class SecurityControl:
    """One security control (existing or proposed)."""

    control_id: str
    title: str
    description: str
    status: str  # existing_confirmed | existing_partial | proposed
    reduces: tuple[str, ...]  # probability | impact | both
    how_it_helps: str
    applies_to_threats: tuple[str, ...]
    architecture_fit: str


@dataclass(frozen=True)
class ThreatRecommendationPack:
    """Existing + proposed controls for a single threat."""

    threat_id: str
    threat_name: str
    existing_controls: tuple[SecurityControl, ...]
    proposed_controls: tuple[SecurityControl, ...]
    residual_notes: str

    @property
    def all_controls(self) -> tuple[SecurityControl, ...]:
        return self.existing_controls + self.proposed_controls


# ---------------------------------------------------------------------------
# Shared control catalogue (referenced by multiple threats where appropriate)
# ---------------------------------------------------------------------------

CONTROL_CATALOG: dict[str, SecurityControl] = {
    "C-EXIST-01": SecurityControl(
        control_id="C-EXIST-01",
        title="Default localhost MQTT endpoints",
        description=(
            "Publisher and subscriber default to host=localhost, port=1883, "
            "which reduces accidental remote exposure in the classroom demo."
        ),
        status="existing_confirmed",
        reduces=("probability",),
        how_it_helps=(
            "Lowers the chance that arbitrary internet hosts reach the broker "
            "when operators keep defaults. It does not replace authentication."
        ),
        applies_to_threats=("T-01", "T-03", "T-04", "T-06"),
        architecture_fit="Matches current paho-mqtt client defaults in this repo.",
    ),
    "C-EXIST-02": SecurityControl(
        control_id="C-EXIST-02",
        title="Sensor message schema validation",
        description=(
            "subscriber/message_validator.py requires expected fields and numeric "
            "metric types before SQLite insert."
        ),
        status="existing_confirmed",
        reduces=("impact",),
        how_it_helps=(
            "Malformed or incomplete payloads are rejected, reducing corruption "
            "and some classes of bad data. It does not stop schema-valid spoofing."
        ),
        applies_to_threats=("T-02", "T-09"),
        architecture_fit="Already wired into MqttSubscriber._on_message.",
    ),
    "C-EXIST-03": SecurityControl(
        control_id="C-EXIST-03",
        title="Parameterized SQLite queries",
        description=(
            "database/db.py uses placeholders (?) for inserts and filtered selects."
        ),
        status="existing_confirmed",
        reduces=("impact",),
        how_it_helps=(
            "Reduces SQL injection impact if unexpected strings reach persistence."
        ),
        applies_to_threats=("T-05", "T-09"),
        architecture_fit="Fits the current SensorDatabase implementation.",
    ),
    "C-EXIST-04": SecurityControl(
        control_id="C-EXIST-04",
        title="Database files ignored by Git",
        description="*.db is listed in .gitignore, reducing accidental commit of local DB files.",
        status="existing_confirmed",
        reduces=("probability",),
        how_it_helps=(
            "Lowers likelihood of leaking sensor history through the Git remote. "
            "Does not protect the local filesystem copy."
        ),
        applies_to_threats=("T-05", "T-06"),
        architecture_fit="Repository hygiene control only.",
    ),
    "C-EXIST-05": SecurityControl(
        control_id="C-EXIST-05",
        title="Invalid MQTT payloads are ignored",
        description=(
            "mqtt_subscriber.py catches JSON/validation errors, increments "
            "invalid_count, and continues without writing bad rows."
        ),
        status="existing_confirmed",
        reduces=("impact",),
        how_it_helps=(
            "Improves resilience against malformed message floods aimed at parser crashes."
        ),
        applies_to_threats=("T-09",),
        architecture_fit="Confirmed in subscriber message handler.",
    ),
    "C-PROP-01": SecurityControl(
        control_id="C-PROP-01",
        title="Disable anonymous MQTT and require authentication",
        description=(
            "Set allow_anonymous false and configure a password file / dynamic security. "
            "Do not apply automatically in this assignment branch without approval."
        ),
        status="proposed",
        reduces=("probability",),
        how_it_helps=(
            "Blocks unauthenticated connect attempts, directly addressing T-01 and "
            "raising the bar for spoofing, theft, and broker abuse."
        ),
        applies_to_threats=("T-01", "T-02", "T-04", "T-06", "T-09", "T-10"),
        architecture_fit="Compatible with bundled Mosquitto under tools/mosquitto/.",
    ),
    "C-PROP-02": SecurityControl(
        control_id="C-PROP-02",
        title="MQTT topic ACLs",
        description=(
            "Allow only the publisher client to write smartcity/sensors and only "
            "the subscriber (and maybe dashboard tooling) to read it."
        ),
        status="proposed",
        reduces=("probability",),
        how_it_helps=(
            "Limits who can inject or exfiltrate telemetry even after authentication exists."
        ),
        applies_to_threats=("T-01", "T-02", "T-06", "T-10"),
        architecture_fit="Mosquitto ACL files are supported by the bundled broker package.",
    ),
    "C-PROP-03": SecurityControl(
        control_id="C-PROP-03",
        title="MQTT over TLS",
        description=(
            "Terminate MQTT with certificates so payloads are not plaintext on the wire."
        ),
        status="proposed",
        reduces=("probability", "impact"),
        how_it_helps=(
            "Makes passive interception much harder and supports stronger client auth patterns."
        ),
        applies_to_threats=("T-03", "T-06"),
        architecture_fit=(
            "Not configured in tools/mosquitto/mosquitto.conf today; would require certs "
            "and client TLS settings in publisher/subscriber."
        ),
    ),
    "C-PROP-04": SecurityControl(
        control_id="C-PROP-04",
        title="Network filtering and broker exposure limits",
        description=(
            "Keep listener on loopback and/or firewall port 1883; avoid publishing "
            "the broker to untrusted networks."
        ),
        status="proposed",
        reduces=("probability",),
        how_it_helps=(
            "Shrinks the remote attack surface for unauthorized access and DDoS."
        ),
        applies_to_threats=("T-01", "T-03", "T-04", "T-06", "T-08"),
        architecture_fit="Complements localhost defaults; OS firewall was not verified.",
    ),
    "C-PROP-05": SecurityControl(
        control_id="C-PROP-05",
        title="Connection limits / rate controls",
        description=(
            "Use Mosquitto connection limits and host-level rate filtering where available."
        ),
        status="proposed",
        reduces=("impact", "probability"),
        how_it_helps=(
            "Reduces the chance that connection/publish floods exhaust broker resources."
        ),
        applies_to_threats=("T-04", "T-09"),
        architecture_fit="No such limits found in the reviewed project mosquitto.conf.",
    ),
    "C-PROP-06": SecurityControl(
        control_id="C-PROP-06",
        title="Restrict SQLite file permissions and least privilege",
        description=(
            "Make data/smartcity.db readable/writable only by the service account "
            "running subscriber/dashboard."
        ),
        status="proposed",
        reduces=("probability",),
        how_it_helps=(
            "Hardens unauthorized local DB reads/writes beyond application code controls."
        ),
        applies_to_threats=("T-05", "T-06", "T-07"),
        architecture_fit="Fits local-file SQLite architecture used by database/db.py.",
    ),
    "C-PROP-07": SecurityControl(
        control_id="C-PROP-07",
        title="Protected backups and recovery procedure",
        description=(
            "Keep offline/immutable copies of smartcity.db and document restore steps."
        ),
        status="proposed",
        reduces=("impact",),
        how_it_helps=(
            "Does not stop ransomware infection, but reduces downtime and data-loss impact."
        ),
        applies_to_threats=("T-05", "T-07"),
        architecture_fit="No backup automation found in the current repository.",
    ),
    "C-PROP-08": SecurityControl(
        control_id="C-PROP-08",
        title="Dashboard authentication / reverse-proxy access control",
        description=(
            "Put Streamlit behind auth (app auth, OIDC, or reverse-proxy basic/SSO) "
            "and avoid exposing :8501 publicly."
        ),
        status="proposed",
        reduces=("probability",),
        how_it_helps=(
            "Prevents anonymous viewing of monitoring data through the UI."
        ),
        applies_to_threats=("T-08", "T-06"),
        architecture_fit="dashboard/app.py currently has no login flow.",
    ),
    "C-PROP-09": SecurityControl(
        control_id="C-PROP-09",
        title="Stronger semantic validation and anomaly monitoring",
        description=(
            "Allow-list sensor_id/location values, enforce metric ranges, and alert "
            "on rising invalid_count or impossible readings."
        ),
        status="proposed",
        reduces=("impact", "probability"),
        how_it_helps=(
            "Extends existing schema checks toward spoof/anomaly detection without claiming "
            "cryptographic authenticity by itself."
        ),
        applies_to_threats=("T-02", "T-09", "T-10"),
        architecture_fit="Natural extension of message_validator.py.",
    ),
    "C-PROP-10": SecurityControl(
        control_id="C-PROP-10",
        title="Per-device credentials and secure publisher identity",
        description=(
            "In real IoT deployments use unique device credentials / mutual TLS; "
            "in this lab, protect the publisher process and its secrets."
        ),
        status="proposed",
        reduces=("probability",),
        how_it_helps=(
            "Makes sensor compromise or publisher impersonation harder to sustain."
        ),
        applies_to_threats=("T-02", "T-10"),
        architecture_fit=(
            "Educational simulator has no field firmware; recommendation is architecture-aware."
        ),
    ),
    "C-PROP-11": SecurityControl(
        control_id="C-PROP-11",
        title="Dependency and host patch management",
        description=(
            "Keep OS packages and Python dependencies updated; limit local admin access."
        ),
        status="proposed",
        reduces=("probability",),
        how_it_helps=(
            "Reduces likelihood of host compromise paths that enable ransomware or data theft."
        ),
        applies_to_threats=("T-07", "T-05", "T-06"),
        architecture_fit="Applies to the lab host running Mosquitto, Python, and Streamlit.",
    ),
}


# Explicit mapping: threat_id -> (existing control ids, proposed control ids, residual note)
_THREAT_CONTROL_MAP: dict[str, tuple[tuple[str, ...], tuple[str, ...], str]] = {
    "T-01": (
        ("C-EXIST-01",),
        ("C-PROP-01", "C-PROP-02", "C-PROP-04"),
        "Localhost defaults help, but anonymous access remains a confirmed weak point.",
    ),
    "T-02": (
        ("C-EXIST-02",),
        ("C-PROP-01", "C-PROP-02", "C-PROP-09", "C-PROP-10"),
        "Schema validation is necessary but not sufficient against authentic-looking fakes.",
    ),
    "T-03": (
        ("C-EXIST-01",),
        ("C-PROP-03", "C-PROP-04"),
        "Interception risk stays low on pure localhost, higher if MQTT leaves the host.",
    ),
    "T-04": (
        ("C-EXIST-01",),
        ("C-PROP-01", "C-PROP-04", "C-PROP-05"),
        "Availability protections are mostly absent in the reviewed broker config.",
    ),
    "T-05": (
        ("C-EXIST-03", "C-EXIST-04"),
        ("C-PROP-06", "C-PROP-07", "C-PROP-11"),
        "Parameterized SQL helps injection safety; file confidentiality still depends on OS ACLs.",
    ),
    "T-06": (
        ("C-EXIST-01", "C-EXIST-04"),
        ("C-PROP-01", "C-PROP-02", "C-PROP-03", "C-PROP-04", "C-PROP-06", "C-PROP-08"),
        "Data theft is a multi-channel threat; one control alone is incomplete.",
    ),
    "T-07": (
        (),
        ("C-PROP-06", "C-PROP-07", "C-PROP-11"),
        "No application-level backup/restore control was verified in the repository.",
    ),
    "T-08": (
        (),
        ("C-PROP-08", "C-PROP-04"),
        "No dashboard authentication was found; localhost binding alone is not app auth.",
    ),
    "T-09": (
        ("C-EXIST-02", "C-EXIST-03", "C-EXIST-05"),
        ("C-PROP-05", "C-PROP-09", "C-PROP-01"),
        "Existing validation already lowers impact; residual issue is authenticated abuse volume.",
    ),
    "T-10": (
        (),
        ("C-PROP-01", "C-PROP-02", "C-PROP-09", "C-PROP-10"),
        "Virtual simulator context: treat this as a Smart City teaching analogue, not firmware audit.",
    ),
}


def _controls_from_ids(control_ids: Iterable[str]) -> tuple[SecurityControl, ...]:
    controls: list[SecurityControl] = []
    for control_id in control_ids:
        try:
            controls.append(CONTROL_CATALOG[control_id])
        except KeyError as exc:
            raise KeyError(f"Unknown control_id: {control_id}") from exc
    return tuple(controls)


def _validate_map_against_catalog() -> None:
    threat_ids = {threat.threat_id for threat in THREAT_CATALOG}
    mapped_ids = set(_THREAT_CONTROL_MAP)
    if threat_ids != mapped_ids:
        raise RuntimeError(
            "Recommendation map out of sync with THREAT_CATALOG: "
            f"missing={sorted(threat_ids - mapped_ids)} "
            f"extra={sorted(mapped_ids - threat_ids)}"
        )

    for threat_id, (existing_ids, proposed_ids, _note) in _THREAT_CONTROL_MAP.items():
        for control_id in existing_ids + proposed_ids:
            control = CONTROL_CATALOG[control_id]
            if threat_id not in control.applies_to_threats:
                raise RuntimeError(
                    f"{control_id} mapped to {threat_id} but applies_to_threats="
                    f"{control.applies_to_threats}"
                )
            if control_id.startswith("C-EXIST") and not control.status.startswith("existing"):
                raise RuntimeError(f"{control_id} must have existing* status")
            if control_id.startswith("C-PROP") and control.status != "proposed":
                raise RuntimeError(f"{control_id} must have proposed status")


_validate_map_against_catalog()


def list_controls() -> tuple[SecurityControl, ...]:
    return tuple(CONTROL_CATALOG[key] for key in sorted(CONTROL_CATALOG))


def get_control(control_id: str) -> SecurityControl:
    try:
        return CONTROL_CATALOG[control_id]
    except KeyError as exc:
        raise KeyError(f"Unknown control_id: {control_id}") from exc


def get_recommendations_for_threat(threat_id: str) -> ThreatRecommendationPack:
    threat = get_threat_by_id(threat_id)
    existing_ids, proposed_ids, residual = _THREAT_CONTROL_MAP[threat_id]
    return ThreatRecommendationPack(
        threat_id=threat.threat_id,
        threat_name=threat.name,
        existing_controls=_controls_from_ids(existing_ids),
        proposed_controls=_controls_from_ids(proposed_ids),
        residual_notes=residual,
    )


def list_recommendation_packs() -> list[ThreatRecommendationPack]:
    return [get_recommendations_for_threat(threat.threat_id) for threat in THREAT_CATALOG]


def recommendations_as_table_rows() -> list[dict[str, str]]:
    """Flat rows useful for Streamlit tables / Markdown export."""
    rows: list[dict[str, str]] = []
    for pack in list_recommendation_packs():
        for control in pack.all_controls:
            rows.append(
                {
                    "threat_id": pack.threat_id,
                    "threat_name": pack.threat_name,
                    "control_id": control.control_id,
                    "title": control.title,
                    "status": control.status,
                    "reduces": ", ".join(control.reduces),
                    "how_it_helps": control.how_it_helps,
                }
            )
    return rows


def assert_threat_mitigations_covered(threat: Threat) -> None:
    """Ensure each free-text mitigation in Threat still maps to a proposed control theme.

    This is a lightweight consistency check for teaching integrity, not a NLP matcher.
    """
    pack = get_recommendations_for_threat(threat.threat_id)
    if not pack.proposed_controls and threat.recommended_mitigations:
        raise AssertionError(
            f"{threat.threat_id} has textual mitigations but no proposed controls"
        )
