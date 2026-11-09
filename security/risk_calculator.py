"""Risk assessment engine for Smart City IoT threat model.

Demonstration formula (not an official cybersecurity standard):

    Risk Score = Probability × Impact

Probability and Impact are integers in [1, 5].
Risk levels use configurable score thresholds (defaults: Low 1–7, Medium 8–14, High 15–25).

Initial scores in INITIAL_ASSESSMENTS are illustrative estimates based on the
Stage 1 static review. They are NOT measured from penetration testing.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Mapping

from .threats import THREAT_CATALOG, Threat, get_threat_by_id


MIN_FACTOR = 1
MAX_FACTOR = 5

PROBABILITY_LABELS: dict[int, str] = {
    1: "Rare",
    2: "Unlikely",
    3: "Possible",
    4: "Likely",
    5: "Very likely",
}

IMPACT_LABELS: dict[int, str] = {
    1: "Negligible",
    2: "Minor",
    3: "Moderate",
    4: "Major",
    5: "Critical",
}


@dataclass(frozen=True)
class RiskThresholds:
    """Inclusive score ranges for Low / Medium / High classification."""

    low_max: int = 7
    medium_max: int = 14
    high_max: int = 25

    def __post_init__(self) -> None:
        if self.low_max < 1:
            raise ValueError("low_max must be >= 1")
        if self.medium_max <= self.low_max:
            raise ValueError("medium_max must be greater than low_max")
        if self.high_max <= self.medium_max:
            raise ValueError("high_max must be greater than medium_max")
        if self.high_max > MAX_FACTOR * MAX_FACTOR:
            raise ValueError(
                f"high_max cannot exceed {MAX_FACTOR * MAX_FACTOR} "
                f"(maximum Probability × Impact)"
            )


DEFAULT_THRESHOLDS = RiskThresholds()


@dataclass(frozen=True)
class RiskAssessment:
    """Calculated risk for one threat."""

    threat_id: str
    threat_name: str
    affected_component: str
    probability: int
    impact: int
    risk_score: int
    risk_level: str
    probability_label: str
    impact_label: str
    rationale: str
    assessment_type: str  # illustrative_estimate | adjusted_by_user
    is_illustrative: bool = True

    @property
    def probability_display(self) -> str:
        return f"{self.probability} ({self.probability_label})"

    @property
    def impact_display(self) -> str:
        return f"{self.impact} ({self.impact_label})"


@dataclass(frozen=True)
class InitialRiskInput:
    """Starting Probability/Impact values with an explanation."""

    threat_id: str
    probability: int
    impact: int
    rationale: str
    assessment_type: str = "illustrative_estimate"


def validate_factor(value: int, name: str) -> int:
    """Validate a Probability or Impact factor (integer 1..5)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    if value < MIN_FACTOR or value > MAX_FACTOR:
        raise ValueError(
            f"{name} must be between {MIN_FACTOR} and {MAX_FACTOR}, got {value}"
        )
    return value


def calculate_risk_score(probability: int, impact: int) -> int:
    """Return Probability × Impact after validating both factors."""
    probability = validate_factor(probability, "probability")
    impact = validate_factor(impact, "impact")
    return probability * impact


def classify_risk_level(
    score: int,
    thresholds: RiskThresholds | None = None,
) -> str:
    """Classify a risk score into Low, Medium, or High."""
    thresholds = thresholds or DEFAULT_THRESHOLDS
    if not isinstance(score, int) or isinstance(score, bool):
        raise TypeError(f"score must be an int, got {type(score).__name__}")
    if score < 1 or score > thresholds.high_max:
        raise ValueError(
            f"score must be between 1 and {thresholds.high_max}, got {score}"
        )

    if score <= thresholds.low_max:
        return "Low"
    if score <= thresholds.medium_max:
        return "Medium"
    return "High"


def assess_threat(
    threat: Threat | str,
    probability: int,
    impact: int,
    *,
    rationale: str = "",
    assessment_type: str = "illustrative_estimate",
    thresholds: RiskThresholds | None = None,
) -> RiskAssessment:
    """Build a RiskAssessment for one threat."""
    if isinstance(threat, str):
        threat = get_threat_by_id(threat)

    score = calculate_risk_score(probability, impact)
    level = classify_risk_level(score, thresholds=thresholds)
    illustrative = assessment_type == "illustrative_estimate"

    return RiskAssessment(
        threat_id=threat.threat_id,
        threat_name=threat.name,
        affected_component=threat.affected_component,
        probability=probability,
        impact=impact,
        risk_score=score,
        risk_level=level,
        probability_label=PROBABILITY_LABELS[probability],
        impact_label=IMPACT_LABELS[impact],
        rationale=rationale,
        assessment_type=assessment_type,
        is_illustrative=illustrative,
    )


# ---------------------------------------------------------------------------
# Initial illustrative assessments (Stage 1 static review → teaching estimates)
# ---------------------------------------------------------------------------

INITIAL_ASSESSMENTS: tuple[InitialRiskInput, ...] = (
    InitialRiskInput(
        threat_id="T-01",
        probability=4,
        impact=4,
        rationale=(
            "Illustrative estimate: allow_anonymous true is confirmed, so any "
            "client that can reach the broker can connect without credentials. "
            "Probability=4 (Likely) for a shared lab host; Impact=4 (Major) "
            "because unauthorized publish/subscribe affects integrity and "
            "confidentiality of all topic traffic. Remote likelihood may be "
            "lower if the port is truly localhost-only (not dynamically verified)."
        ),
    ),
    InitialRiskInput(
        threat_id="T-02",
        probability=4,
        impact=4,
        rationale=(
            "Illustrative estimate: after anonymous MQTT access, publishing "
            "schema-valid JSON is straightforward. Validator checks structure, "
            "not publisher identity. Impact=4 because falsified city readings "
            "mislead the dashboard and stored history."
        ),
    ),
    InitialRiskInput(
        threat_id="T-03",
        probability=2,
        impact=3,
        rationale=(
            "Illustrative estimate: TLS is absent in mosquitto.conf (confirmed), "
            "but default clients use localhost, which lowers practical on-path "
            "sniffing. Probability=2 (Unlikely) for the default demo topology; "
            "Impact=3 (Moderate) if traffic ever crosses an untrusted segment."
        ),
    ),
    InitialRiskInput(
        threat_id="T-04",
        probability=2,
        impact=4,
        rationale=(
            "Illustrative estimate: no connection limits found in project "
            "mosquitto.conf, and anonymous clients are allowed. For a classroom "
            "localhost demo, mass flooding is Unlikely (2), but Impact=4 (Major) "
            "on broker/subscriber availability if it occurs."
        ),
    ),
    InitialRiskInput(
        threat_id="T-05",
        probability=3,
        impact=3,
        rationale=(
            "Illustrative estimate: SQLite is a local file without DB credentials "
            "(confirmed). Any OS user who can read data/smartcity.db can extract "
            "history. Probability=3 (Possible) on a shared machine; Impact=3 "
            "(Moderate) for educational telemetry. File permissions were not verified."
        ),
    ),
    InitialRiskInput(
        threat_id="T-06",
        probability=3,
        impact=4,
        rationale=(
            "Illustrative estimate: multiple readable channels exist (anonymous "
            "MQTT subscribe, DB file, unauthenticated dashboard). Probability=3 "
            "(Possible) when combining local access paths; Impact=4 (Major) for "
            "loss of confidentiality of monitoring data in a Smart City narrative."
        ),
    ),
    InitialRiskInput(
        threat_id="T-07",
        probability=2,
        impact=5,
        rationale=(
            "Illustrative estimate: ransomware is a host-level threat outside the "
            "MQTT app logic. No backup/restore automation was found in the repo. "
            "Probability=2 (Unlikely) for a careful lab PC; Impact=5 (Critical) "
            "for availability of historical data if encryption/deletion succeeds."
        ),
    ),
    InitialRiskInput(
        threat_id="T-08",
        probability=4,
        impact=3,
        rationale=(
            "Illustrative estimate: dashboard/app.py has no authentication "
            "(confirmed). On a shared host, opening :8501 is Likely (4). "
            "Impact=3 (Moderate): disclosure of environmental charts without "
            "direct write access to the broker from the UI alone."
        ),
    ),
    InitialRiskInput(
        threat_id="T-09",
        probability=3,
        impact=2,
        rationale=(
            "Illustrative estimate: malformed messages are Possible (3) because "
            "anonymous publish is allowed, but Impact=2 (Minor) due to confirmed "
            "validation that rejects invalid JSON/types without inserting into SQLite. "
            "Residual integrity risk of valid-but-false data is covered by T-02."
        ),
    ),
    InitialRiskInput(
        threat_id="T-10",
        probability=2,
        impact=4,
        rationale=(
            "Illustrative estimate: this repo uses a virtual Python simulator, not "
            "field IoT firmware, so classical device compromise is Unlikely (2) here. "
            "Impact=4 (Major) mirrors a real Smart City outcome if a trusted publisher "
            "identity were controlled by an attacker."
        ),
    ),
)


def _initial_map() -> dict[str, InitialRiskInput]:
    mapping = {item.threat_id: item for item in INITIAL_ASSESSMENTS}
    catalog_ids = {threat.threat_id for threat in THREAT_CATALOG}
    missing = catalog_ids - mapping.keys()
    extra = mapping.keys() - catalog_ids
    if missing or extra:
        raise RuntimeError(
            f"INITIAL_ASSESSMENTS out of sync with THREAT_CATALOG "
            f"(missing={sorted(missing)}, extra={sorted(extra)})"
        )
    return mapping


INITIAL_BY_ID: dict[str, InitialRiskInput] = _initial_map()


def assess_from_initial(
    threat_id: str,
    thresholds: RiskThresholds | None = None,
) -> RiskAssessment:
    """Assess one threat using the built-in illustrative Probability/Impact."""
    initial = INITIAL_BY_ID[threat_id]
    return assess_threat(
        threat_id,
        initial.probability,
        initial.impact,
        rationale=initial.rationale,
        assessment_type=initial.assessment_type,
        thresholds=thresholds,
    )


def assess_all(
    overrides: Mapping[str, tuple[int, int]] | None = None,
    thresholds: RiskThresholds | None = None,
) -> list[RiskAssessment]:
    """Assess every catalog threat; optional overrides are (probability, impact)."""
    overrides = overrides or {}
    results: list[RiskAssessment] = []

    for threat in THREAT_CATALOG:
        if threat.threat_id in overrides:
            probability, impact = overrides[threat.threat_id]
            results.append(
                assess_threat(
                    threat,
                    probability,
                    impact,
                    rationale=(
                        "User-adjusted values for interactive what-if analysis. "
                        "Not a measured operational risk."
                    ),
                    assessment_type="adjusted_by_user",
                    thresholds=thresholds,
                )
            )
        else:
            results.append(assess_from_initial(threat.threat_id, thresholds=thresholds))

    return results


def summarize_assessments(assessments: Iterable[RiskAssessment]) -> dict[str, int]:
    """Return aggregate counters for dashboard overview widgets."""
    items = list(assessments)
    if not items:
        return {
            "total_threats": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "highest_score": 0,
        }

    return {
        "total_threats": len(items),
        "high": sum(1 for item in items if item.risk_level == "High"),
        "medium": sum(1 for item in items if item.risk_level == "Medium"),
        "low": sum(1 for item in items if item.risk_level == "Low"),
        "highest_score": max(item.risk_score for item in items),
    }


def with_updated_factors(
    assessment: RiskAssessment,
    probability: int,
    impact: int,
    thresholds: RiskThresholds | None = None,
) -> RiskAssessment:
    """Recalculate an existing assessment after interactive slider changes."""
    score = calculate_risk_score(probability, impact)
    level = classify_risk_level(score, thresholds=thresholds)
    return replace(
        assessment,
        probability=probability,
        impact=impact,
        risk_score=score,
        risk_level=level,
        probability_label=PROBABILITY_LABELS[probability],
        impact_label=IMPACT_LABELS[impact],
        rationale=(
            "User-adjusted values for interactive what-if analysis. "
            "Not a measured operational risk."
        ),
        assessment_type="adjusted_by_user",
        is_illustrative=False,
    )
