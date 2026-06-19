"""Local file source — a video/audio file a creator gave you."""

from __future__ import annotations

import json
import logging
import os
import subprocess

from ..models import Source

log = logging.getLogger("sourcer.local")

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}


def probe_duration(path: str) -> float:
    """Duration via ffprobe; 0.0 if ffprobe isn't available."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode == 0:
            return float(json.loads(out.stdout)["format"]["duration"])
    except Exception as exc:  # ffprobe missing or unparsable — non-fatal
        log.debug("ffprobe failed for %s: %s", path, exc)
    return 0.0


def fetch(path: str) -> Source:
    if not os.path.exists(path):
        raise FileNotFoundError(f"file not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    title = os.path.splitext(os.path.basename(path))[0]
    return Source(
        title=title,
        url="",
        source_type="local",
        media_path=os.path.abspath(path),
        has_video=ext in VIDEO_EXTS,
        duration_seconds=probe_duration(path),
    )
