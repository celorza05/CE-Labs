"""Podcast RSS source — pull an episode's audio from the publisher's feed."""

from __future__ import annotations

import logging
import os

from .. import config
from ..models import Source

log = logging.getLogger("sourcer.podcast")


def _audio_url(entry) -> str | None:
    for enc in entry.get("enclosures", []) or []:
        if "audio" in (enc.get("type") or "") and enc.get("href"):
            return enc["href"]
    for link in entry.get("links", []) or []:
        if link.get("rel") == "enclosure" and "audio" in (link.get("type") or ""):
            return link.get("href")
    return None


def _duration(entry) -> float:
    raw = entry.get("itunes_duration") or ""
    if not raw:
        return 0.0
    try:
        parts = [float(p) for p in str(raw).split(":")]
    except ValueError:
        return 0.0
    secs = 0.0
    for p in parts:
        secs = secs * 60 + p
    return secs


def fetch(feed_url: str, index: int | None = None) -> Source:
    try:
        import feedparser
    except ImportError as exc:
        raise RuntimeError("feedparser not installed. Install: pip install feedparser") from exc
    import requests

    idx = config.RSS_EPISODE_INDEX if index is None else index
    feed = feedparser.parse(feed_url)
    if not feed.entries:
        raise RuntimeError(f"no episodes found in feed: {feed_url}")
    if idx >= len(feed.entries):
        raise RuntimeError(f"episode index {idx} out of range ({len(feed.entries)} episodes)")

    entry = feed.entries[idx]
    audio_url = _audio_url(entry)
    if not audio_url:
        raise RuntimeError("could not find an audio enclosure in that episode")

    os.makedirs(config.MEDIA_DIR, exist_ok=True)
    ext = os.path.splitext(audio_url.split("?")[0])[1] or ".mp3"
    safe = "".join(c if c.isalnum() else "-" for c in entry.get("title", "episode"))[:50]
    dest = os.path.join(config.MEDIA_DIR, f"{safe}{ext}")

    log.info("downloading episode audio: %s", entry.get("title"))
    with requests.get(audio_url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                if chunk:
                    fh.write(chunk)

    return Source(
        title=entry.get("title", "Untitled episode"),
        url=audio_url,
        source_type="podcast",
        media_path=dest,
        has_video=False,
        duration_seconds=_duration(entry),
    )
