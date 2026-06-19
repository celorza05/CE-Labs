"""The Orchestrator: sequence stages, post to Slack, hold the approval gate."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from . import config, slack

log = logging.getLogger("orchestrator")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_state(state: dict) -> None:
    os.makedirs(config.STATE_DIR, exist_ok=True)
    state["updated_at"] = _now()
    with open(os.path.join(config.STATE_DIR, "state.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)


def load_state() -> dict:
    path = os.path.join(config.STATE_DIR, "state.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# --- Message builders (pure; unit-tested) ---------------------------------

def build_prepare_message(scripts, jobs, generated: bool) -> str:
    lines = [f":movie_camera: *Pipeline run* — {len(scripts)} scripts ready for review"]
    for i, s in enumerate(scripts, start=1):
        lines.append(f"{i}. *{_attr(s, 'hook')}* — {_attr(s, 'title')}")
    completed = sum(1 for j in jobs if _attr(j, "status") == "completed")
    failed = sum(1 for j in jobs if _attr(j, "status") == "failed")
    if generated:
        lines.append(f"\n:clapper: Generated {completed} videos ({failed} failed).")
    else:
        lines.append(f"\n:page_facing_up: Planned {len(jobs)} generation jobs (videos not generated).")
    lines.append("\n:white_check_mark: Review, then approve by running `python -m src.orchestrator publish`.")
    return "\n".join(lines)


def build_publish_message(results, youtube: bool) -> str:
    uploaded = sum(1 for r in results if _attr(r, "youtube_status") == "uploaded")
    prepared = sum(1 for r in results if _attr(r, "tiktok_status") == "prepared")
    head = ":rocket: *Published*" if youtube else ":package: *Publish step run*"
    lines = [f"{head} — {len(results)} videos"]
    lines.append(f"• YouTube: {uploaded} uploaded" + ("" if youtube else " (planning only — `--youtube` to upload)"))
    lines.append(f"• TikTok: {prepared} hand-off packages ready")
    for r in results:
        if _attr(r, "youtube_url"):
            lines.append(f"   - {_attr(r, 'title')}: {_attr(r, 'youtube_url')}")
    return "\n".join(lines)


def _attr(obj, name):
    """Read an attribute from a dataclass/pydantic object or a dict."""
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


# --- Stages ---------------------------------------------------------------

def prepare(generate: bool | None = None, limit: int | None = None) -> dict:
    """Scout -> Writer -> Producer (plan, optionally generate); post to Slack; stop."""
    do_generate = config.GENERATE_BY_DEFAULT if generate is None else generate

    from ..scout import pipeline as scout_pipeline

    log.info("stage 1/3 — Scout")
    trends, _ = scout_pipeline.run()

    from ..writer import generator as writer_gen

    log.info("stage 2/3 — Writer")
    scripts, _ = writer_gen.run()

    from ..producer import planner as producer_planner

    log.info("stage 3/3 — Producer (plan)")
    jobs, _ = producer_planner.run()

    if do_generate:
        from ..producer import submit as producer_submit

        log.info("generating videos via Higgsfield")
        producer_submit.submit_all(jobs, limit=limit)
        producer_planner.write_plan(jobs)

    msg = build_prepare_message(scripts, jobs, do_generate)
    delivered = slack.notify(msg)

    state = {
        "stage": "awaiting_approval",
        "trends": len(trends),
        "scripts": len(scripts),
        "jobs": len(jobs),
        "generated": do_generate,
        "slack_delivered": delivered,
    }
    save_state(state)
    return state


def publish(youtube: bool = False, privacy: str | None = None, limit: int | None = None) -> dict:
    """Run the Publisher. The deliberate, post-approval step."""
    from ..publisher import publisher as pub

    log.info("publishing (youtube=%s, privacy=%s)", youtube, privacy)
    results, report_path = pub.run(do_youtube=youtube, privacy=privacy, limit=limit, dry_run=False)

    msg = build_publish_message(results, youtube)
    delivered = slack.notify(msg)

    state = {
        "stage": "published",
        "published": len(results),
        "youtube_uploaded": sum(1 for r in results if r.youtube_status == "uploaded"),
        "tiktok_prepared": sum(1 for r in results if r.tiktok_status == "prepared"),
        "report": report_path,
        "slack_delivered": delivered,
    }
    save_state(state)
    return state
