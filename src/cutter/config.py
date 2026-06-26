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
# A speaker switch is detected when the face jumps more than this fraction of the
# frame width (and stays). Big enough to ignore jitter, small enough to catch a
# left<->right camera cut.
REFRAME_JUMP_FRACTION: float = float(os.getenv("CUTTER_REFRAME_JUMP_FRACTION", "0.15"))
# Minimum seconds a shot must hold before it counts as a real switch. Brief
# blips (a quick cut back to the other speaker for a second) are merged into the
# surrounding shot so the vertical crop doesn't flicker on fast back-and-forth.
REFRAME_MIN_SHOT_SECONDS: float = float(os.getenv("CUTTER_REFRAME_MIN_SHOT_SECONDS", "1.5"))

# Output canvas (vertical 9:16).
WIDTH: int = _env_int("CUTTER_WIDTH", 1080)
HEIGHT: int = _env_int("CUTTER_HEIGHT", 1920)
# Constant output frame rate. YouTube sources are often VFR; forcing CFR avoids
# the "first few seconds play in slow motion" artifact on upload.
FPS: int = _env_int("CUTTER_FPS", 30)

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
