"""Build the generation plan: scripts -> jobs -> data/jobs/latest.json."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from . import config
from .models import GenerationJob, slugify

log = logging.getLogger("producer")


def load_scripts(path: str | None = None) -> list[dict]:
    """Read the Writer's scripts from latest.json."""
    p = path or config.SCRIPTS_INPUT
    if not os.path.exists(p):
        raise FileNotFoundError(
            f"scripts file not found: {p}. Run the Writer first (python -m src.writer)."
        )
    with open(p, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get("scripts", [])


def build_plan(scripts: list[dict]) -> list[GenerationJob]:
    """Turn each script's b_roll_prompt into a generation job."""
    jobs: list[GenerationJob] = []
    for i, s in enumerate(scripts, start=1):
        prompt = (s.get("b_roll_prompt") or "").strip()
        if not prompt:
            log.warning("script %d has no b_roll_prompt; skipping", i)
            continue
        title = s.get("title", "") or s.get("source_title", "")
        jobs.append(
            GenerationJob(
                job_id=f"{i:02d}-{slugify(title)}",
                source_title=s.get("source_title", ""),
                source_url=s.get("source_url", ""),
                prompt=prompt,
                aspect_ratio=config.ASPECT_RATIO,
                duration_seconds=config.DURATION_SECONDS,
                model=config.MODEL,
                script_title=title,
                hook=s.get("hook", ""),
            )
        )
    return jobs


def _payload(jobs: list[GenerationJob]) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(jobs),
        "defaults": {
            "aspect_ratio": config.ASPECT_RATIO,
            "duration_seconds": config.DURATION_SECONDS,
            "model": config.MODEL or None,
        },
        "jobs": [j.to_dict() for j in jobs],
    }


def write_plan(jobs: list[GenerationJob], output_dir: str | None = None) -> str:
    """Write the job plan to a timestamped file plus latest.json."""
    out_dir = output_dir or config.OUTPUT_DIR
    os.makedirs(out_dir, exist_ok=True)

    payload = _payload(jobs)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    dated_path = os.path.join(out_dir, f"jobs-{stamp}.json")
    latest_path = os.path.join(out_dir, "latest.json")

    for path in (dated_path, latest_path):
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    log.info("wrote %d jobs to %s (and latest.json)", len(jobs), dated_path)
    return dated_path


def run(input_path: str | None = None, output_dir: str | None = None) -> tuple[list[GenerationJob], str]:
    scripts = load_scripts(input_path)
    jobs = build_plan(scripts)
    path = write_plan(jobs, output_dir)
    return jobs, path
