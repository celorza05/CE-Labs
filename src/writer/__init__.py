"""Writer — turns Scout trends into short-form scripts + Higgsfield prompts.

Reads ``data/trends/latest.json`` (the Scout's output), judges which trends are
genuinely video-worthy, and writes punchy hook + script + Higgsfield B-roll
prompt for the strongest ones to ``data/scripts/``.

See ``PIPELINE.md`` (repo root) for how the Writer fits the wider pipeline.
"""

from .models import ScriptBatch, VideoScript

__all__ = ["ScriptBatch", "VideoScript"]
