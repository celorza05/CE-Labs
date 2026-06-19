"""Transcriber — local Whisper audio -> timestamped transcript.

Reads ``data/clips/source.json`` (from the Sourcer), runs OpenAI Whisper locally
to transcribe the media, and writes ``data/clips/transcript.json`` in the schema
the Clipper consumes. Free (no per-use cost); needs ``ffmpeg`` and a one-time
model download.
"""
