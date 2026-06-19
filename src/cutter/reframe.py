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
import statistics
import subprocess

from . import config

log = logging.getLogger("cutter.reframe")


def _crop_x(center: float, crop_w: float, src_w: float) -> int:
    """Clamp a face-centered crop window inside the frame."""
    return int(max(0.0, min(center - crop_w / 2.0, src_w - crop_w)))


def segment_shots(samples: list[tuple[float, float]], duration: float, crop_w: float,
                  src_w: float, jump: float) -> list[tuple[float, float, int]]:
    """Split the face-position series into shots wherever it jumps and stays.

    A new shot starts when a sample deviates from the current shot's median face
    position by more than ``jump`` AND the *next* sample confirms it (so a single
    bad detection doesn't trigger a switch). Each shot gets one stable crop.
    """
    if not samples:
        return []

    runs: list[tuple[float, float]] = []  # (start_time, median_center)
    start_t = samples[0][0]
    cur = [samples[0][1]]
    i = 1
    while i < len(samples):
        t, c = samples[i]
        ref = statistics.median(cur)
        confirmed = i + 1 < len(samples) and abs(samples[i + 1][1] - ref) > jump
        if abs(c - ref) > jump and confirmed:
            runs.append((start_t, statistics.median(cur)))
            start_t = t
            cur = [c]
        else:
            cur.append(c)  # median resists the occasional outlier
        i += 1
    runs.append((start_t, statistics.median(cur)))

    windows: list[tuple[float, float, int]] = []
    for idx, (st, center) in enumerate(runs):
        t1 = runs[idx + 1][0] if idx + 1 < len(runs) else duration
        windows.append((st, t1, _crop_x(center, crop_w, src_w)))
    # the crop must cover from t=0
    if windows and windows[0][0] > 0:
        first = windows[0]
        windows[0] = (0.0, first[1], first[2])
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

    jump = src_w * config.REFRAME_JUMP_FRACTION
    windows = segment_shots(samples, duration, crop_w, src_w, jump)
    expr = build_x_expr(windows)
    log.info("face reframe: %d face samples -> %d shot(s)", len(samples), len(windows))
    return f"crop=w={crop_w}:h={src_h}:x='{expr}':y=0"
