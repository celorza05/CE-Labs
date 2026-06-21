"""CLI: ``python -m src.clips_orchestrator <command>`` (run from repo root).

Commands:
    prepare <source>   Sourcer -> Transcriber -> Clipper -> Cutter; post to Slack; stop.
    publish            Publish the cut clips (after approving `prepare`).
    status             Show where the last run left off.

Examples:
    python -m src.clips_orchestrator prepare "https://youtu.be/VIDEO" --reframe face
    python -m src.clips_orchestrator publish --youtube --privacy unlisted
    python -m src.clips_orchestrator status
"""

from __future__ import annotations

import argparse
import json
import logging
import sys


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="clips_orchestrator", description="Drive the clips pipeline.")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prep = sub.add_parser("prepare", help="source -> transcribe -> clip -> cut, then await approval")
    p_prep.add_argument("source", help="YouTube URL, local file, or podcast RSS URL")
    p_prep.add_argument("--reframe", choices=["center", "face"], default=None, help="Cutter crop mode")

    p_pub = sub.add_parser("publish", help="publish the cut clips (after approving prepare)")
    p_pub.add_argument("--youtube", action="store_true", help="actually upload to YouTube")
    p_pub.add_argument("--privacy", choices=["private", "unlisted", "public"], default=None)
    p_pub.add_argument("--limit", type=int, default=None, help="publish at most N clips")

    sub.add_parser("status", help="show the last run's state")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    from . import orchestrator

    try:
        if args.command == "prepare":
            state = orchestrator.prepare(args.source, reframe=args.reframe)
            print(json.dumps(state, indent=2))
            print("\nawaiting approval — review data/clips/out/, then: python -m src.clips_orchestrator publish")
        elif args.command == "publish":
            state = orchestrator.publish(youtube=args.youtube, privacy=args.privacy, limit=args.limit)
            print(json.dumps(state, indent=2))
        elif args.command == "status":
            state = orchestrator.load_state()
            print(json.dumps(state, indent=2) if state else "no runs yet")
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
