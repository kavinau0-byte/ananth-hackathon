"""Speaker enrollment helper and CLI for Eidos voice profiles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from .config import ConfigError, load_config
from .detectif_client import (
    SUPPORTED_AUDIO_EXTENSIONS,
    DetectifClient,
    DetectifError,
    validate_speaker_id,
)

MAX_ENROLLMENT_SAMPLES = 5


class EnrollmentError(Exception):
    """Raised when local enrollment validation or an enrollment API call fails."""


def _validate_audio_paths(paths: Sequence[str | Path]) -> list[Path]:
    if not paths:
        raise EnrollmentError("At least one audio file path is required for enrollment.")
    if len(paths) > MAX_ENROLLMENT_SAMPLES:
        raise EnrollmentError(
            f"Too many samples provided ({len(paths)}). "
            f"Detectif allows a maximum of {MAX_ENROLLMENT_SAMPLES} enrollment samples per speaker."
        )

    validated: list[Path] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_file():
            raise EnrollmentError(f"Audio file not found or not a file: {path}")
        if path.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            allowed = ", ".join(sorted(SUPPORTED_AUDIO_EXTENSIONS))
            raise EnrollmentError(
                f"Unsupported audio format '{path.suffix.lower()}' for {path.name}. "
                f"Supported formats: {allowed}."
            )
        if path.stat().st_size == 0:
            raise EnrollmentError(f"Audio file is empty: {path}")
        validated.append(path)

    return validated


def enroll_employee(
    employee_id: str,
    paths: Sequence[str | Path],
    *,
    display_name: str | None = None,
    client: DetectifClient | None = None,
) -> dict[str, Any]:
    """Validate audio files locally and enroll up to 5 samples for an employee."""
    try:
        speaker_id = validate_speaker_id(employee_id)
    except DetectifError as exc:
        raise EnrollmentError(exc.message) from exc

    audio_paths = _validate_audio_paths(paths)

    owns_client = client is None
    if client is None:
        try:
            config = load_config(require_live=True)
            assert config.detectif_api_key is not None
            client = DetectifClient(
                config.detectif_api_key,
                base_url=config.detectif_base_url,
            )
        except (ConfigError, DetectifError) as exc:
            raise EnrollmentError(str(exc)) from exc

    enrolled: list[dict[str, Any]] = []
    skipped: list[str] = []

    try:
        for index, audio_path in enumerate(audio_paths):
            try:
                response = client.enroll_speaker(
                    audio_path,
                    speaker_id=speaker_id,
                    display_name=display_name,
                )
            except DetectifError as exc:
                if exc.status == 409 and (exc.code in (None, "too_many_samples")):
                    skipped = [str(p) for p in audio_paths[index:]]
                    return {
                        "employee_id": speaker_id,
                        "enrolled": enrolled,
                        "skipped": skipped,
                        "cap_reached": True,
                        "message": (
                            f"Speaker '{speaker_id}' has already reached the maximum of "
                            f"{MAX_ENROLLMENT_SAMPLES} enrollment samples (HTTP 409 too_many_samples). "
                            f"Enrolled {len(enrolled)} new sample(s) in this run; "
                            f"{len(skipped)} remaining file(s) were not uploaded."
                        ),
                    }
                raise EnrollmentError(
                    f"Failed to enroll '{audio_path.name}' for '{speaker_id}': {exc}"
                ) from exc

            enrolled.append(
                {
                    "file": str(audio_path),
                    "operation_id": response.get("operation_id"),
                    "request_id": response.get("request_id"),
                }
            )
    finally:
        if owns_client:
            client.close()

    return {
        "employee_id": speaker_id,
        "enrolled": enrolled,
        "skipped": skipped,
        "cap_reached": False,
        "message": (
            f"Successfully enrolled {len(enrolled)} sample(s) for speaker '{speaker_id}' "
            f"(limit is {MAX_ENROLLMENT_SAMPLES} samples per speaker)."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Enroll 1-5 voice samples (15-60s each, >=10s speech) for an employee."
    )
    parser.add_argument("employee_id", help="Employee / speaker ID (^[A-Za-z0-9_.:-]{1,64}$)")
    parser.add_argument(
        "audio_paths",
        nargs="+",
        help="1 to 5 local audio files (WAV, MP3, M4A, FLAC, OGG, WebM)",
    )
    parser.add_argument(
        "--display-name",
        default=None,
        help="Optional display name stored with the speaker profile",
    )
    args = parser.parse_args(argv)

    try:
        summary = enroll_employee(
            args.employee_id,
            args.audio_paths,
            display_name=args.display_name,
        )
    except EnrollmentError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(summary["message"])
    for item in summary["enrolled"]:
        print(f"  - enrolled: {item['file']} (operation_id={item.get('operation_id')})")
    if summary["cap_reached"]:
        for path in summary["skipped"]:
            print(f"  - skipped (5-sample cap): {path}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
