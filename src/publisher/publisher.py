"""The Publisher pipeline: match assets to scripts, then publish each."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from . import config, metadata, tiktok, youtube
from .models import PublishResult

log = logging.getLogger("publisher")


def _load(path: str, key: str) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found — run the earlier stages first.")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get(key, [])


def _index_scripts(scripts: list[dict]) -> dict[str, dict]:
    """Index scripts by source_url (falling back to title) for joining to jobs."""
    idx: dict[str, dict] = {}
    for s in scripts:
        for k in (s.get("source_url"), s.get("title")):
            if k:
                idx.setdefault(k, s)
    return idx


def _match(job: dict, idx: dict[str, dict]) -> dict:
    """Find the script for a job; fall back to job fields if not found."""
    for k in (job.get("source_url"), job.get("script_title")):
        if k and k in idx:
            return idx[k]
    return {
        "title": job.get("script_title", ""),
        "source_title": job.get("source_title", ""),
        "source_url": job.get("source_url", ""),
        "caption": "",
        "hashtags": [],
    }


def select_jobs(jobs: list[dict], dry_run: bool) -> list[dict]:
    """In dry-run, preview all jobs. For real publishing, require a downloaded asset."""
    if dry_run:
        return jobs
    ready = []
    for j in jobs:
        if j.get("status") == "completed" and j.get("asset_path") and os.path.exists(j["asset_path"]):
            ready.append(j)
        else:
            log.info("skipping %s (no downloaded asset yet)", j.get("job_id"))
    return ready


def publish_item(job: dict, script: dict, *, do_youtube: bool, privacy: str, dry_run: bool) -> PublishResult:
    title = metadata.youtube_title(script)
    asset = job.get("asset_path") or "(not generated yet)"
    result = PublishResult(job_id=job.get("job_id", "?"), title=title, asset_path=asset)

    # --- YouTube ---
    if config.YOUTUBE_ENABLED and do_youtube:
        desc = metadata.youtube_description(script)
        tags = metadata.youtube_tags(script)
        if dry_run:
            result.youtube_status = "planned"
            result.youtube_privacy = privacy
            log.info("[dry-run] YouTube upload: %r (privacy=%s)", title, privacy)
        else:
            try:
                vid, url = youtube.upload(asset, title, desc, tags, privacy)
                result.youtube_status = "uploaded"
                result.youtube_video_id = vid
                result.youtube_url = url
                result.youtube_privacy = privacy
                log.info("uploaded to YouTube: %s", url)
            except Exception as exc:
                result.youtube_status = "failed"
                result.youtube_error = str(exc)[:500]
                log.warning("YouTube upload failed for %s: %s", result.job_id, exc)
    elif config.YOUTUBE_ENABLED:
        result.youtube_status = "planned"  # not requested this run
        result.youtube_privacy = privacy

    # --- TikTok (manual hand-off) ---
    if config.TIKTOK_ENABLED:
        caption = metadata.tiktok_caption(script)
        if dry_run or not job.get("asset_path"):
            result.tiktok_status = "skipped" if not job.get("asset_path") else "prepared"
            if dry_run:
                log.info("[dry-run] TikTok hand-off: %r", caption.replace("\n", " ")[:80])
        else:
            try:
                pkg = tiktok.prepare(asset, caption, config.PUBLISH_DIR, result.job_id)
                result.tiktok_status = "prepared"
                result.tiktok_package_dir = pkg
                log.info("prepared TikTok hand-off: %s", pkg)
            except Exception as exc:
                result.tiktok_status = "failed"
                result.tiktok_error = str(exc)[:500]
                log.warning("TikTok hand-off failed for %s: %s", result.job_id, exc)

    return result


def run(*, do_youtube: bool, privacy: str | None, limit: int | None, dry_run: bool) -> tuple[list[PublishResult], str]:
    jobs = _load(config.JOBS_INPUT, "jobs")
    scripts = _load(config.SCRIPTS_INPUT, "scripts")
    idx = _index_scripts(scripts)

    selected = select_jobs(jobs, dry_run)
    if limit is not None:
        selected = selected[:limit]

    use_privacy = privacy or config.YOUTUBE_PRIVACY
    results = [
        publish_item(j, _match(j, idx), do_youtube=do_youtube, privacy=use_privacy, dry_run=dry_run)
        for j in selected
    ]

    path = _write_report(results, do_youtube=do_youtube, privacy=use_privacy, dry_run=dry_run)
    return results, path


def _write_report(results: list[PublishResult], *, do_youtube: bool, privacy: str, dry_run: bool) -> str:
    os.makedirs(config.PUBLISH_DIR, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "youtube_requested": do_youtube,
        "youtube_privacy": privacy,
        "count": len(results),
        "results": [r.to_dict() for r in results],
    }
    path = os.path.join(config.PUBLISH_DIR, "latest.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    return path
