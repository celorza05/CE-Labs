"""Typed output schema for the Writer.

These Pydantic models are passed to the Anthropic API as a structured-output
format, so each generated script comes back as validated, typed fields rather
than a blob of text the next stage has to parse.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class VideoScript(BaseModel):
    """One short-form video, ready for the Producer (Higgsfield) stage."""

    source_title: str = Field(description="Title of the trend this is based on.")
    source_url: str = Field(description="URL of the source trend.")
    angle: str = Field(description="The sharp, specific take — why this matters / the hook idea in one line.")
    hook: str = Field(description="First ~3 seconds, on screen. Punchy, <= 12 words, stops the scroll.")
    script: str = Field(description="Full 30-60s voiceover / on-screen narration (~90-150 words). One idea, payoff at the end.")
    title: str = Field(description="Platform title for YouTube Shorts / TikTok.")
    caption: str = Field(description="Short social caption to accompany the post.")
    hashtags: list[str] = Field(description="5-8 relevant hashtags, without the # symbol.")
    b_roll_prompt: str = Field(
        description=(
            "A Higgsfield text-to-video prompt for faceless, vertical 9:16 B-roll: "
            "text-on-screen + abstract AI/tech visuals. No real people's likenesses, no brand logos."
        )
    )


class ScriptBatch(BaseModel):
    """The set of scripts the Writer chose to produce this run."""

    scripts: list[VideoScript] = Field(description="The selected, video-worthy scripts.")
