"""YouTube (and other yt-dlp-supported sites) via yt-dlp.

Note: downloading from YouTube is restricted by its Terms of Service regardless
of who owns the content — use this only for content you're permitted to use, and
prefer creator-provided files where possible.
"""

from __future__ import annotations

import logging
import os

from .. import config
from ..models import Source

log = logging.getLogger("sourcer.youtube")


def fetch(url: str) -> Source:
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError("yt-dlp not installed. Install: pip install yt-dlp") from exc

    os.makedirs(config.MEDIA_DIR, exist_ok=True)
    opts = {
        "format": config.YTDLP_FORMAT,
        "outtmpl": os.path.join(config.MEDIA_DIR, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = _resolve_path(ydl, info)

    return Source(
        title=info.get("title", "Untitled"),
        url=url,
        source_type="youtube",
        media_path=path,
        has_video=True,
        duration_seconds=float(info.get("duration") or 0),
    )


def _resolve_path(ydl, info) -> str:
    """Find the final file path after any merge."""
    downloads = info.get("requested_downloads") or []
    if downloads and downloads[0].get("filepath"):
        return downloads[0]["filepath"]
    # Fallback: prepared name with the merged extension.
    base = ydl.prepare_filename(info)
    root, _ = os.path.splitext(base)
    for ext in (".mp4", ".mkv", ".webm"):
        if os.path.exists(root + ext):
            return root + ext
    return base
