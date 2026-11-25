import argparse
import os
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

API_URL = "https://platform.detectif.ai/v1/deepfake/detect"
FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "aletheia_sample.json"


def main():
    parser = argparse.ArgumentParser(description="Save one Aletheia response as a fixture.")
    parser.add_argument("audio", type=Path, help="path to a 4-120 second audio clip")
    args = parser.parse_args()

    if load_dotenv is not None:
        load_dotenv()

    api_key = os.getenv("DETECTIF_API_KEY")
    if not api_key:
        print(
            "DETECTIF_API_KEY is not set; export it or add it to .env (never commit it).",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not args.audio.is_file():
        print(f"Audio file not found: {args.audio}", file=sys.stderr)
        raise SystemExit(1)

    with args.audio.open("rb") as handle:
        response = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (args.audio.name, handle)},
            timeout=120,
        )
    response.raise_for_status()

    raw = response.text
    print(raw)
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE_PATH.write_text(raw, encoding="utf-8")
    print(f"Saved response to {FIXTURE_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
