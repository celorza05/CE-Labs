"""The Writer pipeline: load trends -> generate scripts -> write output."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from . import config
from .models import ScriptBatch, VideoScript
from .prompts import build_user_prompt, system_prompt

log = logging.getLogger("writer")

NICHE = "AI/tech news & tool breakdowns"


def load_trends(path: str | None = None) -> list[dict]:
    """Read the Scout's ranked trends from latest.json."""
    p = path or config.TRENDS_INPUT
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"trends file not found: {p}. Run the Scout first (python -m src.scout)."
        )
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("items", [])


def generate(trends: list[dict]) -> list[VideoScript]:
    """Call the Anthropic API to turn candidate trends into scripts."""
    import anthropic

    candidates = trends[: config.CANDIDATE_POOL]
    if not candidates:
        raise ValueError("no trends to write from — run the Scout first")

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env / .env
    log.info("asking %s to script the best %d of %d trends", config.MODEL, config.SCRIPTS_PER_RUN, len(candidates))

    response = client.messages.parse(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=system_prompt(config.VOICE, config.SCRIPTS_PER_RUN),
        messages=[{"role": "user", "content": build_user_prompt(candidates, config.SCRIPTS_PER_RUN)}],
        output_format=ScriptBatch,
    )

    if response.stop_reason == "refusal":
        raise RuntimeError("the model refused this request; nothing generated")
    batch = response.parsed_output
    if batch is None:
        raise RuntimeError(f"no structured output returned (stop_reason={response.stop_reason})")

    return batch.scripts[: config.SCRIPTS_PER_RUN]


def _payload(scripts: list[VideoScript]) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "niche": NICHE,
        "voice": config.VOICE,
        "model": config.MODEL,
        "count": len(scripts),
        "scripts": [s.model_dump() for s in scripts],
    }


def write_output(scripts: list[VideoScript], output_dir: str | None = None) -> str:
    """Write scripts to a timestamped file plus latest.json. Returns the dated path."""
    out_dir = output_dir or config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    payload = _payload(scripts)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dated_path = os.path.join(out_dir, f"scripts-{stamp}.json")
    latest_path = os.path.join(out_dir, "latest.json")

    for path in (dated_path, latest_path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    log.info("wrote %d scripts to %s (and latest.json)", len(scripts), dated_path)
    return dated_path


def run(input_path: str | None = None, output_dir: str | None = None) -> tuple[list[VideoScript], str]:
    trends = load_trends(input_path)
    scripts = generate(trends)
    path = write_output(scripts, output_dir)
    return scripts, path
