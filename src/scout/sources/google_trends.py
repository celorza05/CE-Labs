"""Google Trends via the official Trending Now RSS feed.

We used to use ``pytrends`` (an unofficial scraper), but its endpoints break
often — it was returning HTTP 404. Google publishes a real RSS feed of trending
searches per region, which is stable and needs no library beyond ``feedparser``.

The feed is general (all topics), so the niche filter downstream keeps only the
AI/tech ones. Trends carry no engagement number and no reliable timestamp, so
they rank on source weight and a neutral recency.
"""

from __future__ import annotations

import logging

from .. import config
from ..models import TrendItem
from .http import session

log = logging.getLogger("scout.sources.google_trends")


def fetch() -> list[TrendItem]:
    try:
        import feedparser
    except ImportError:
        log.warning("feedparser not installed; skipping Google Trends")
        return []

    url = f"https://trends.google.com/trending/rss?geo={config.GOOGLE_TRENDS_GEO}"
    try:
        resp = session().get(url, timeout=config.HTTP_TIMEOUT)
        resp.raise_for_status()
    except Exception as exc:
        log.warning("Google Trends request failed: %s", exc)
        return []

    feed = feedparser.parse(resp.content)
    items: list[TrendItem] = []
    for entry in feed.entries:
        title = (entry.get("title") or "").strip()
        if not title:
            continue
        # The feed nests related news headlines; fold them into the summary so
        # the niche filter has more text to match against.
        news_titles = [
            n.get("ht_news_item_title", "")
            for n in entry.get("ht_news_item", [])
            if isinstance(n, dict)
        ]
        summary = "; ".join(t for t in news_titles if t)
        query = title.replace(" ", "+")
        items.append(
            TrendItem(
                title=title,
                url=f"https://trends.google.com/trends/explore?q={query}&geo={config.GOOGLE_TRENDS_GEO}",
                source="google_trends",
                raw_score=0.0,
                summary=summary,
            )
        )
    return items
