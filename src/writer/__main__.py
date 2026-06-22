"""CLI entrypoint: ``python -m src.writer`` (run from the repo root).

Examples:
    python -m src.writer                 # generate scripts, write data/scripts/
    python -m src.writer --print         # also print the scripts to stdout
    python -m src.writer --top 3         # produce up to 3 scripts
    python -m src.writer --show-prompt   # print the assembled prompt only (no API call)
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import config, generator
from .prompts import build_user_prompt, system_prompt


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="writer", description="Turn trends into short-form scripts.")
    parser.add_argument("--top", type=int, default=None, help="override how many scripts to produce")
    parser.add_argument("--input", default=None, help="override the trends input path")
    parser.add_argument("--output-dir", default=None, help="override the output directory")
    parser.add_argument("--print", dest="do_print", action="store_true", help="print the generated scripts")
    parser.add_argument("--show-prompt", action="store_true", help="print the prompt and exit (no API call)")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def _print_scripts(scripts) -> None:
    for i, s in enumerate(scripts, start=1):
        print(f"\n=== {i}. {s.title} ===")
        print(f"source : {s.source_title}\n         {s.source_url}")
        print(f"angle  : {s.angle}")
        print(f"hook   : {s.hook}")
        print(f"script : {s.script}")
        print(f"caption: {s.caption}")
        print(f"tags   : {' '.join('#' + h for h in s.hashtags)}")
        print(f"b-roll : {s.b_roll_prompt}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.top is not None:
        config.SCRIPTS_PER_RUN = args.top

    if args.show_prompt:
        trends = generator.load_trends(args.input)
        candidates = trends[: config.CANDIDATE_POOL]
        print("===== SYSTEM =====")
        print(system_prompt(config.VOICE, config.SCRIPTS_PER_RUN, config.MAX_PER_COMPANY))
        print("\n===== USER =====")
        print(build_user_prompt(candidates, config.SCRIPTS_PER_RUN))
        return 0

    try:
        scripts, path = generator.run(args.input, args.output_dir)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # API/auth/runtime errors → friendly message
        name = type(exc).__name__
        if "Authentication" in name or "api_key" in str(exc).lower():
            print(
                "error: missing/invalid ANTHROPIC_API_KEY. Create one at "
                "https://console.anthropic.com and put it in .env.",
                file=sys.stderr,
            )
        else:
            print(f"error: {name}: {exc}", file=sys.stderr)
        return 1

    if args.do_print:
        _print_scripts(scripts)
    print(f"\nWrote {len(scripts)} scripts to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
