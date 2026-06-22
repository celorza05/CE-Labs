"""CLI entrypoint: ``python -m src.producer`` (run from the repo root).

Builds the Higgsfield generation plan from the Writer's scripts, and optionally
generates the videos via the Higgsfield CLI.

Examples:
    python -m src.producer                      # plan only -> data/jobs/latest.json
    python -m src.producer --print              # also print the planned jobs
    python -m src.producer --submit --dry-run   # print the exact CLI commands, generate nothing
    python -m src.producer --submit --limit 1   # generate just the first video (test one before spending)
    python -m src.producer --submit             # generate all planned videos
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import planner, submit


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="producer", description="Plan Higgsfield generation jobs from scripts.")
    parser.add_argument("--input", default=None, help="override the scripts input path")
    parser.add_argument("--output-dir", default=None, help="override the output directory")
    parser.add_argument("--print", dest="do_print", action="store_true", help="print the planned jobs")
    parser.add_argument("--submit", action="store_true", help="generate the videos via the Higgsfield CLI")
    parser.add_argument("--dry-run", action="store_true", help="with --submit, print the CLI commands without running them")
    parser.add_argument("--limit", type=int, default=None, help="with --submit, generate at most N jobs")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def _print_jobs(jobs) -> None:
    for j in jobs:
        print(f"\n[{j.job_id}]  ({j.aspect_ratio}, {j.duration_seconds}s)")
        print(f"  title : {j.script_title}")
        print(f"  prompt: {j.prompt}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        jobs, path = planner.run(args.input, args.output_dir)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.do_print:
        _print_jobs(jobs)
    print(f"\nPlanned {len(jobs)} generation jobs -> {path}")

    if args.submit:
        try:
            submit.submit_all(jobs, limit=args.limit, dry_run=args.dry_run)
        except RuntimeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        # Persist the updated statuses/asset paths back to the plan.
        planner.write_plan(jobs, args.output_dir)
        if not args.dry_run:
            done = sum(1 for j in jobs if j.status == "completed")
            failed = sum(1 for j in jobs if j.status == "failed")
            print(f"Generated {done} videos ({failed} failed) -> {config_assets()}")
    return 0


def config_assets() -> str:
    from . import config

    return config.ASSETS_DIR


if __name__ == "__main__":
    raise SystemExit(main())
