"""Trend sources. Each module exposes a ``fetch() -> list[TrendItem]``.

Sources fail soft: a network error or bad response logs a warning and yields an
empty list rather than crashing the whole run, so one dead source never blocks
the others.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from .. import config
from ..models import TrendItem
from . import google_trends, hacker_news, reddit, rss

log = logging.getLogger("scout.sources")

# (enabled-flag, human label, fetch callable)
_REGISTRY: list[tuple[bool, str, Callable[[], list[TrendItem]]]] = [
    (config.ENABLE_HACKER_NEWS, "Hacker News", hacker_news.fetch),
    (config.ENABLE_REDDIT, "Reddit", reddit.fetch),
    (config.ENABLE_RSS, "RSS", rss.fetch),
    (config.ENABLE_GOOGLE_TRENDS, "Google Trends", google_trends.fetch),
]


def fetch_all() -> list[TrendItem]:
    """Run every enabled source and concatenate their items."""
    items: list[TrendItem] = []
    for enabled, label, fetch in _REGISTRY:
        if not enabled:
            log.info("%s disabled, skipping", label)
            continue
        try:
            found = fetch()
        except Exception as exc:  # defensive: never let one source kill the run
            log.warning("%s failed: %s", label, exc)
            continue
        log.info("%s returned %d items", label, len(found))
        items.extend(found)
    return items
