"""CLI entrypoint: ``python -m src.orchestrator <command>`` (run from repo root).

Commands:
    prepare   Scout -> Writer -> Producer; post to Slack; stop for review.
    publish   Run the Publisher (do this only after approving `prepare`).
    status    Show where the last run left off.

Examples:
    python -m src.orchestrator prepare              # plan only (free; no generation)
    python -m src.orchestrator prepare --generate   # also generate videos (Higgsfield)
    python -m src.orchestrator publish              # prepare TikTok; plan YouTube
    python -m src.orchestrator publish --youtube --privacy unlisted
    python -m src.orchestrator status
"""

from __future__ import annotations

import argparse
import json
import logging
import sys


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="orchestrator", description="Drive the content pipeline.")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    p_prep = sub.add_parser("prepare", help="run Scout -> Writer -> Producer, then await approval")
    p_prep.add_argument("--generate", action="store_true", help="also generate videos via Higgsfield (costs credits)")
    p_prep.add_argument("--limit", type=int, default=None, help="with --generate, generate at most N videos")

    p_pub = sub.add_parser("publish", help="run the Publisher (after approving prepare)")
    p_pub.add_argument("--youtube", action="store_true", help="actually upload to YouTube (default: plan only)")
    p_pub.add_argument("--privacy", choices=["private", "unlisted", "public"], default=None)
    p_pub.add_argument("--limit", type=int, default=None, help="publish at most N videos")

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
            state = orchestrator.prepare(generate=args.generate or None, limit=args.limit)
            print(json.dumps(state, indent=2))
            print("\nawaiting approval — review, then: python -m src.orchestrator publish")
        elif args.command == "publish":
            state = orchestrator.publish(youtube=args.youtube, privacy=args.privacy, limit=args.limit)
            print(json.dumps(state, indent=2))
        elif args.command == "status":
            state = orchestrator.load_state()
            print(json.dumps(state, indent=2) if state else "no runs yet")
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
