"""Scout — the trend-discovery agent for the CE-Labs content pipeline.

Pulls trending AI/tech topics from several sources, filters them to the niche,
ranks and de-duplicates them, and writes the result to ``data/trends/``.

See ``PIPELINE.md`` (repo root) for how Scout fits into the wider pipeline.
"""

from .models import TrendItem

__all__ = ["TrendItem"]
