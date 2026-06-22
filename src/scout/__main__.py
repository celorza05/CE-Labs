"""CLI entrypoint: ``python -m src.scout`` (run from the repo root).

Examples:
    python -m src.scout                 # fetch, rank, write data/trends/
    python -m src.scout --top 10        # keep only the top 10
    python -m src.scout --print         # also print the ranked list to stdout
    python -m src.scout --dry-run       # don't write files, just print
"""

from __future__ import annotations

import argparse
import logging

from . import config, pipeline


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="scout", description="Discover trending AI/tech topics.")
    parser.add_argument("--top", type=int, default=None, help="override how many trends to keep")
    parser.add_argument("--output-dir", default=None, help="override the output directory")
    parser.add_argument("--print", dest="do_print", action="store_true", help="print the ranked list")
    parser.add_argument("--dry-run", action="store_true", help="don't write files (implies --print)")
    parser.add_argument("--verbose", "-v", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def _print_items(items) -> None:
    for it in items:
        kws = ", ".join(it.matched_keywords[:4])
        print(f"{it.rank:>2}. [{it.score:.3f}] ({it.source}) {it.title}")
        print(f"     {it.url}")
        if kws:
            print(f"     keywords: {kws}")


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.top is not None:
        config.TOP_N = args.top

    if args.dry_run:
        items = pipeline.discover()
        _print_items(items)
        print(f"\n[dry-run] {len(items)} trends (not written)")
        return 0

    items, path = pipeline.run(output_dir=args.output_dir)
    if args.do_print:
        _print_items(items)
    print(f"\nWrote {len(items)} trends to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
