"""CLI: ``python -m src.cutter`` (run from the repo root).

Cuts each clip from data/clips/clips.json into a finished vertical MP4 with
burned captions, written to data/clips/out/.

Examples:
    python -m src.cutter --dry-run     # print the ffmpeg commands, cut nothing
    python -m src.cutter --limit 1     # cut just the first clip
    python -m src.cutter               # cut all clips
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import cutter


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="cutter", description="Cut vertical clips with captions via ffmpeg.")
    parser.add_argument("--limit", type=int, default=None, help="cut at most N clips")
    parser.add_argument("--dry-run", action="store_true", help="print ffmpeg commands; cut nothing")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        results, report = cutter.run(limit=args.limit, dry_run=args.dry_run)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    done = sum(1 for r in results if r["status"] == "done")
    failed = sum(1 for r in results if r["status"] == "failed")
    for r in results:
        print(f"  [{r['status']}] {r['clip']} -> {r['output']}")
    mode = "dry-run" if args.dry_run else "done"
    print(f"\n[{mode}] {len(results)} clips | cut: {done} | failed: {failed}")
    print(f"report -> {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
