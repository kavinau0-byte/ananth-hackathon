"""Public AI voice verification entry point for Member A."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .config import ConfigError, load_config
from .detectif_client import DetectifClient, DetectifError
from .policy import classify

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
SCENARIO_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
REQUIRED_OUTPUT_KEYS = {"aletheia", "eidos", "risk", "reason"}
VALID_RISKS = {"PASS", "BORDERLINE", "FAIL"}


def _fail_closed(
    reason: str,
    *,
    aletheia: dict[str, Any] | None = None,
    eidos: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "aletheia": aletheia,
        "eidos": eidos,
        "risk": "BORDERLINE",
        "reason": reason,
    }


def _load_fixture(scenario: str) -> dict[str, Any]:
    if not SCENARIO_PATTERN.match(scenario):
        return _fail_closed(
            "Invalid fixture scenario name; voice check failed closed. "
            "A score is evidence, not proof. "
            "Next step: verify FIXTURE_SCENARIO or call back on a number you already know."
        )

    fixture_path = FIXTURES_DIR / f"verify_{scenario}.json"
    if not fixture_path.is_file():
        return _fail_closed(
            f"Saved fixture for scenario '{scenario}' was not found; voice check failed closed. "
            "A score is evidence, not proof. "
            "Next step: check fixture files or call back on a number you already know."
        )

    try:
        data = json.loads(fixture_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _fail_closed(
            "Saved fixture file could not be read; voice check failed closed. "
            "A score is evidence, not proof. "
            "Next step: repair the fixture or call back on a number you already know."
        )

    if (
        not isinstance(data, dict)
        or set(data.keys()) != REQUIRED_OUTPUT_KEYS
        or data.get("risk") not in VALID_RISKS
        or not isinstance(data.get("reason"), str)
    ):
        return _fail_closed(
            "Saved fixture did not match the agreed output schema; voice check failed closed. "
            "A score is evidence, not proof. "
            "Next step: fix the fixture file or call back on a number you already know."
        )

    return {
        "aletheia": data["aletheia"],
        "eidos": data["eidos"],
        "risk": data["risk"],
        "reason": data["reason"],
    }


def _parse_eidos_response(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the agreed eidos shape from a Detectif /v1/speakers/verify response."""
    result = raw.get("result")
    operation_id = raw.get("operation_id")
    if not isinstance(result, dict) or not isinstance(operation_id, str) or not operation_id:
        return None
    if not {"decision", "similarity", "duration_seconds"}.issubset(result.keys()):
        return None
    return {
        "decision": result["decision"],
        "similarity": result["similarity"],
        "duration_seconds": result["duration_seconds"],
        "operation_id": operation_id,
    }


def _parse_aletheia_from_verify(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Extract the agreed aletheia shape from a combined verify_speaker response."""
    if raw.get("aletheia_status") == "unavailable":
        return None

    result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
    deepfake = raw.get("deepfake")
    if deepfake is None and isinstance(result, dict):
        deepfake = result.get("deepfake")

    if not isinstance(deepfake, dict) or deepfake.get("error") is not None:
        return None

    verdict = deepfake.get("verdict")
    score = deepfake.get("score")
    duration = deepfake.get("duration_seconds", result.get("duration_seconds"))
    operation_id = deepfake.get("operation_id", raw.get("operation_id"))

    if verdict is None or score is None or duration is None:
        return None
    if not isinstance(operation_id, str) or not operation_id:
        return None

    return {
        "verdict": verdict,
        "score": score,
        "duration_seconds": duration,
        "operation_id": operation_id,
    }


def verify_voice(audio_path: str, employee_id: str) -> dict[str, Any]:
    """Verify voice audio and return the agreed 4-key decision dict.

    Live mode makes ONE combined verify_speaker(..., detect_deepfake=True) call
    so both Eidos and Aletheia evaluate the exact same recording.
    """
    try:
        config = load_config()
    except ConfigError:
        return _fail_closed(
            "Voice check is not configured for live verification; check failed closed. "
            "A score is evidence, not proof. "
            "Next step: escalate to an admin or call back on a number you already know."
        )

    if config.ai_mode == "fixture":
        return _load_fixture(config.fixture_scenario)

    if not audio_path or not isinstance(audio_path, str):
        return _fail_closed(
            "No usable audio file was provided. "
            "A score is evidence, not proof. "
            "Next step: ask the requester to re-record clearly, or call back on a number you already know."
        )

    if not employee_id or not isinstance(employee_id, str):
        return _fail_closed(
            "No valid employee identifier was provided for speaker verification. "
            "A score is evidence, not proof. "
            "Next step: confirm the requester's employee ID or call back on a number you already know."
        )

    try:
        assert config.detectif_api_key is not None
        with DetectifClient(
            config.detectif_api_key,
            base_url=config.detectif_base_url,
        ) as client:
            raw = client.verify_speaker(
                audio_path,
                speaker_id=employee_id,
                detect_deepfake=True,
            )
    except (DetectifError, OSError):
        return _fail_closed(
            "Voice check service encountered an error or unreadable audio and failed closed. "
            "A score is evidence, not proof. "
            "Next step: ask the requester to re-record, or call back on a number you already know."
        )

    aletheia = _parse_aletheia_from_verify(raw)
    eidos = _parse_eidos_response(raw)
    risk, reason = classify(aletheia, eidos)
    return {
        "aletheia": aletheia,
        "eidos": eidos,
        "risk": risk,
        "reason": reason,
    }
