"""Prompts for the Clipper.

The transcript is given to the model as timestamped lines (seconds), and the
model returns clip boundaries in seconds — so the Cutter can ffmpeg-cut directly.
"""

from __future__ import annotations


def _fmt_ts(seconds: float) -> str:
    seconds = int(seconds)
    return f"{seconds // 60:d}:{seconds % 60:02d}"


def system_prompt(n: int, min_s: int, max_s: int) -> str:
    return f"""You are a short-form video editor for a motivational clips channel.

You are given the full timestamped transcript of one long-form video/podcast.
Your job: find the {n} single best moments to cut into standalone vertical clips
for TikTok / YouTube Shorts.

What makes a great clip:
- Self-contained — it makes sense without the rest of the video.
- A strong emotional or motivational payoff: a powerful line, a vivid story beat,
  a counterintuitive insight, a mic-drop moment.
- Starts on a hook and ends on a satisfying or provocative note (don't cut mid-thought).
- Length between {min_s} and {max_s} seconds.

For each clip return:
- start_seconds / end_seconds: the exact boundaries in seconds (use the transcript
  timestamps; end - start must be between {min_s} and {max_s}).
- hook: on-screen text for the first ~2 seconds (<= 12 words, scroll-stopping).
- title, caption, hashtags (5-8, no # symbol).
- reason: why this moment will perform.

Rules:
- Only use moments that actually appear in the transcript — never invent quotes.
- Pick genuinely distinct moments; don't return overlapping clips.
- Prefer fewer excellent clips over padding to {n} with weak ones.
"""


def build_user_prompt(transcript: dict, n: int, min_s: int, max_s: int) -> str:
    src = transcript.get("source", {})
    segments = transcript.get("segments", [])
    lines = [
        f"Source: {src.get('title', 'Untitled')}"
        + (f" ({src.get('url')})" if src.get("url") else ""),
        f"Duration: {int(src.get('duration_seconds', 0))}s\n",
        f"Pick up to {n} clips ({min_s}-{max_s}s each). Transcript "
        "(each line is `[start_seconds] text`):\n",
    ]
    for seg in segments:
        start = float(seg.get("start", 0))
        text = (seg.get("text") or "").strip()
        if text:
            lines.append(f"[{start:.1f}] ({_fmt_ts(start)}) {text}")
    return "\n".join(lines)
