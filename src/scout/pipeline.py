"""The Scout pipeline: fetch -> filter -> rank -> write."""

from __future__ import annotations

import json
import logging
import os
from collections import Counter
from datetime import datetime, timezone

from . import config, sources
from .filters import filter_niche
from .models import TrendItem
from .ranking import rank

log = logging.getLogger("scout")

NICHE = "AI/tech news & tool breakdowns"


def discover() -> list[TrendItem]:
    """Run the full discovery pipeline and return the ranked trends."""
    raw = sources.fetch_all()
    log.info("fetched %d raw items", len(raw))

    on_topic = filter_niche(raw)
    log.info("%d items passed the niche filter", len(on_topic))

    ranked = rank(on_topic)
    log.info("kept top %d after ranking and de-dup", len(ranked))
    return ranked


def _payload(items: list[TrendItem]) -> dict:
    family_counts = Counter(it.source_family for it in items)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "niche": NICHE,
        "count": len(items),
        "sources": dict(family_counts),
        "items": [it.to_dict() for it in items],
    }


def write_output(items: list[TrendItem], output_dir: str | None = None) -> str:
    """Write the ranked trends to a timestamped file plus ``latest.json``.

    Returns the path of the timestamped file.
    """
    out_dir = output_dir or config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    payload = _payload(items)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dated_path = os.path.join(out_dir, f"trends-{stamp}.json")
    latest_path = os.path.join(out_dir, "latest.json")

    for path in (dated_path, latest_path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    log.info("wrote %d trends to %s (and latest.json)", len(items), dated_path)
    return dated_path


def run(output_dir: str | None = None) -> tuple[list[TrendItem], str]:
    items = discover()
    path = write_output(items, output_dir)
    return items, path
