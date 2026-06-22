"""Niche filtering — keep only AI/tech items.

Sources like AI subreddits and AI RSS feeds are already on-topic, but the HN
front page and Google Trends are general, so every item is matched against a
keyword list. The matched keywords are also recorded on the item so downstream
agents (and humans reviewing the trend list) can see *why* it was kept.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from .models import TrendItem

# Lower-case keywords/phrases that mark an item as AI/tech. Word-boundary matched
# so "ai" doesn't match "said" or "maid".
KEYWORDS: tuple[str, ...] = (
    "ai",
    "a.i.",
    "artificial intelligence",
    "agi",
    "machine learning",
    "deep learning",
    "neural network",
    "llm",
    "large language model",
    "gpt",
    "chatgpt",
    "claude",
    "anthropic",
    "openai",
    "gemini",
    "deepmind",
    "google deepmind",
    "llama",
    "mistral",
    "grok",
    "copilot",
    "midjourney",
    "stable diffusion",
    "diffusion model",
    "generative ai",
    "genai",
    "transformer",
    "fine-tune",
    "fine-tuning",
    "rag",
    "retrieval augmented",
    "embedding",
    "agent",
    "agentic",
    "chatbot",
    "prompt",
    "inference",
    "nvidia",
    "gpu",
    "tensor",
    "hugging face",
    "huggingface",
    "model release",
    "benchmark",
    "multimodal",
    "text-to-video",
    "text-to-image",
    "image generation",
    "video generation",
    "neural",
    "machine vision",
    "computer vision",
    "robotics",
    "humanoid",
)

# Pre-compile one regex per keyword with word boundaries where it makes sense.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (kw, re.compile(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"))
    for kw in KEYWORDS
]


def matched_keywords(text: str) -> list[str]:
    """Return the keywords found in ``text`` (de-duplicated, in keyword order)."""
    if not text:
        return []
    haystack = text.lower()
    found: list[str] = []
    for kw, pattern in _PATTERNS:
        if pattern.search(haystack):
            found.append(kw)
    return found


def filter_niche(items: Iterable[TrendItem]) -> list[TrendItem]:
    """Keep only items that mention at least one niche keyword.

    Tags each kept item with the keywords it matched.
    """
    kept: list[TrendItem] = []
    for item in items:
        hits = matched_keywords(f"{item.title} {item.summary}")
        if hits:
            item.matched_keywords = hits
            kept.append(item)
    return kept
