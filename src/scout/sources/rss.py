"""RSS feeds from AI news sites, parsed with ``feedparser``.

RSS has no engagement signal, so these items are ranked on freshness and source
weight (handled in ranking.py). Entry summaries are kept so the niche filter and
the downstream Writer have context to work with.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from time import mktime

from .. import config
from ..models import TrendItem

log = logging.getLogger("scout.sources.rss")


def _entry_published(entry) -> str | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(mktime(parsed), tz=timezone.utc).isoformat()


def _feed_label(feed) -> str:
    title = getattr(feed, "feed", {}).get("title")
    return title.strip() if title else "feed"


def fetch() -> list[TrendItem]:
    try:
        import feedparser
    except ImportError:
        log.warning("feedparser not installed; skipping RSS feeds")
        return []

    items: list[TrendItem] = []
    for feed_url in config.RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        if feed.bozo and not feed.entries:
            log.warning("could not parse feed %s: %s", feed_url, feed.bozo_exception)
            continue
        label = _feed_label(feed)
        for entry in feed.entries:
            title = (entry.get("title") or "").strip()
            link = entry.get("link") or ""
            if not title or not link:
                continue
            summary = (entry.get("summary") or "")[:500]
            items.append(
                TrendItem(
                    title=title,
                    url=link,
                    source=f"rss:{label}",
                    raw_score=0.0,
                    published=_entry_published(entry),
                    summary=summary,
                )
            )
    return items
