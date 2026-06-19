"""Reddit hot posts via the public ``.json`` endpoints (no auth for basic read).

Reddit rate-limits/blocks anonymous requests without a descriptive User-Agent,
so the shared session sets one. Engagement score = upvotes + comments. Stickied
mod posts are skipped.
"""

from __future__ import annotations

from datetime import datetime, timezone

from .. import config
from ..models import TrendItem
from .http import get_json


def _post_to_item(subreddit: str, post: dict) -> TrendItem | None:
    data = post.get("data", {})
    if data.get("stickied"):
        return None
    title = (data.get("title") or "").strip()
    if not title:
        return None

    permalink = data.get("permalink", "")
    discussion_url = f"https://www.reddit.com{permalink}" if permalink else ""
    # Prefer the linked article; fall back to the reddit discussion.
    url = data.get("url_overridden_by_dest") or data.get("url") or discussion_url

    score = data.get("score") or 0
    comments = data.get("num_comments") or 0

    published = None
    created = data.get("created_utc")
    if created:
        published = datetime.fromtimestamp(created, tz=timezone.utc).isoformat()

    summary = (data.get("selftext") or "")[:500]

    return TrendItem(
        title=title,
        url=url,
        source=f"reddit:{subreddit}",
        raw_score=float(score + comments),
        published=published,
        summary=summary,
    )


def fetch() -> list[TrendItem]:
    items: list[TrendItem] = []
    for subreddit in config.SUBREDDITS:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={config.REDDIT_LIMIT}"
        data = get_json(url)
        children = data.get("data", {}).get("children", [])
        for post in children:
            item = _post_to_item(subreddit, post)
            if item is not None:
                items.append(item)
    return items
