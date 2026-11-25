"""CLI to capture live Detectif responses into backend/fixtures/raw_<name>.json."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .detectif_client import DetectifClient, DetectifError

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"
NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a live Detectif deepfake check and save the raw JSON fixture."
    )
    parser.add_argument("audio_path", help="Path to the local audio file (e.g. sample.wav)")
    parser.add_argument(
        "--name",
        required=True,
        help="Short fixture name; saves to backend/fixtures/raw_<name>.json",
    )
    args = parser.parse_args(argv)

    if not NAME_PATTERN.match(args.name):
        print("Error: --name must contain only letters, digits, '_' or '-'.", file=sys.stderr)
        return 2

    try:
        config = load_config(require_live=True)
        assert config.detectif_api_key is not None
        with DetectifClient(
            config.detectif_api_key,
            base_url=config.detectif_base_url,
        ) as client:
            raw_response = client.detect_deepfake(args.audio_path)
    except (ConfigError, DetectifError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIXTURES_DIR / f"raw_{args.name}.json"
    out_path.write_text(
        json.dumps(raw_response, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )

    result = raw_response.get("result") if isinstance(raw_response, dict) else None
    verdict = result.get("verdict") if isinstance(result, dict) else "unknown"
    score = result.get("score") if isinstance(result, dict) else "unknown"
    print(f"Saved raw fixture to {out_path} (verdict={verdict}, score={score})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
