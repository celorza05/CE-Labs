"""Sourcer configuration. All env-overridable (see ``.env.example``)."""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


# Where downloaded media is stored, and where the source descriptor is written.
MEDIA_DIR: str = os.getenv("SOURCER_MEDIA_DIR", "data/clips/media")
OUTPUT: str = os.getenv("SOURCER_OUTPUT", "data/clips/source.json")

# yt-dlp format selection (cap height to keep files reasonable; vertical crop
# happens later in the Cutter).
YTDLP_FORMAT: str = os.getenv(
    "SOURCER_YTDLP_FORMAT",
    "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
)

# Which podcast episode to pull (0 = newest).
RSS_EPISODE_INDEX: int = _env_int("SOURCER_RSS_EPISODE_INDEX", 0)
