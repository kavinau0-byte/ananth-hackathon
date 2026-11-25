"""AI voice verification module (Aletheia / Eidos)."""

from __future__ import annotations

from typing import Any

__all__ = ["verify_voice", "enroll_employee", "generate_challenge"]


def __getattr__(name: str) -> Any:
    if name == "verify_voice":
        from .voice_check import verify_voice

        return verify_voice
    if name == "enroll_employee":
        from .enrollment import enroll_employee

        return enroll_employee
    if name == "generate_challenge":
        from .challenge import generate_challenge

        return generate_challenge
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
