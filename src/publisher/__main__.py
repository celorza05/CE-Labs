"""CLI entrypoint: ``python -m src.publisher`` (run from the repo root).

Safe by default: prepares the TikTok hand-off and *plans* the YouTube upload,
but only uploads to YouTube when you pass ``--youtube``. Uploads are PRIVATE
unless you override ``--privacy``.

Examples:
    python -m src.publisher --dry-run             # preview titles/descriptions, do nothing
    python -m src.publisher                        # prepare TikTok hand-offs; plan YouTube (no upload)
    python -m src.publisher --youtube              # also upload to YouTube as PRIVATE
    python -m src.publisher --youtube --privacy unlisted --limit 1
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import publisher


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="publisher", description="Publish videos to YouTube / TikTok.")
    parser.add_argument("--youtube", action="store_true", help="actually upload to YouTube (default: plan only)")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"], default=None,
                        help="YouTube privacy (default: private)")
    parser.add_argument("--limit", type=int, default=None, help="publish at most N videos")
    parser.add_argument("--dry-run", action="store_true", help="preview only; upload/prepare nothing")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def _print_results(results) -> None:
    for r in results:
        print(f"\n[{r.job_id}] {r.title}")
        print(f"  asset  : {r.asset_path}")
        print(f"  youtube: {r.youtube_status}" + (f" -> {r.youtube_url}" if r.youtube_url else "")
              + (f" (privacy={r.youtube_privacy})" if r.youtube_privacy else ""))
        print(f"  tiktok : {r.tiktok_status}" + (f" -> {r.tiktok_package_dir}" if r.tiktok_package_dir else ""))


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        results, path = publisher.run(
            do_youtube=args.youtube, privacy=args.privacy, limit=args.limit, dry_run=args.dry_run
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    _print_results(results)
    uploaded = sum(1 for r in results if r.youtube_status == "uploaded")
    prepared = sum(1 for r in results if r.tiktok_status == "prepared")
    mode = "dry-run" if args.dry_run else "done"
    print(f"\n[{mode}] {len(results)} videos | YouTube uploaded: {uploaded} | TikTok prepared: {prepared}")
    print(f"report -> {path}")
    if not args.youtube and not args.dry_run:
        print("note: YouTube was planned, not uploaded. Re-run with --youtube to upload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
