"""Pytest suite for Day-2 policy, challenge, enrollment, client, and voice_check."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import httpx
import pytest

try:
    from backend.app.ai import challenge, enrollment, policy
    from backend.app.ai.detectif_client import DetectifClient, DetectifError
    from backend.app.ai.voice_check import verify_voice
except ModuleNotFoundError:
    from app.ai import challenge, enrollment, policy  # type: ignore[no-redef]
    from app.ai.detectif_client import DetectifClient, DetectifError  # type: ignore[no-redef]
    from app.ai.voice_check import verify_voice  # type: ignore[no-redef]


def _sample_aletheia(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "verdict": "real",
        "score": 0.12,
        "duration_seconds": 5.5,
        "operation_id": "op_aletheia_123",
    }
    base.update(overrides)
    return base


def _sample_eidos(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "decision": "match",
        "similarity": 0.85,
        "duration_seconds": 5.5,
        "operation_id": "op_eidos_123",
    }
    base.update(overrides)
    return base


def _assert_reason_quality(reason: str) -> None:
    lower = reason.lower()
    assert isinstance(reason, str) and len(reason.strip()) > 20
    assert "evidence, not proof" in lower
    assert "next step:" in lower


# --- Policy tests ---


def test_aletheia_fake_returns_fail_even_with_eidos_match() -> None:
    risk, reason = policy.classify(
        _sample_aletheia(verdict="fake", score=0.92),
        _sample_eidos(decision="match", similarity=0.91),
    )
    assert risk == "FAIL"
    _assert_reason_quality(reason)


def test_aletheia_fake_with_missing_eidos_still_fails() -> None:
    risk, reason = policy.classify(_sample_aletheia(verdict="fake", score=0.92), None)
    assert risk == "FAIL"
    _assert_reason_quality(reason)


def test_eidos_no_match_returns_fail_when_threshold_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(policy, "EIDOS_NEAR_MISS_SIMILARITY", None)
    risk, reason = policy.classify(
        _sample_aletheia(verdict="real", score=0.05),
        _sample_eidos(decision="no_match", similarity=0.55),
    )
    assert risk == "FAIL"
    _assert_reason_quality(reason)


def test_eidos_no_match_near_miss_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(policy, "EIDOS_NEAR_MISS_SIMILARITY", 0.50)

    risk_low, reason_low = policy.classify(
        _sample_aletheia(),
        _sample_eidos(decision="no_match", similarity=0.49),
    )
    assert risk_low == "FAIL"
    _assert_reason_quality(reason_low)

    risk_equal, reason_equal = policy.classify(
        _sample_aletheia(),
        _sample_eidos(decision="no_match", similarity=0.50),
    )
    assert risk_equal == "BORDERLINE"
    _assert_reason_quality(reason_equal)

    risk_above, reason_above = policy.classify(
        _sample_aletheia(),
        _sample_eidos(decision="no_match", similarity=0.62),
    )
    assert risk_above == "BORDERLINE"
    _assert_reason_quality(reason_above)


def test_real_and_match_returns_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(policy, "ALETHEIA_BORDER_SCORE", None)
    risk, reason = policy.classify(_sample_aletheia(), _sample_eidos())
    assert risk == "PASS"
    _assert_reason_quality(reason)


def test_real_and_match_with_aletheia_border_score(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(policy, "ALETHEIA_BORDER_SCORE", 0.40)

    risk_below, reason_below = policy.classify(
        _sample_aletheia(score=0.39), _sample_eidos()
    )
    assert risk_below == "PASS"
    _assert_reason_quality(reason_below)

    risk_equal, reason_equal = policy.classify(
        _sample_aletheia(score=0.40), _sample_eidos()
    )
    assert risk_equal == "BORDERLINE"
    _assert_reason_quality(reason_equal)

    risk_above, reason_above = policy.classify(
        _sample_aletheia(score=0.65), _sample_eidos()
    )
    assert risk_above == "BORDERLINE"
    _assert_reason_quality(reason_above)


def test_either_model_missing_returns_borderline() -> None:
    risk_both, reason_both = policy.classify(None, None)
    assert risk_both == "BORDERLINE"
    _assert_reason_quality(reason_both)

    risk_no_aletheia, reason_no_aletheia = policy.classify(None, _sample_eidos())
    assert risk_no_aletheia == "BORDERLINE"
    _assert_reason_quality(reason_no_aletheia)

    risk_no_eidos, reason_no_eidos = policy.classify(_sample_aletheia(), None)
    assert risk_no_eidos == "BORDERLINE"
    _assert_reason_quality(reason_no_eidos)


@pytest.mark.parametrize(
    "bad_aletheia",
    [
        {},
        _sample_aletheia(verdict="unknown"),
        _sample_aletheia(verdict=None),
        _sample_aletheia(score=-0.01),
        _sample_aletheia(score=1.01),
        _sample_aletheia(score=float("nan")),
        _sample_aletheia(score=True),
        _sample_aletheia(duration_seconds=0),
        _sample_aletheia(duration_seconds=-2.0),
        _sample_aletheia(operation_id=""),
    ],
)
def test_fail_closed_on_invalid_aletheia(bad_aletheia: object) -> None:
    risk, reason = policy.classify(bad_aletheia, _sample_eidos())  # type: ignore[arg-type]
    assert risk == "BORDERLINE"
    _assert_reason_quality(reason)


@pytest.mark.parametrize(
    "bad_eidos",
    [
        {},
        _sample_eidos(decision="maybe"),
        _sample_eidos(similarity=1.5),
        _sample_eidos(similarity=False),
        _sample_eidos(duration_seconds=0),
        _sample_eidos(operation_id=""),
    ],
)
def test_fail_closed_on_invalid_eidos(bad_eidos: dict[str, object]) -> None:
    risk, reason = policy.classify(_sample_aletheia(), bad_eidos)
    assert risk == "BORDERLINE"
    _assert_reason_quality(reason)


# --- Challenge tests ---


def test_challenge_word_list_and_generation() -> None:
    assert len(challenge.WORD_LIST) >= 200
    assert len(set(challenge.WORD_LIST)) == len(challenge.WORD_LIST)

    word_set = set(challenge.WORD_LIST)
    for _ in range(25):
        phrase = challenge.generate_challenge()
        # Extract the 3 chosen words from the phrase
        match = re.search(r"words are ([a-z]+), ([a-z]+), and ([a-z]+),", phrase)
        assert match is not None
        chosen = list(match.groups())
        assert len(set(chosen)) == 3
        assert all(w in word_set for w in chosen)
        digits = re.findall(r"\b\d\b", phrase)
        assert len(digits) == 2
        # Long enough to speak for ~4+ seconds (>= 15 words)
        assert len(phrase.split()) >= 15


# --- Client + Enrollment + Combined Live Voice Check tests ---


def test_verify_speaker_deepfake_error_marks_aletheia_unavailable(
    tmp_path: Path,
) -> None:
    wav = tmp_path / "clip.wav"
    wav.write_bytes(b"RIFFdemo")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/speakers/verify"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert "Idempotency-Key" in request.headers
        return httpx.Response(
            200,
            json={
                "request_id": "req_1",
                "operation_id": "op_eidos_9",
                "result": {
                    "decision": "match",
                    "similarity": 0.88,
                    "duration_seconds": 5.1,
                },
                "deepfake": {"error": {"code": "service_unavailable", "message": "busy"}},
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(base_url="https://platform.detectif.ai", transport=transport) as http_client:
        client = DetectifClient("test-key", client=http_client)
        res = client.verify_speaker(wav, "emp_001", detect_deepfake=True)

    assert res["aletheia_status"] == "unavailable"
    assert res["deepfake"] is None
    assert res["result"]["decision"] == "match"


def test_enroll_employee_local_validation_and_409_cap(tmp_path: Path) -> None:
    bad_ext = tmp_path / "clip.txt"
    bad_ext.write_text("not audio")
    with pytest.raises(enrollment.EnrollmentError, match="Unsupported audio format"):
        enrollment.enroll_employee("emp_001", [bad_ext])

    valid_files = []
    for i in range(6):
        p = tmp_path / f"sample_{i}.wav"
        p.write_bytes(b"RIFFdata")
        valid_files.append(p)

    with pytest.raises(enrollment.EnrollmentError, match="maximum of 5"):
        enrollment.enroll_employee("emp_001", valid_files)

    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"request_id": "r1", "operation_id": "op1"})
        return httpx.Response(
            409,
            json={
                "request_id": "r2",
                "error": {
                    "type": "conflict",
                    "code": "too_many_samples",
                    "message": "Speaker already has 5 samples.",
                },
            },
        )

    transport = httpx.MockTransport(handler)
    with httpx.Client(base_url="https://platform.detectif.ai", transport=transport) as http_client:
        client = DetectifClient("test-key", client=http_client)
        summary = enrollment.enroll_employee("emp_001", valid_files[:2], client=client)

    assert summary["cap_reached"] is True
    assert len(summary["enrolled"]) == 1
    assert len(summary["skipped"]) == 1
    assert "maximum of 5" in summary["message"]


def test_verify_voice_live_single_combined_call_and_deepfake_error_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    wav = tmp_path / "live.wav"
    wav.write_bytes(b"RIFFdemo")

    monkeypatch.setenv("AI_MODE", "live")
    monkeypatch.setenv("DETECTIF_API_KEY", "dummy-key")

    call_count = 0

    def fake_verify_speaker(
        self: DetectifClient,
        path: str | Path,
        speaker_id: str,
        detect_deepfake: bool = True,
    ) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        assert speaker_id == "emp_001"
        assert detect_deepfake is True
        return {
            "request_id": "req_live",
            "operation_id": "op_live_1",
            "result": {
                "decision": "match",
                "similarity": 0.91,
                "duration_seconds": 5.4,
            },
            "deepfake": None,
            "aletheia_status": "unavailable",
        }

    monkeypatch.setattr(DetectifClient, "verify_speaker", fake_verify_speaker)

    out = verify_voice(str(wav), "emp_001")
    assert call_count == 1
    assert set(out.keys()) == {"aletheia", "eidos", "risk", "reason"}
    assert out["aletheia"] is None
    assert out["eidos"] == {
        "decision": "match",
        "similarity": 0.91,
        "duration_seconds": 5.4,
        "operation_id": "op_live_1",
    }
    assert out["risk"] == "BORDERLINE"
    _assert_reason_quality(out["reason"])


@pytest.mark.parametrize(
    ("scenario", "expected_risk"),
    [
        ("pass", "PASS"),
        ("borderline", "BORDERLINE"),
        ("fail", "FAIL"),
        ("error", "BORDERLINE"),
        ("does_not_exist", "BORDERLINE"),
    ],
)
def test_verify_voice_fixture_mode(
    monkeypatch: pytest.MonkeyPatch, scenario: str, expected_risk: str
) -> None:
    monkeypatch.setenv("AI_MODE", "fixture")
    monkeypatch.setenv("FIXTURE_SCENARIO", scenario)
    monkeypatch.delenv("DETECTIF_API_KEY", raising=False)

    out = verify_voice("unused.wav", "emp_001")
    assert set(out.keys()) == {"aletheia", "eidos", "risk", "reason"}
    assert out["risk"] == expected_risk
    _assert_reason_quality(out["reason"])
