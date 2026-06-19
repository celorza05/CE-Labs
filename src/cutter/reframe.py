"""Face-aware reframing for the Cutter.

A fixed center-crop misframes shots where the speaker isn't centered. This module
samples faces across a clip with OpenCV and builds a time-varying ffmpeg crop so
the 9:16 window follows the face. Because podcasts cut the camera to whoever is
talking, "the largest face in the shot" is a good proxy for the active speaker —
no true audio-visual speaker detection required.

Limitation: in a static *two-shot* where both people are visible at once, this
picks the larger/closer face, not necessarily the one talking. That's the case
where Higgsfield's reframe (or proper active-speaker detection) would do better.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import statistics
import subprocess

from . import config

log = logging.getLogger("cutter.reframe")


def _crop_x(center: float, crop_w: float, src_w: float) -> int:
    """Clamp a face-centered crop window inside the frame."""
    return int(max(0.0, min(center - crop_w / 2.0, src_w - crop_w)))


def shots_from_cuts(cuts: list[float], duration: float) -> list[tuple[float, float]]:
    """Turn scene-cut times into (t0, t1) shot windows spanning [0, duration]."""
    bounds = sorted({0.0, duration, *(c for c in cuts if 0.0 < c < duration)})
    return [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]


def crop_per_shot(samples: list[tuple[float, float]], shots: list[tuple[float, float]],
                  crop_w: float, src_w: float) -> list[tuple[float, float, int]]:
    """One stable crop x per shot (median face center within it; hold across gaps)."""
    windows: list[tuple[float, float, int]] = []
    last_x: int | None = None
    for t0, t1 in shots:
        centers = [c for (t, c) in samples if t0 <= t < t1]
        if centers:
            x = _crop_x(statistics.median(centers), crop_w, src_w)
            last_x = x
        else:
            x = last_x if last_x is not None else _crop_x(src_w / 2.0, crop_w, src_w)
        windows.append((t0, t1, x))
    return windows


def build_x_expr(windows: list[tuple[float, float, int]]) -> str:
    """ffmpeg crop ``x`` expression (piecewise-constant over time t)."""
    if not windows:
        return "0"
    expr = str(windows[-1][2])
    for _t0, t1, x in reversed(windows[:-1]):
        expr = f"if(lt(t,{t1:.2f}),{x},{expr})"
    return expr


def probe_resolution(media: str) -> tuple[int, int] | None:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-print_format", "json", media],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode == 0:
            s = json.loads(out.stdout)["streams"][0]
            return int(s["width"]), int(s["height"])
    except Exception as exc:
        log.debug("ffprobe resolution failed: %s", exc)
    return None


def detect_scene_cuts(media: str, start: float, duration: float, threshold: float) -> list[float]:
    """Clip-relative times where the camera cuts, via ffmpeg's scene score."""
    exe = shutil.which(config.FFMPEG_BIN)
    if exe is None:
        return []
    cmd = [
        exe, "-hide_banner", "-ss", f"{start}", "-t", f"{duration}", "-i", media,
        "-filter:v", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=config.TIMEOUT)
    except Exception as exc:
        log.debug("scene detection failed: %s", exc)
        return []
    cuts = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", out.stderr)]
    return sorted({c for c in cuts if 0.0 < c < duration})


def face_centers(media: str, start: float, duration: float, sample_fps: float) -> list[tuple[float, float]]:
    """Sample the clip and return (clip_relative_time, face_x_center) for the largest face."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python not installed (pip install opencv-python)") from exc

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(media)
    samples: list[tuple[float, float]] = []
    try:
        step = 1.0 / max(0.5, sample_fps)
        t = 0.0
        while t < duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, (start + t) * 1000.0)
            ok, frame = cap.read()
            if ok:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
                if len(faces):
                    fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])
                    samples.append((t, float(fx) + fw / 2.0))
            t += step
    finally:
        cap.release()
    return samples


def crop_filter(media: str, start: float, duration: float) -> str | None:
    """Build a face-following ffmpeg crop filter, or None to fall back to center crop."""
    res = probe_resolution(media)
    if not res:
        log.info("couldn't probe resolution; using center crop")
        return None
    src_w, src_h = res
    crop_w = round(src_h * 9 / 16)

    samples = face_centers(media, start, duration, config.REFRAME_SAMPLE_FPS)
    if not samples:
        log.info("no faces detected; using center crop")
        return None

    cuts = detect_scene_cuts(media, start, duration, config.REFRAME_SCENE_THRESHOLD)
    shots = shots_from_cuts(cuts, duration)
    windows = crop_per_shot(samples, shots, crop_w, src_w)
    expr = build_x_expr(windows)
    log.info("face reframe: %d face samples, %d shots (one stable crop each)", len(samples), len(windows))
    return f"crop=w={crop_w}:h={src_h}:x='{expr}':y=0"
