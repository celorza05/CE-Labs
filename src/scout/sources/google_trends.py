"""Google Trends via ``pytrends`` (unofficial).

pytrends scrapes an undocumented endpoint, so it's the flakiest source: it can
rate-limit (HTTP 429) or change shape without notice. It is therefore optional
and fails soft — if pytrends isn't installed or the request fails, we log and
return nothing rather than breaking the run.

We pull the realtime trending stories for the configured region; the niche
filter downstream keeps only the AI/tech ones. Trends have no engagement number
and no per-item timestamp, so they rank on source weight and a neutral recency.
"""

from __future__ import annotations

import logging

from .. import config
from ..models import TrendItem

log = logging.getLogger("scout.sources.google_trends")


def fetch() -> list[TrendItem]:
    try:
        from pytrends.request import TrendReq
    except ImportError:
        log.warning("pytrends not installed; skipping Google Trends")
        return []

    try:
        pytrends = TrendReq(hl="en-US", tz=0)
        df = pytrends.realtime_trending_searches(pn=config.GOOGLE_TRENDS_GEO)
    except Exception as exc:  # network / rate-limit / API drift
        log.warning("Google Trends request failed: %s", exc)
        return []

    items: list[TrendItem] = []
    for _, row in df.iterrows():
        title = str(row.get("title", "")).strip()
        if not title:
            continue
        entity_names = row.get("entityNames")
        summary = ", ".join(entity_names) if isinstance(entity_names, list) else ""
        query = title.replace(" ", "+")
        items.append(
            TrendItem(
                title=title,
                url=f"https://trends.google.com/trends/explore?q={query}",
                source="google_trends",
                raw_score=0.0,
                summary=summary,
            )
        )
    return items
