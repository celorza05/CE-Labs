"""Submission step: generate each job's video via the Higgsfield CLI.

Shells out to the official CLI (``higgsfield generate create ... --wait --json``),
parses the returned asset URL, downloads it, and records the result on the job.

The CLI command is assembled from config so the model and any uncertain flags
(e.g. the aspect-ratio flag name) can be corrected via ``.env`` without code
changes. ``--dry-run`` prints the exact commands without running them, so you can
verify the syntax before spending any credits.

Prerequisites (one-time, on the machine that runs this):
    npm install -g @higgsfield/cli
    higgsfield auth login
"""

from __future__ import annotations

import json
import logging
import os
import re
import shlex
import shutil
import subprocess

from . import config
from .models import GenerationJob

log = logging.getLogger("producer.submit")

_MEDIA_URL_RE = re.compile(r"https?://\S+\.(?:mp4|mov|webm|m4v)\b", re.IGNORECASE)
_ANY_URL_RE = re.compile(r"https?://\S+")


def build_command(job: GenerationJob) -> list[str]:
    """Assemble the Higgsfield CLI argv for one job (no shell, safe quoting)."""
    model = job.model or config.CLI_MODEL
    cmd = [
        config.CLI_BIN,
        "generate",
        "create",
        model,
        "--prompt",
        job.prompt,
        "--duration",
        str(job.duration_seconds),
    ]
    if config.CLI_MODE:
        cmd += ["--mode", config.CLI_MODE]
    if config.CLI_SOUND:
        cmd += ["--sound", config.CLI_SOUND]
    if config.CLI_ASPECT_FLAG:
        cmd += [config.CLI_ASPECT_FLAG, job.aspect_ratio]
    cmd += ["--wait"]
    if config.CLI_WAIT_TIMEOUT.strip():
        cmd += ["--wait-timeout", config.CLI_WAIT_TIMEOUT]
    cmd += ["--json"]
    if config.CLI_EXTRA_FLAGS.strip():
        cmd += shlex.split(config.CLI_EXTRA_FLAGS)
    return cmd


_URL_KEY_HINTS = ("url", "video", "result", "asset", "output")
_ID_KEYS = ("id", "job_id", "job_set_id", "generation_id", "request_id")


def _string_leaves(obj, key: str = ""):
    """Yield every (key, string-value) leaf in a nested dict/list."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _string_leaves(v, str(k))
    elif isinstance(obj, list):
        for v in obj:
            yield from _string_leaves(v, key)
    elif isinstance(obj, str):
        yield key, obj


def _find_url(leaves: list[tuple[str, str]]) -> str | None:
    # Prefer a value that's literally a media URL...
    for _, v in leaves:
        if _MEDIA_URL_RE.fullmatch(v) or _MEDIA_URL_RE.match(v):
            return v
    # ...then any http value under a URL-ish key.
    for k, v in leaves:
        if v.startswith("http") and any(h in k.lower() for h in _URL_KEY_HINTS):
            return v
    return None


def _find_id(leaves: list[tuple[str, str]]) -> str | None:
    for k, v in leaves:
        kl = k.lower()
        if kl in _ID_KEYS or kl.endswith("_id"):
            return v
    return None


def parse_result(stdout: str) -> tuple[str | None, str | None]:
    """Extract (asset_url, job_id) from the CLI's output.

    Tries JSON first (``--json``), then falls back to scraping a media URL from
    plain text (the ``--wait`` path prints the result URL).
    """
    text = stdout.strip()
    if text:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if data is not None:
            leaves = list(_string_leaves(data))
            url = _find_url(leaves)
            if url:
                return url, _find_id(leaves)

    m = _MEDIA_URL_RE.search(stdout) or _ANY_URL_RE.search(stdout)
    return (m.group(0) if m else None), None


def download_asset(url: str, dest_path: str) -> None:
    """Stream the generated video to a local file."""
    import requests

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with requests.get(url, stream=True, timeout=config.CLI_TIMEOUT) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=1 << 16):
                if chunk:
                    fh.write(chunk)


def submit_job(job: GenerationJob, dry_run: bool = False) -> GenerationJob:
    """Generate one job's video. Mutates and returns the job."""
    cmd = build_command(job)
    if dry_run:
        log.info("[dry-run] %s", " ".join(shlex.quote(c) for c in cmd))
        return job

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=config.CLI_TIMEOUT)
    except FileNotFoundError:
        job.status = "failed"
        job.error = f"CLI '{config.CLI_BIN}' not found — run: npm install -g @higgsfield/cli"
        return job
    except subprocess.TimeoutExpired:
        job.status = "failed"
        job.error = f"generation timed out after {config.CLI_TIMEOUT}s"
        return job

    if proc.returncode != 0:
        job.status = "failed"
        job.error = (proc.stderr or proc.stdout or "non-zero exit").strip()[:500]
        return job

    url, hf_id = parse_result(proc.stdout)
    if not url:
        job.status = "failed"
        job.error = "could not find an asset URL in CLI output"
        return job

    job.higgsfield_job_id = hf_id
    job.asset_url = url
    dest = os.path.join(config.ASSETS_DIR, f"{job.job_id}.mp4")
    try:
        download_asset(url, dest)
        job.asset_path = dest
        job.status = "completed"
    except Exception as exc:  # asset generated but download failed — keep the URL
        job.status = "failed"
        job.error = f"generated but download failed: {exc}"
    return job


def submit_all(jobs: list[GenerationJob], limit: int | None = None, dry_run: bool = False) -> list[GenerationJob]:
    """Submit pending jobs (up to ``limit``)."""
    if not dry_run and config.CLI_BIN and shutil.which(config.CLI_BIN) is None:
        raise RuntimeError(
            f"Higgsfield CLI '{config.CLI_BIN}' not on PATH. Install it with "
            "`npm install -g @higgsfield/cli` and run `higgsfield auth login`."
        )

    pending = [j for j in jobs if j.status == "pending"]
    if limit is not None:
        pending = pending[:limit]

    for i, job in enumerate(pending, start=1):
        log.info("generating %d/%d: %s", i, len(pending), job.job_id)
        submit_job(job, dry_run=dry_run)
        if not dry_run and job.status == "failed":
            log.warning("job %s failed: %s", job.job_id, job.error)
    return jobs
