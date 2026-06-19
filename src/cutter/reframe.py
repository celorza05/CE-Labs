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
import math
import statistics
import subprocess

from . import config

log = logging.getLogger("cutter.reframe")


def _crop_x(center: float, crop_w: float, src_w: float) -> int:
    """Clamp a face-centered crop window inside the frame."""
    return int(max(0.0, min(center - crop_w / 2.0, src_w - crop_w)))


def bucket_windows(samples: list[tuple[float, float]], duration: float, crop_w: float,
                   src_w: float, bucket: float = 1.0, merge_tol: int = 20) -> list[tuple[float, float, int]]:
    """Turn (time, face_x_center) samples into (t0, t1, crop_x) windows.

    Samples are grouped into ``bucket``-second windows (median per bucket); gaps
    hold the previous position; adjacent windows within ``merge_tol`` px are merged
    to avoid jitter.
    """
    by_bucket: dict[int, list[float]] = {}
    for t, c in samples:
        by_bucket.setdefault(int(t // bucket), []).append(c)

    n = max(1, math.ceil(duration / bucket))
    last_x: int | None = None
    raw: list[tuple[float, float, int]] = []
    for i in range(n):
        t0 = i * bucket
        t1 = min((i + 1) * bucket, duration)
        if i in by_bucket:
            x = _crop_x(statistics.median(by_bucket[i]), crop_w, src_w)
            last_x = x
        else:
            x = last_x if last_x is not None else _crop_x(src_w / 2.0, crop_w, src_w)
        raw.append((t0, t1, x))

    merged: list[list[float]] = []
    for t0, t1, x in raw:
        if merged and abs(merged[-1][2] - x) <= merge_tol:
            merged[-1][1] = t1  # extend the previous window
        else:
            merged.append([t0, t1, x])
    return [(a, b, int(c)) for a, b, c in merged]


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

    windows = bucket_windows(samples, duration, crop_w, src_w)
    expr = build_x_expr(windows)
    log.info("face reframe: %d face samples, %d crop windows", len(samples), len(windows))
    return f"crop=w={crop_w}:h={src_h}:x='{expr}':y=0"
