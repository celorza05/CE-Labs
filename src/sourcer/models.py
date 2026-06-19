"""Data model describing a sourced piece of long-form content."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class Source:
    """A long-form source ready for transcription."""

    title: str
    url: str  # original URL (or audio URL for podcasts); "" for local files
    source_type: str  # youtube | local | podcast
    media_path: str  # local path to the downloaded/referenced media file
    has_video: bool  # True if there's a video track to cut (False = audio-only)
    duration_seconds: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)
