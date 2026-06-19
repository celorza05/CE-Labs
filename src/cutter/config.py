"""Cutter configuration. All env-overridable (see ``.env.example``)."""

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


FFMPEG_BIN: str = os.getenv("CUTTER_FFMPEG_BIN", "ffmpeg")

# Reframing: "center" (fixed center-crop) or "face" (follow the speaker's face
# via OpenCV). Face mode needs opencv-python.
REFRAME: str = os.getenv("CUTTER_REFRAME", "center")
REFRAME_SAMPLE_FPS: float = float(os.getenv("CUTTER_REFRAME_SAMPLE_FPS", "2.0"))

# Output canvas (vertical 9:16).
WIDTH: int = _env_int("CUTTER_WIDTH", 1080)
HEIGHT: int = _env_int("CUTTER_HEIGHT", 1920)

# Caption styling (burned in via ASS).
FONT_NAME: str = os.getenv("CUTTER_FONT_NAME", "Arial")
FONT_SIZE: int = _env_int("CUTTER_FONT_SIZE", 72)

# Background colour for audio-only sources (podcasts have no video track).
BG_COLOR: str = os.getenv("CUTTER_BG_COLOR", "black")

# Seconds before ffmpeg is killed per clip.
TIMEOUT: int = _env_int("CUTTER_TIMEOUT", 600)

# I/O.
CLIPS_INPUT: str = os.getenv("CUTTER_CLIPS_INPUT", "data/clips/clips.json")
SOURCE_INPUT: str = os.getenv("CUTTER_SOURCE_INPUT", "data/clips/source.json")
TRANSCRIPT_INPUT: str = os.getenv("CUTTER_TRANSCRIPT_INPUT", "data/clips/transcript.json")
OUTPUT_DIR: str = os.getenv("CUTTER_OUTPUT_DIR", "data/clips/out")
