"""CLI entrypoint: ``python -m src.clipper`` (run from the repo root).

Examples:
    python -m src.clipper                 # select clips -> data/clips/clips.json
    python -m src.clipper --print         # also print the chosen clips
    python -m src.clipper --top 3         # pick up to 3 clips
    python -m src.clipper --show-prompt   # print the prompt only (no API call)
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import config, selector
from .prompts import build_user_prompt, system_prompt


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="clipper", description="Pick the best clips from a transcript.")
    parser.add_argument("--top", type=int, default=None, help="override how many clips to pick")
    parser.add_argument("--input", default=None, help="override the transcript input path")
    parser.add_argument("--output-dir", default=None, help="override the output directory")
    parser.add_argument("--print", dest="do_print", action="store_true", help="print the chosen clips")
    parser.add_argument("--show-prompt", action="store_true", help="print the prompt and exit (no API call)")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def _fmt(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60:d}:{s % 60:02d}"


def _print_clips(clips) -> None:
    for i, c in enumerate(clips, start=1):
        print(f"\n{i}. [{_fmt(c.start_seconds)}–{_fmt(c.end_seconds)}]  ({c.end_seconds - c.start_seconds:.0f}s)")
        print(f"   hook : {c.hook}")
        print(f"   title: {c.title}")
        print(f"   why  : {c.reason}")
        print(f"   tags : {' '.join('#' + h for h in c.hashtags)}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    if args.top is not None:
        config.CLIPS_PER_RUN = args.top

    if args.show_prompt:
        transcript = selector.load_transcript(args.input)
        print("===== SYSTEM =====")
        print(system_prompt(config.CLIPS_PER_RUN, config.CLIP_MIN_SECONDS, config.CLIP_MAX_SECONDS))
        print("\n===== USER =====")
        print(build_user_prompt(transcript, config.CLIPS_PER_RUN, config.CLIP_MIN_SECONDS, config.CLIP_MAX_SECONDS))
        return 0

    try:
        clips, path = selector.run(args.input, args.output_dir)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        name = type(exc).__name__
        if "Authentication" in name or "api_key" in str(exc).lower():
            print("error: missing/invalid ANTHROPIC_API_KEY (see .env).", file=sys.stderr)
        else:
            print(f"error: {name}: {exc}", file=sys.stderr)
        return 1

    if args.do_print:
        _print_clips(clips)
    print(f"\nSelected {len(clips)} clips -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
