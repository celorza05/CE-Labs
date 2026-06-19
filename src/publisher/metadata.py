"""Build platform metadata (title, description, tags) from a script."""

from __future__ import annotations

YT_TITLE_MAX = 100
YT_DESC_MAX = 4900  # API limit is 5000; leave headroom


def _hashtag_line(hashtags: list[str]) -> str:
    return " ".join("#" + h.lstrip("#") for h in hashtags if h)


def youtube_title(script: dict) -> str:
    title = (script.get("title") or script.get("source_title") or "Untitled").strip()
    return title[:YT_TITLE_MAX]


def youtube_description(script: dict) -> str:
    """Caption + hashtags + source + #Shorts (so YouTube treats it as a Short)."""
    parts: list[str] = []
    caption = (script.get("caption") or "").strip()
    if caption:
        parts.append(caption)
    tags_line = _hashtag_line(script.get("hashtags", []))
    if tags_line:
        parts.append(tags_line)
    url = (script.get("source_url") or "").strip()
    if url:
        parts.append(f"Source: {url}")
    parts.append("#Shorts")
    return "\n\n".join(parts)[:YT_DESC_MAX]


def youtube_tags(script: dict) -> list[str]:
    return [h.lstrip("#") for h in script.get("hashtags", []) if h]


def tiktok_caption(script: dict) -> str:
    """A single caption line for the manual TikTok hand-off."""
    caption = (script.get("caption") or script.get("title") or "").strip()
    tags_line = _hashtag_line(script.get("hashtags", []))
    return f"{caption}\n\n{tags_line}".strip()
