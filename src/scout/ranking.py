"""Ranking and de-duplication.

Each source uses a different engagement scale (HN points vs. Reddit upvotes vs.
RSS, which has none), so raw scores are normalised *within* their source family
before being blended with a freshness score and a per-source trust weight.
"""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone

from . import config
from .models import TrendItem


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _recency_norm(published: str | None, now: datetime) -> float:
    """Exponential decay on age; items with no date get a neutral 0.5."""
    dt = _parse_dt(published)
    if dt is None:
        return 0.5
    age_hours = max(0.0, (now - dt).total_seconds() / 3600.0)
    # Half-life style decay: value halves every RECENCY_HALFLIFE_HOURS.
    return math.pow(0.5, age_hours / config.RECENCY_HALFLIFE_HOURS)


def _normalise_engagement(items: list[TrendItem]) -> None:
    """Set ``engagement_norm`` (0..1) within each source family."""
    by_family: dict[str, list[TrendItem]] = defaultdict(list)
    for item in items:
        by_family[item.source_family].append(item)

    for family_items in by_family.values():
        max_raw = max((it.raw_score for it in family_items), default=0.0)
        for it in family_items:
            # Families without an engagement signal (RSS, trends) get 0.5 so they
            # are ranked purely on freshness and source weight.
            it.engagement_norm = (it.raw_score / max_raw) if max_raw > 0 else 0.5


def rank(items: list[TrendItem]) -> list[TrendItem]:
    """De-duplicate, score, sort, trim to TOP_N, and assign ranks."""
    now = datetime.now(timezone.utc)
    _normalise_engagement(items)

    for item in items:
        item.recency_norm = _recency_norm(item.published, now)
        weight = config.SOURCE_WEIGHTS.get(item.source_family, 0.5)
        blended = (
            config.ENGAGEMENT_WEIGHT * item.engagement_norm
            + config.RECENCY_WEIGHT * item.recency_norm
        )
        item.score = round(weight * blended, 6)

    # Highest score first so de-dup keeps the strongest copy of a topic.
    items.sort(key=lambda it: it.score, reverse=True)

    deduped = _dedupe(items)
    top = deduped[: config.TOP_N]
    for i, item in enumerate(top, start=1):
        item.rank = i
    return top


def _dedupe(items: list[TrendItem]) -> list[TrendItem]:
    """Drop later items sharing a canonical URL or a normalised title."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    result: list[TrendItem] = []
    for item in items:
        url_key = item.canonical_url()
        title_key = item.title_key()
        if url_key and url_key in seen_urls:
            continue
        if title_key and title_key in seen_titles:
            continue
        if url_key:
            seen_urls.add(url_key)
        if title_key:
            seen_titles.add(title_key)
        result.append(item)
    return result
