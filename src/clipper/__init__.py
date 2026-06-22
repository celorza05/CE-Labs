"""Clipper — picks the best short-form moments from a long-form transcript.

The "brain" of the clips pipeline (see ``CLIPS.md``). Reads a timestamped
transcript (whatever the Transcriber produces) and asks Claude to select the
most rewatchable, self-contained 20-60s moments, returning precise start/end
timestamps plus a hook, title, caption, and hashtags for each. The Cutter then
uses those timestamps to cut the real footage.
"""

from .models import Clip, ClipBatch

__all__ = ["Clip", "ClipBatch"]
