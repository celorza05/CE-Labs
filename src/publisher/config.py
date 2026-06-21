"""Publisher configuration. All env-overridable (see ``.env.example``)."""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# --- Inputs ---------------------------------------------------------------
JOBS_INPUT: str = os.getenv("PUBLISHER_JOBS_INPUT", "data/jobs/latest.json")
SCRIPTS_INPUT: str = os.getenv("PUBLISHER_SCRIPTS_INPUT", "data/scripts/latest.json")
PUBLISH_DIR: str = os.getenv("PUBLISHER_OUTPUT_DIR", "data/publish")

# Clips pipeline inputs (for `--clips` mode): the Clipper's metadata + the
# Cutter's output report.
CLIPS_INPUT: str = os.getenv("PUBLISHER_CLIPS_INPUT", "data/clips/clips.json")
CLIPS_REPORT: str = os.getenv("PUBLISHER_CLIPS_REPORT", "data/clips/out/report.json")

# --- YouTube (Data API v3) ------------------------------------------------
YOUTUBE_ENABLED: bool = _env_bool("PUBLISHER_YOUTUBE_ENABLED", True)
# OAuth client secret JSON downloaded from Google Cloud Console (Desktop app).
YOUTUBE_CLIENT_SECRET: str = os.getenv("PUBLISHER_YOUTUBE_CLIENT_SECRET", "client_secret.json")
# Where the cached OAuth token is stored after first login.
YOUTUBE_TOKEN_FILE: str = os.getenv("PUBLISHER_YOUTUBE_TOKEN_FILE", "data/publish/youtube_token.json")
# Default privacy — PRIVATE so nothing goes public by accident. Override per run.
YOUTUBE_PRIVACY: str = os.getenv("PUBLISHER_YOUTUBE_PRIVACY", "private")  # private | unlisted | public
# 28 = Science & Technology.
YOUTUBE_CATEGORY_ID: str = os.getenv("PUBLISHER_YOUTUBE_CATEGORY_ID", "28")
YOUTUBE_MADE_FOR_KIDS: bool = _env_bool("PUBLISHER_YOUTUBE_MADE_FOR_KIDS", False)

# --- TikTok (manual hand-off) ---------------------------------------------
TIKTOK_ENABLED: bool = _env_bool("PUBLISHER_TIKTOK_ENABLED", True)
