"""Sourcer — fetch long-form content for the clips pipeline.

Takes a YouTube URL, a local file, or a podcast RSS feed and produces a
``data/clips/source.json`` descriptor (title, media path, duration, whether it
has a video track) for the Transcriber.

Use only content you're permitted to use — see ``CLIPS.md``.
"""

from .models import Source

__all__ = ["Source"]
