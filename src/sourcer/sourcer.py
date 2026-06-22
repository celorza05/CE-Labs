"""Dispatch a source input to the right backend and write source.json."""

from __future__ import annotations

import json
import logging
import os

from . import config
from .backends import local, podcast, youtube
from .models import Source

log = logging.getLogger("sourcer")


def detect_type(inp: str) -> str:
    """Guess the source type from the input string."""
    if os.path.exists(inp):
        return "local"
    low = inp.lower()
    if "youtube.com" in low or "youtu.be" in low:
        return "youtube"
    if low.endswith((".rss", ".xml")) or "/rss" in low or "/feed" in low:
        return "podcast"
    # yt-dlp supports many video sites, so default there for other URLs.
    return "youtube"


def fetch(inp: str, source_type: str | None = None, episode: int | None = None) -> Source:
    stype = source_type or detect_type(inp)
    log.info("sourcing (%s): %s", stype, inp)
    if stype == "local":
        return local.fetch(inp)
    if stype == "podcast":
        return podcast.fetch(inp, episode)
    if stype == "youtube":
        return youtube.fetch(inp)
    raise ValueError(f"unknown source type: {stype}")


def write_source(source: Source, output: str | None = None) -> str:
    path = output or config.OUTPUT
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(source.to_dict(), fh, indent=2, ensure_ascii=False)
    return path


def run(inp: str, source_type: str | None = None, episode: int | None = None, output: str | None = None):
    source = fetch(inp, source_type, episode)
    path = write_source(source, output)
    log.info("sourced %r (%s, %.0fs) -> %s", source.title, source.source_type, source.duration_seconds, path)
    return source, path
