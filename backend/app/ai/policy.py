"""Pure decision policy for Break-Glass Voice Gate (full Day-2 fail-closed rules)."""

from __future__ import annotations

import math
from typing import Any, Literal

Risk = Literal["PASS", "BORDERLINE", "FAIL"]

# TODO: calibrate from saved fixtures
ALETHEIA_BORDER_SCORE: float | None = None
# TODO: calibrate from saved fixtures
EIDOS_NEAR_MISS_SIMILARITY: float | None = None


def _is_valid_number(value: Any, *, low: float, high: float) -> bool:
    """Return True if value is a finite int/float (excluding bool) within [low, high]."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and low <= float(value) <= high


def _is_positive_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and float(value) > 0.0


def _validate_aletheia(aletheia: dict[str, Any] | None) -> tuple[str, float] | None:
    if not isinstance(aletheia, dict):
        return None
    verdict = aletheia.get("verdict")
    score = aletheia.get("score")
    duration = aletheia.get("duration_seconds")
    operation_id = aletheia.get("operation_id")

    if verdict not in ("real", "fake"):
        return None
    if not _is_valid_number(score, low=0.0, high=1.0):
        return None
    if not _is_positive_number(duration):
        return None
    if not isinstance(operation_id, str) or not operation_id.strip():
        return None
    return verdict, float(score)


def _validate_eidos(eidos: dict[str, Any] | None) -> tuple[str, float] | None:
    if not isinstance(eidos, dict):
        return None
    decision = eidos.get("decision")
    similarity = eidos.get("similarity")
    duration = eidos.get("duration_seconds")
    operation_id = eidos.get("operation_id")

    if decision not in ("match", "no_match"):
        return None
    if not _is_valid_number(similarity, low=-1.0, high=1.0):
        return None
    if not _is_positive_number(duration):
        return None
    if not isinstance(operation_id, str) or not operation_id.strip():
        return None
    return decision, float(similarity)


def classify(
    aletheia: dict[str, Any] | None,
    eidos: dict[str, Any] | None,
) -> tuple[Risk, str]:
    """Classify Aletheia + Eidos signals into (risk, reason).

    Full Day-2 rules (fail closed):
    - aletheia "fake" -> FAIL
    - eidos "no_match" -> FAIL, unless EIDOS_NEAR_MISS_SIMILARITY is set and similarity >= it -> BORDERLINE
    - either model missing/errored -> BORDERLINE (never PASS)
    - aletheia "real" + eidos "match" -> PASS (or BORDERLINE if ALETHEIA_BORDER_SCORE is set and score >= it)
    """
    parsed_aletheia = _validate_aletheia(aletheia)
    parsed_eidos = _validate_eidos(eidos)

    # Synthetic speech indicator always fails even if speaker check errored.
    if parsed_aletheia is not None and parsed_aletheia[0] == "fake":
        return (
            "FAIL",
            "Voice check flagged synthetic speech indicators. "
            "This score is evidence, not proof, so treat the request as high risk. "
            "Next step: do not approve yet and call back on a number you already know.",
        )

    # Speaker mismatch fails unless similarity is high enough to be a calibrated near-miss.
    if parsed_eidos is not None and parsed_eidos[0] == "no_match":
        similarity = parsed_eidos[1]
        if (
            EIDOS_NEAR_MISS_SIMILARITY is not None
            and similarity >= EIDOS_NEAR_MISS_SIMILARITY
        ):
            return (
                "BORDERLINE",
                "Speaker check returned a near-miss close to the match threshold. "
                "A score is evidence, not proof. "
                "Next step: ask the requester to re-record clearly, or call back on a number you already know.",
            )
        return (
            "FAIL",
            "Voice did not match the enrolled speaker profile. "
            "This score is evidence, not proof, so treat the request as high risk. "
            "Next step: do not approve yet and call back on a number you already know.",
        )

    # Both models are required to PASS; if either is missing or invalid, fail closed.
    if parsed_aletheia is None and parsed_eidos is None:
        return (
            "BORDERLINE",
            "Voice check could not be completed with usable audio or results. "
            "Remember that any voice score is evidence, not proof. "
            "Next step: ask the requester to re-record clearly, or call back on a number you already know.",
        )

    if parsed_aletheia is None:
        return (
            "BORDERLINE",
            "Deepfake detection was unavailable or returned incomplete data, so the check failed closed. "
            "A score is evidence, not proof. "
            "Next step: ask the requester to re-record, or call back on a number you already know.",
        )

    if parsed_eidos is None:
        return (
            "BORDERLINE",
            "Speaker identity check was unavailable or returned incomplete data, so the check failed closed. "
            "A score is evidence, not proof. "
            "Next step: confirm the employee is enrolled, ask to re-record, or call back on a number you already know.",
        )

    # Both models succeeded: aletheia == "real" and eidos == "match".
    _, score = parsed_aletheia
    if ALETHEIA_BORDER_SCORE is not None and score >= ALETHEIA_BORDER_SCORE:
        return (
            "BORDERLINE",
            "Voice matched the speaker and was labeled real, but the deepfake score is close to the review cutoff. "
            "A score is evidence, not proof. "
            "Next step: ask the requester to re-record in a quiet spot, or call back on a number you already know.",
        )

    return (
        "PASS",
        "Voice matched the enrolled speaker with no synthetic speech indicators detected. "
        "Remember that these scores are evidence, not proof. "
        "Next step: continue with your normal break-glass approval checks, or call back on a number you already know if anything feels off.",
    )
