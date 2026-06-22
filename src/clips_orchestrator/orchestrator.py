"""The clips Orchestrator: sequence stages, post to Slack, hold the gate."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from ..orchestrator import slack

log = logging.getLogger("clips_orchestrator")

STATE_DIR = os.getenv("CLIPS_ORCHESTRATOR_STATE_DIR", "data/clips/orchestrator")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_state(state: dict) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    state["updated_at"] = _now()
    with open(os.path.join(STATE_DIR, "state.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)


def load_state() -> dict:
    path = os.path.join(STATE_DIR, "state.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _fmt(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60:d}:{s % 60:02d}"


def _attr(obj, name, default=""):
    return getattr(obj, name) if hasattr(obj, name) else obj.get(name, default)


def build_prepare_message(source, clips, cut_results) -> str:
    title = _attr(source, "title", "source")
    lines = [f":scissors: *Clips run* — {len(clips)} clips from _{title}_"]
    done = sum(1 for r in cut_results if r.get("status") == "done")
    for i, c in enumerate(clips, start=1):
        clip_title = _attr(c, "title", "")
        hook = _attr(c, "hook", "")
        start = _attr(c, "start_seconds", 0)
        end = _attr(c, "end_seconds", 0)
        head = f"{i}. *{clip_title}*" if clip_title else f"{i}."
        lines.append(f"{head}  [{_fmt(start)}–{_fmt(end)}]")
        if hook:
            lines.append(f"    _{hook}_")
    lines.append(f"\n:film_frames: Cut {done}/{len(cut_results)} clips to `data/clips/out/`.")
    lines.append(
        "\n:white_check_mark: *To approve*, review the clips then run:\n"
        "```python -m src.clips_orchestrator publish --youtube --privacy unlisted```"
    )
    return "\n".join(lines)


def build_publish_message(results, youtube: bool) -> str:
    uploaded = sum(1 for r in results if r.youtube_status == "uploaded")
    prepared = sum(1 for r in results if r.tiktok_status == "prepared")
    head = ":rocket: *Clips published*" if youtube else ":package: *Clips publish step run*"
    lines = [f"{head} — {len(results)} clips"]
    lines.append(f"• YouTube: {uploaded} uploaded" + ("" if youtube else " (planning only — `--youtube` to upload)"))
    lines.append(f"• TikTok: {prepared} hand-off packages ready")
    for r in results:
        if r.youtube_url:
            lines.append(f"   - {r.title}: {r.youtube_url}")
    return "\n".join(lines)


def prepare(source_input: str, reframe: str | None = None) -> dict:
    """Sourcer -> Transcriber -> Clipper -> Cutter; post to Slack; stop."""
    from ..sourcer import sourcer
    from ..transcriber import transcriber
    from ..clipper import selector
    from ..cutter import cutter, config as cutter_config

    log.info("stage 1/4 — Sourcer")
    source, _ = sourcer.run(source_input)

    log.info("stage 2/4 — Transcriber")
    transcriber.run()

    log.info("stage 3/4 — Clipper")
    clips, _ = selector.run()

    if reframe:
        cutter_config.REFRAME = reframe
    log.info("stage 4/4 — Cutter")
    cut_results, _ = cutter.run()

    msg = build_prepare_message(source, clips, cut_results)
    delivered = slack.notify(msg)

    state = {
        "stage": "awaiting_approval",
        "source": getattr(source, "title", ""),
        "clips": len(clips),
        "cut": sum(1 for r in cut_results if r.get("status") == "done"),
        "reframe": reframe or cutter_config.REFRAME,
        "slack_delivered": delivered,
    }
    save_state(state)
    return state


def publish(youtube: bool = False, privacy: str | None = None, limit: int | None = None) -> dict:
    """Run the Publisher on the cut clips. The post-approval step."""
    from ..publisher import publisher as pub

    log.info("publishing clips (youtube=%s, privacy=%s)", youtube, privacy)
    results, report_path = pub.run_clips(do_youtube=youtube, privacy=privacy, limit=limit, dry_run=False)

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
