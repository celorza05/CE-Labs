"""Transcribe a source's media with local Whisper -> transcript.json."""

from __future__ import annotations

import json
import logging
import os

from . import config

log = logging.getLogger("transcriber")


def load_source(path: str | None = None) -> dict:
    p = path or config.SOURCE_INPUT
    if not os.path.exists(p):
        raise FileNotFoundError(f"source not found: {p}. Run the Sourcer first.")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def segments_from_result(result: dict) -> list[dict]:
    """Convert a Whisper result into the Clipper's segment schema."""
    segments = []
    for s in result.get("segments", []):
        text = (s.get("text") or "").strip()
        if not text:
            continue
        segments.append({
            "start": round(float(s.get("start", 0.0)), 2),
            "end": round(float(s.get("end", 0.0)), 2),
            "text": text,
        })
    return segments


def build_transcript(source: dict, result: dict) -> dict:
    return {
        "source": {
            "title": source.get("title", "Untitled"),
            "url": source.get("url", ""),
            "duration_seconds": source.get("duration_seconds", 0),
        },
        "segments": segments_from_result(result),
    }


def transcribe(source: dict) -> dict:
    """Run Whisper locally on the source media and return a transcript dict."""
    try:
        import whisper
    except ImportError as exc:
        raise RuntimeError(
            "openai-whisper not installed. Install: pip install -r requirements-clips.txt "
            "(also needs ffmpeg on PATH)."
        ) from exc

    media = source.get("media_path")
    if not media or not os.path.exists(media):
        raise FileNotFoundError(f"media file not found: {media}")

    log.info("loading Whisper model %r (first run downloads it)", config.WHISPER_MODEL)
    model = whisper.load_model(config.WHISPER_MODEL)

    kwargs = {"verbose": False}
    if config.LANGUAGE.strip():
        kwargs["language"] = config.LANGUAGE.strip()

    log.info("transcribing %s", os.path.basename(media))
    result = model.transcribe(media, **kwargs)
    return build_transcript(source, result)


def write_transcript(transcript: dict, output: str | None = None) -> str:
    path = output or config.OUTPUT
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(transcript, fh, indent=2, ensure_ascii=False)
    return path


def run(source_path: str | None = None, output: str | None = None):
    source = load_source(source_path)
    transcript = transcribe(source)
    path = write_transcript(transcript, output)
    log.info("transcribed %d segments -> %s", len(transcript["segments"]), path)
    return transcript, path
