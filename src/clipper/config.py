"""Clipper configuration. Needs ANTHROPIC_API_KEY (see ``.env.example``)."""

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


MODEL: str = os.getenv("CLIPPER_MODEL", "claude-opus-4-8")
MAX_TOKENS: int = _env_int("CLIPPER_MAX_TOKENS", 16000)

# How many clips to pull from one source (the model may return fewer).
CLIPS_PER_RUN: int = _env_int("CLIPPER_CLIPS_PER_RUN", 5)

# Target clip length bounds (seconds).
CLIP_MIN_SECONDS: int = _env_int("CLIPPER_CLIP_MIN_SECONDS", 20)
CLIP_MAX_SECONDS: int = _env_int("CLIPPER_CLIP_MAX_SECONDS", 60)

# I/O paths.
TRANSCRIPT_INPUT: str = os.getenv("CLIPPER_TRANSCRIPT_INPUT", "data/clips/transcript.json")
OUTPUT_DIR: str = os.getenv("CLIPPER_OUTPUT_DIR", "data/clips")
