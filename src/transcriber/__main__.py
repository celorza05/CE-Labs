"""CLI: ``python -m src.transcriber`` (run from the repo root).

Reads data/clips/source.json and writes data/clips/transcript.json.

Examples:
    python -m src.transcriber
    python -m src.transcriber --input data/clips/source.json --output data/clips/transcript.json
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import transcriber


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="transcriber", description="Transcribe source media with local Whisper.")
    parser.add_argument("--input", default=None, help="override source.json path")
    parser.add_argument("--output", default=None, help="override transcript.json path")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        transcript, path = transcriber.run(args.input, args.output)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"\nTranscribed: {transcript['source']['title']}")
    print(f"  segments: {len(transcript['segments'])}")
    print(f"  -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
