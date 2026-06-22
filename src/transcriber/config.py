"""Transcriber configuration. All env-overridable (see ``.env.example``)."""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Whisper model size: tiny | base | small | medium | large. Bigger = more
# accurate but slower and more memory. "base" is a good CPU default.
WHISPER_MODEL: str = os.getenv("TRANSCRIBER_WHISPER_MODEL", "base")
# Optional language hint (e.g. "en"); blank lets Whisper auto-detect.
LANGUAGE: str = os.getenv("TRANSCRIBER_LANGUAGE", "")

SOURCE_INPUT: str = os.getenv("TRANSCRIBER_SOURCE_INPUT", "data/clips/source.json")
OUTPUT: str = os.getenv("TRANSCRIBER_OUTPUT", "data/clips/transcript.json")
