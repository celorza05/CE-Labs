"""Typed output schema for the Clipper (structured outputs)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Clip(BaseModel):
    """One short-form clip selected from the source, by timestamp."""

    start_seconds: float = Field(description="Clip start time in seconds from the source start.")
    end_seconds: float = Field(description="Clip end time in seconds. Should be 20-60s after start.")
    hook: str = Field(description="On-screen hook for the first ~2 seconds. Punchy, <= 12 words.")
    title: str = Field(description="Platform title for YouTube Shorts / TikTok.")
    caption: str = Field(description="Short social caption.")
    hashtags: list[str] = Field(description="5-8 relevant hashtags, without the # symbol.")
    reason: str = Field(description="Why this moment will perform as a standalone clip.")


class ClipBatch(BaseModel):
    """The set of clips the Clipper chose from one source."""

    clips: list[Clip] = Field(description="The selected clips, strongest first.")
