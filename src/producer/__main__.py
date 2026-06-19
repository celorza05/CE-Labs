"""CLI entrypoint: ``python -m src.producer`` (run from the repo root).

Builds the Higgsfield generation plan from the Writer's scripts. The actual
generation/submission step is wired separately once the Higgsfield access
method is confirmed (see the repo README).

Examples:
    python -m src.producer            # build data/jobs/latest.json
    python -m src.producer --print    # also print the planned jobs
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import planner


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="producer", description="Plan Higgsfield generation jobs from scripts.")
    parser.add_argument("--input", default=None, help="override the scripts input path")
    parser.add_argument("--output-dir", default=None, help="override the output directory")
    parser.add_argument("--print", dest="do_print", action="store_true", help="print the planned jobs")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
