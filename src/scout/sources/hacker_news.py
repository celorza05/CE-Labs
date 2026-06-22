"""Hacker News via the free Algolia search API (no key required).

Combines the current front page with a recent keyword search so we catch both
what's hot right now and fresh AI stories that haven't climbed yet. Engagement
score = points + comments.
"""

from __future__ import annotations

from datetime import datetime, timezone

from ..models import TrendItem
from .http import get_json

_FRONT_PAGE = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=50"
_RECENT_AI = (
    "https://hn.algolia.com/api/v1/search_by_date"
    "?query=AI&tags=story&hitsPerPage=50"
)


def _hit_to_item(hit: dict) -> TrendItem | None:
    title = (hit.get("title") or hit.get("story_title") or "").strip()
    if not title:
        return None
    object_id = hit.get("objectID", "")
    url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
    points = hit.get("points") or 0
    comments = hit.get("num_comments") or 0

    published = None
    ts = hit.get("created_at_i")
    if ts:
        published = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    elif hit.get("created_at"):
        published = hit["created_at"]

    return TrendItem(
        title=title,
        url=url,
        source="hacker_news",
        raw_score=float(points + comments),
        published=published,
    )


def fetch() -> list[TrendItem]:
    items: list[TrendItem] = []
    for endpoint in (_FRONT_PAGE, _RECENT_AI):
        data = get_json(endpoint)
        for hit in data.get("hits", []):
            item = _hit_to_item(hit)
            if item is not None:
                items.append(item)
    return items
