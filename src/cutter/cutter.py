"""Cut, reframe to 9:16, and burn captions — one finished clip per spec."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess

from . import captions, config

log = logging.getLogger("cutter")

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str, max_len: int = 50) -> str:
    s = _SLUG_RE.sub("-", text.lower()).strip("-")
    return s[:max_len].strip("-") or "clip"


def _load(path: str, key: str | None):
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} not found — run the earlier clips stages first.")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return data.get(key) if key else data


def build_command(media_abspath: str, has_video: bool, start: float, duration: float,
                  ass_name: str, out_name: str) -> list[str]:
    """ffmpeg argv. ``ass_name``/``out_name`` are basenames (run with cwd=OUTPUT_DIR)."""
    w, h = config.WIDTH, config.HEIGHT
    if has_video:
        vf = f"crop='min(iw,ih*9/16)':ih,scale={w}:{h},ass={ass_name}"
        return [
            config.FFMPEG_BIN, "-y",
            "-ss", f"{start}", "-i", media_abspath, "-t", f"{duration}",
            "-vf", vf,
            "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart",
            out_name,
        ]
    # Audio-only: solid background canvas + the seeked audio + burned captions.
    return [
        config.FFMPEG_BIN, "-y",
        "-f", "lavfi", "-i", f"color=c={config.BG_COLOR}:s={w}x{h}",
        "-ss", f"{start}", "-i", media_abspath, "-t", f"{duration}",
        "-vf", f"ass={ass_name}",
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        out_name,
    ]


def _run_ffmpeg(cmd: list[str]) -> subprocess.CompletedProcess:
    exe = shutil.which(cmd[0])
    if exe is None:
        raise FileNotFoundError(cmd[0])
    return subprocess.run(
        [exe, *cmd[1:]], cwd=config.OUTPUT_DIR,
        capture_output=True, text=True, timeout=config.TIMEOUT,
    )


def cut_one(clip: dict, source: dict, segments: list[dict], index: int, dry_run: bool) -> dict:
    start = float(clip["start_seconds"])
    end = float(clip["end_seconds"])
    duration = max(0.0, end - start)
    name = f"{index:02d}-{_slug(clip.get('title', 'clip'))}"
    ass_name = f"{name}.ass"
    out_name = f"{name}.mp4"

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    media_abspath = os.path.abspath(source["media_path"])
    result = {"clip": name, "start": start, "end": end, "status": "pending",
              "output": os.path.join(config.OUTPUT_DIR, out_name)}

    caps = captions.segments_in_clip(segments, start, end)
    ass_text = captions.build_ass(caps)

    if dry_run:
        cmd = build_command(media_abspath, bool(source.get("has_video")), start, duration, ass_name, out_name)
        log.info("[dry-run] (%d captions) ffmpeg %s", len(caps), " ".join(cmd[1:]))
        result["status"] = "planned"
        return result

    with open(os.path.join(config.OUTPUT_DIR, ass_name), "w", encoding="utf-8") as fh:
        fh.write(ass_text)

    cmd = build_command(media_abspath, bool(source.get("has_video")), start, duration, ass_name, out_name)
    try:
        proc = _run_ffmpeg(cmd)
    except FileNotFoundError:
        result["status"] = "failed"
        result["error"] = f"'{config.FFMPEG_BIN}' not found on PATH — install ffmpeg."
        return result
    except subprocess.TimeoutExpired:
        result["status"] = "failed"
        result["error"] = f"ffmpeg timed out after {config.TIMEOUT}s"
        return result

    if proc.returncode != 0:
        result["status"] = "failed"
        result["error"] = (proc.stderr or "ffmpeg failed").strip()[-500:]
        log.warning("clip %s failed: %s", name, result["error"])
    else:
        result["status"] = "done"
        log.info("cut %s", out_name)
    return result


def run(limit: int | None = None, dry_run: bool = False) -> tuple[list[dict], str]:
    clips = _load(config.CLIPS_INPUT, "clips")
    source = _load(config.SOURCE_INPUT, None)
    segments = _load(config.TRANSCRIPT_INPUT, "segments")

    if not source.get("has_video"):
        log.info("source is audio-only — clips will use a %s background", config.BG_COLOR)

    selected = clips[:limit] if limit is not None else clips
    results = [cut_one(c, source, segments, i, dry_run) for i, c in enumerate(selected, start=1)]

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(config.OUTPUT_DIR, "report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump({"count": len(results), "dry_run": dry_run, "results": results}, fh, indent=2, ensure_ascii=False)
    return results, report_path
