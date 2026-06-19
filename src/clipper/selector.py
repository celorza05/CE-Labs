"""The Clipper pipeline: load transcript -> select clips -> write clips.json."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from . import config
from .models import Clip, ClipBatch
from .prompts import build_user_prompt, system_prompt

log = logging.getLogger("clipper")


def load_transcript(path: str | None = None) -> dict:
    p = path or config.TRANSCRIPT_INPUT
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"transcript not found: {p}. Produce one with the Transcriber first."
        )
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def _valid(clip: Clip) -> bool:
    length = clip.end_seconds - clip.start_seconds
    return clip.start_seconds >= 0 and length > 0


def select(transcript: dict) -> list[Clip]:
    """Call the Anthropic API to choose the best clips from the transcript."""
    import anthropic

    segments = transcript.get("segments", [])
    if not segments:
        raise ValueError("transcript has no segments — nothing to clip")

    client = anthropic.Anthropic()
    log.info("asking %s to find the best %d clips from %d segments",
             config.MODEL, config.CLIPS_PER_RUN, len(segments))

    response = client.messages.parse(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=system_prompt(config.CLIPS_PER_RUN, config.CLIP_MIN_SECONDS, config.CLIP_MAX_SECONDS),
        messages=[{
            "role": "user",
            "content": build_user_prompt(transcript, config.CLIPS_PER_RUN,
                                         config.CLIP_MIN_SECONDS, config.CLIP_MAX_SECONDS),
        }],
        output_format=ClipBatch,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("the model refused this request; nothing selected")
    batch = response.parsed_output
    if batch is None:
        raise RuntimeError(f"no structured output returned (stop_reason={response.stop_reason})")

    clips = [c for c in batch.clips if _valid(c)]
    return clips[: config.CLIPS_PER_RUN]


def _payload(transcript: dict, clips: list[Clip]) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": transcript.get("source", {}),
        "model": config.MODEL,
        "count": len(clips),
        "clips": [c.model_dump() for c in clips],
    }


def write_clips(transcript: dict, clips: list[Clip], output_dir: str | None = None) -> str:
    out_dir = output_dir or config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    payload = _payload(transcript, clips)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dated = os.path.join(out_dir, f"clips-{stamp}.json")
    latest = os.path.join(out_dir, "clips.json")
    for path in (dated, latest):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
    log.info("wrote %d clips to %s (and clips.json)", len(clips), dated)
    return dated


def run(input_path: str | None = None, output_dir: str | None = None) -> tuple[list[Clip], str]:
    transcript = load_transcript(input_path)
    clips = select(transcript)
    path = write_clips(transcript, clips, output_dir)
    return clips, path
