"""CLI: ``python -m src.sourcer <url-or-file> [options]`` (run from repo root).

Examples:
    python -m src.sourcer "https://youtu.be/VIDEO_ID"
    python -m src.sourcer ./my-interview.mp4
    python -m src.sourcer "https://feeds.example.com/podcast.rss" --type podcast --episode 0
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import sourcer


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="sourcer", description="Fetch long-form content for clipping.")
    parser.add_argument("input", help="YouTube URL, local file path, or podcast RSS URL")
    parser.add_argument("--type", choices=["youtube", "local", "podcast"], default=None, help="force the source type")
    parser.add_argument("--episode", type=int, default=None, help="podcast episode index (0 = newest)")
    parser.add_argument("--output", default=None, help="override source.json path")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        source, path = sourcer.run(args.input, args.type, args.episode, args.output)
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"\nSourced: {source.title}")
    print(f"  type    : {source.source_type} ({'video' if source.has_video else 'audio-only'})")
    print(f"  duration: {source.duration_seconds:.0f}s")
    print(f"  media   : {source.media_path}")
    print(f"  -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
