"""Face-aware reframing for the Cutter.

A fixed center-crop misframes shots where the speaker isn't centered. This module
follows the speaker's face:

1. Coarsely sample the face x-position across the clip.
2. Split into shots wherever the face jumps and stays (a left<->right camera cut),
   detected from the face position itself (robust to same-background podcasts where
   a full-frame scene score barely changes).
3. Binary-search-refine each cut to ~1-frame precision, so the crop switches exactly
   when the camera does (no lag-flash).
4. Emit one stable crop per shot as a time-varying ffmpeg crop.

Limitation: in a static two-shot where both people are on screen at once, it picks
the larger face, not necessarily the talker — that's the Higgsfield-reframe case.
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


def segment_runs(samples: list[tuple[float, float]], jump: float) -> list[tuple[float, float, float]]:
    """Split the face-position series into runs (start_t, last_t, median_center).

    A new run starts when a sample deviates from the current run's median by more
    than ``jump`` AND the next sample confirms it (so a lone bad detection doesn't
    trigger a switch).
    """
    if not samples:
        return []
    runs: list[tuple[float, float, float]] = []
    start_t = last_t = samples[0][0]
    cur = [samples[0][1]]
    i = 1
    while i < len(samples):
        t, c = samples[i]
        ref = statistics.median(cur)
        confirmed = i + 1 < len(samples) and abs(samples[i + 1][1] - ref) > jump
        if abs(c - ref) > jump and confirmed:
            runs.append((start_t, last_t, statistics.median(cur)))
            start_t = t
            cur = [c]
        else:
            cur.append(c)
        last_t = t
        i += 1
    runs.append((start_t, last_t, statistics.median(cur)))
    return runs


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


def _face_x(cv2, cascade, cap, start: float, t: float) -> float | None:
    """Largest-face x-center at clip-relative time t, or None if no face."""
    cap.set(cv2.CAP_PROP_POS_MSEC, (start + t) * 1000.0)
    ok, frame = cap.read()
    if not ok:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
    if len(faces) == 0:
        return None
    fx, _fy, fw, _fh = max(faces, key=lambda f: f[2] * f[3])
    return float(fx) + fw / 2.0


def _refine_cut(cv2, cascade, cap, start: float, t_lo: float, t_hi: float,
                ref_a: float, ref_b: float, precision: float = 0.08) -> float:
    """Binary-search the exact cut time in (t_lo, t_hi] between positions A and B."""
    lo, hi = t_lo, t_hi
    for _ in range(6):  # ~6 reads caps the cost per boundary
        if hi - lo <= precision:
            break
        mid = (lo + hi) / 2.0
        x = _face_x(cv2, cascade, cap, start, mid)
        if x is None:
            lo = mid  # mid-cut / no face — the switch is later
        elif abs(x - ref_b) <= abs(x - ref_a):
            hi = mid  # already on B by mid — cut is at/before mid
        else:
            lo = mid  # still on A at mid — cut is after
    return (lo + hi) / 2.0


def crop_filter(media: str, start: float, duration: float) -> str | None:
    """Build a face-following ffmpeg crop filter, or None to fall back to center crop."""
    res = probe_resolution(media)
    if not res:
        log.info("couldn't probe resolution; using center crop")
        return None
    src_w, src_h = res
    crop_w = round(src_h * 9 / 16)

    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("opencv-python not installed (pip install opencv-python)") from exc

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(media)
    try:
        # 1) coarse face-position samples
        samples: list[tuple[float, float]] = []
        step = 1.0 / max(0.5, config.REFRAME_SAMPLE_FPS)
        t = 0.0
        while t < duration:
            x = _face_x(cv2, cascade, cap, start, t)
            if x is not None:
                samples.append((t, x))
            t += step
        if not samples:
            log.info("no faces detected; using center crop")
            return None

        # 2) split into runs by face-position jumps
        jump = src_w * config.REFRAME_JUMP_FRACTION
        runs = segment_runs(samples, jump)

        # 3) refine each boundary to the exact cut frame, then build windows
        windows: list[tuple[float, float, int]] = []
        prev = 0.0
        for idx, (_st, last_t, center) in enumerate(runs):
            if idx + 1 < len(runs):
                nxt_start, _nxt_last, nxt_center = runs[idx + 1]
                end = _refine_cut(cv2, cascade, cap, start, last_t, nxt_start, center, nxt_center)
            else:
                end = duration
            windows.append((prev, end, _crop_x(center, crop_w, src_w)))
            prev = end
    finally:
        cap.release()

    expr = build_x_expr(windows)
    log.info("face reframe: %d face samples -> %d shot(s) (cuts refined)", len(samples), len(windows))
    return f"crop=w={crop_w}:h={src_h}:x='{expr}':y=0"


import json  # noqa: E402  (kept near use; placed last to avoid clutter above)
