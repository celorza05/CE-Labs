"""Data model for a Higgsfield generation job.

A job is a self-contained unit of work: everything the submission step needs to
generate one video, plus the metadata to tie the finished asset back to its
script. The Higgsfield-specific parameter names are mapped at submission time
(once the access method is confirmed); this model stays generic.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(text: str, max_len: int = 50) -> str:
    """A filesystem-safe slug from a title (for job ids and asset filenames)."""
    slug = _SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:max_len].strip("-") or "untitled"


@dataclass
class GenerationJob:
    """One video to generate from a script's B-roll prompt."""

    job_id: str  # stable id, e.g. "01-photoshop-now-has-a-chatbot"
    source_title: str
    source_url: str
    prompt: str  # the script's b_roll_prompt — the actual generation prompt
    aspect_ratio: str = "9:16"
    duration_seconds: int = 5
    model: str = ""  # Higgsfield model; resolved at submission if blank

    # Carried through so the asset can be matched to its script downstream:
    script_title: str = ""  # the platform title from the Writer
    hook: str = ""

    # Filled in by the submission step:
    status: str = "pending"  # pending | submitted | completed | failed
    higgsfield_job_id: str | None = None
    asset_url: str | None = None
    error: str | None = None

    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return asdict(self)
