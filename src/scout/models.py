"""Data model shared across the Scout pipeline."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

_WORD_RE = re.compile(r"[^a-z0-9]+")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TrendItem:
    """A single trending topic discovered by one of the sources.

    Fields up to ``summary`` are populated by the source fetchers; the fields
    below them are filled in later by the filtering and ranking stages.
    """

    title: str
    url: str
    source: str  # e.g. "hacker_news", "reddit:LocalLLaMA", "rss:The Verge"
    raw_score: float = 0.0  # source-native engagement (HN points, Reddit upvotes…)
    published: str | None = None  # ISO-8601 timestamp if the source provides one
    summary: str = ""

    # Populated by later stages:
    matched_keywords: list[str] = field(default_factory=list)
    engagement_norm: float = 0.0  # 0..1 within the source family
    recency_norm: float = 0.0  # 0..1, newer is higher
    score: float = 0.0  # final ranking score
    rank: int = 0

    fetched_at: str = field(default_factory=_now_iso)

    @property
    def source_family(self) -> str:
        """The broad source bucket (``reddit:LocalLLaMA`` -> ``reddit``)."""
        return self.source.split(":", 1)[0]

    def canonical_url(self) -> str:
        """URL stripped of query/fragment and lower-cased host, for de-duping."""
        if not self.url:
            return ""
        parts = urlsplit(self.url)
        host = parts.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        path = parts.path.rstrip("/")
        return urlunsplit((parts.scheme.lower(), host, path, "", ""))

    def title_key(self) -> str:
        """Normalised title (lower-case, alphanumeric only) for de-duping."""
        return _WORD_RE.sub(" ", self.title.lower()).strip()

    def to_dict(self) -> dict:
        return asdict(self)
