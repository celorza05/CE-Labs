"""Reddit hot posts from AI subreddits.

Reddit blocks anonymous ``.json`` requests from many IPs (HTTP 403). If
``SCOUT_REDDIT_CLIENT_ID`` / ``SCOUT_REDDIT_CLIENT_SECRET`` are set (a free
"script" app at https://www.reddit.com/prefs/apps), Scout fetches via
authenticated OAuth, which is reliable. Otherwise it falls back to the public
endpoint and fails soft if that's blocked.

Engagement score = upvotes + comments. Stickied mod posts are skipped.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from .. import config
from ..models import TrendItem
from .http import session

log = logging.getLogger("scout.sources.reddit")


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


def _oauth_token() -> str | None:
    """Fetch an app-only OAuth token, or None if credentials aren't configured."""
    if not (config.REDDIT_CLIENT_ID and config.REDDIT_CLIENT_SECRET):
        return None
    resp = session().post(
        "https://www.reddit.com/api/v1/access_token",
        auth=(config.REDDIT_CLIENT_ID, config.REDDIT_CLIENT_SECRET),
        data={"grant_type": "client_credentials"},
        timeout=config.HTTP_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("access_token")


def _fetch_subreddit(subreddit: str, token: str | None) -> list[TrendItem]:
    if token:
        url = f"https://oauth.reddit.com/r/{subreddit}/hot?limit={config.REDDIT_LIMIT}"
        headers = {"Authorization": f"bearer {token}"}
    else:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={config.REDDIT_LIMIT}"
        headers = {}

    resp = session().get(url, headers=headers, timeout=config.HTTP_TIMEOUT)
    resp.raise_for_status()
    children = resp.json().get("data", {}).get("children", [])
    items = [_post_to_item(subreddit, post) for post in children]
    return [it for it in items if it is not None]


def fetch() -> list[TrendItem]:
    token = _oauth_token()
    if token is None:
        log.info("no Reddit OAuth credentials; using public endpoint (may be blocked)")

    items: list[TrendItem] = []
    for subreddit in config.SUBREDDITS:
        try:
            items.extend(_fetch_subreddit(subreddit, token))
        except Exception as exc:  # one bad subreddit shouldn't drop the rest
            log.warning("r/%s failed: %s", subreddit, exc)
    return items
