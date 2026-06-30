"""Reframe diagnostic — tells us which crop strategy fits a given source.

Samples one clip window from the prepared source, runs the same Haar face
detector the Cutter uses, and reports:

  * faces-per-frame distribution (1 = single-speaker shots -> smart crop wins;
    frequent 2+ = two-shots -> blurred-fit may win)
  * where the talking head sits (left / center / right thirds) and how bimodal
    that is (a clean left<->right two-camera podcast is strongly bimodal)
  * how often the *largest face* jumps sides between samples (the choppiness
    you're seeing — each jump is a crop switch the current mode would make)
  * how many shots the current segmenter + min-shot merge would produce
  * how many *real* camera cuts ffmpeg's scene detector finds (so we can switch
    the crop on real edits instead of detection noise)

Run from the repo root:

    python -m scripts.reframe_diag            # analyse clip #0
    python -m scripts.reframe_diag --clip 2   # analyse a different clip
    python -m scripts.reframe_diag --fps 4    # sample more densely
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

from src.cutter import config
from src.cutter.reframe import merge_short_runs, segment_runs


def _load(path: str) -> dict:
    if not os.path.exists(path):
        sys.exit(f"missing {path} — run `prepare` first so the clip data exists.")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _scene_cuts(media: str, start: float, dur: float, threshold: float) -> int:
    """Count ffmpeg scene-change spikes above `threshold` in the window."""
    try:
        proc = subprocess.run(
            [config.FFMPEG_BIN, "-hide_banner", "-ss", str(start), "-t", str(dur),
             "-i", media, "-filter:v", f"select='gt(scene,{threshold})',showinfo",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=300,
        )
        # showinfo prints one line per selected (scene-change) frame
        return proc.stderr.count("pts_time:")
    except Exception as exc:  # ffmpeg missing / odd input — don't crash the report
        print(f"  (scene detection skipped: {exc})")
        return -1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reframe_diag")
    ap.add_argument("--clip", type=int, default=0, help="clip index in clips.json")
    ap.add_argument("--fps", type=float, default=3.0, help="samples per second")
    args = ap.parse_args(argv)

    source = _load(config.SOURCE_INPUT)
    clips = _load(config.CLIPS_INPUT)
    clip_list = clips if isinstance(clips, list) else clips.get("clips", [])
    if not clip_list:
        sys.exit("no clips found in clips.json")
    if not (0 <= args.clip < len(clip_list)):
        sys.exit(f"--clip {args.clip} out of range (have {len(clip_list)} clips)")

    media = source.get("media_path") or source.get("media") or ""
    if not media or not os.path.exists(media):
        sys.exit(f"source media not found: {media!r}")

    clip = clip_list[args.clip]
    start = float(clip.get("start_seconds", 0))
    end = float(clip.get("end_seconds", start))
    dur = max(0.0, end - start)
    print(f"source : {source.get('title', media)}")
    print(f"clip #{args.clip}: [{start:.1f}s -> {end:.1f}s] ({dur:.1f}s)  hook: {clip.get('hook','')[:60]}")
    print(f"media  : {media}  ({source.get('has_video', '?')} video)\n")

    try:
        import cv2
    except ImportError:
        sys.exit("opencv-python not installed (pip install -r requirements-clips.txt)")

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    cap = cv2.VideoCapture(media)
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920

    # Sample face counts + the largest-face x-center over the clip window.
    step = 1.0 / max(0.5, args.fps)
    n_frames = 0
    face_counts: list[int] = []
    biggest: list[tuple[float, float]] = []  # (t, x-center of largest face)
    t = 0.0
    while t < dur:
        cap.set(cv2.CAP_PROP_POS_MSEC, (start + t) * 1000.0)
        ok, frame = cap.read()
        if not ok:
            break
        n_frames += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))
        face_counts.append(len(faces))
        if len(faces):
            fx, _fy, fw, _fh = max(faces, key=lambda f: f[2] * f[3])
            biggest.append((t, float(fx) + fw / 2.0))
        t += step
    cap.release()

    if n_frames == 0:
        sys.exit("couldn't read any frames from the clip window.")

    # --- faces per frame ---
    zero = face_counts.count(0)
    one = face_counts.count(1)
    multi = sum(1 for c in face_counts if c >= 2)
    avg = sum(face_counts) / n_frames
    print("== faces on screen ==")
    print(f"  sampled {n_frames} frames at {args.fps}/s")
    print(f"  0 faces : {zero:3d} ({100*zero/n_frames:4.0f}%)   <- detector missed / no clear face")
    print(f"  1 face  : {one:3d} ({100*one/n_frames:4.0f}%)   <- single-speaker shot (smart crop frames correctly)")
    print(f"  2+ faces: {multi:3d} ({100*multi/n_frames:4.0f}%)   <- two-shot (largest-face guess can be wrong)")
    print(f"  avg faces/frame: {avg:.2f}\n")

    # --- position distribution of the largest face ---
    thirds = [0, 0, 0]
    for _t, x in biggest:
        thirds[min(2, int(3 * x / src_w))] += 1
    tot = max(1, len(biggest))
    print("== largest-face position (thirds of frame width) ==")
    print(f"  left  : {thirds[0]:3d} ({100*thirds[0]/tot:4.0f}%)")
    print(f"  center: {thirds[1]:3d} ({100*thirds[1]/tot:4.0f}%)")
    print(f"  right : {thirds[2]:3d} ({100*thirds[2]/tot:4.0f}%)")
    bimodal = thirds[0] > 0.2 * tot and thirds[2] > 0.2 * tot
    print(f"  -> {'BIMODAL (left<->right camera setup)' if bimodal else 'mostly one region'}\n")

    # --- choppiness: how often the largest-face side flips between samples ---
    flips = 0
    prev_third = None
    for _t, x in biggest:
        th = min(2, int(3 * x / src_w))
        if prev_third is not None and th != prev_third:
            flips += 1
        prev_third = th
    print("== choppiness (largest-face side changes) ==")
    print(f"  raw side-flips across samples: {flips}")

    # --- what the current segmenter would produce ---
    jump = src_w * config.REFRAME_JUMP_FRACTION
    runs = segment_runs(biggest, jump)
    merged = merge_short_runs(runs, config.REFRAME_MIN_SHOT_SECONDS)
    print(f"  shots from segment_runs        : {len(runs)}")
    print(f"  shots after min-shot merge ({config.REFRAME_MIN_SHOT_SECONDS}s): {len(merged)}")
    print(f"  -> {len(merged)} crop switches in {dur:.0f}s "
          f"({len(merged)/max(1,dur)*60:.1f} switches/min)\n")

    # --- real camera cuts per ffmpeg scene detection ---
    print("== real camera cuts (ffmpeg scene detection) ==")
    for thr in (0.2, 0.3, 0.4):
        n = _scene_cuts(media, start, dur, thr)
        if n >= 0:
            print(f"  threshold {thr}: {n} cuts")
    print()

    # --- recommendation ---
    print("== read ==")
    if avg < 1.3 and multi < 0.25 * n_frames:
        print("  Mostly SINGLE-SPEAKER shots -> the smart face crop (lip-motion +")
        print("  scene-cut switching) should frame the talker correctly and large.")
    elif multi > 0.4 * n_frames:
        print("  Frequent TWO-SHOTS -> largest-face guessing will mis-frame often;")
        print("  the blurred-fit mode (whole frame, never mis-frames) is the safer bet.")
    else:
        print("  Mixed -> smart face crop with a fit fallback per clip is the move.")
    if zero > 0.3 * n_frames:
        print("  NOTE: detector missed faces in >30% of frames (small/angled/low-light")
        print("  faces) — face-follow will be unreliable here regardless of mode.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
