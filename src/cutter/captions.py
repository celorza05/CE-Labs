"""Build burned-in captions (ASS subtitles) for a clip.

Takes the transcript segments that fall inside a clip's [start, end] window,
re-times them to clip-relative time (so they line up with the cut), and renders
an ASS file styled for big, centered, motivational-style captions.
"""

from __future__ import annotations

from . import config


def segments_in_clip(segments: list[dict], start: float, end: float) -> list[dict]:
    """Transcript segments overlapping [start, end], re-timed to clip-relative."""
    out: list[dict] = []
    for s in segments:
        a = float(s.get("start", 0.0))
        b = float(s.get("end", 0.0))
        if b <= start or a >= end:
            continue
        text = (s.get("text") or "").strip()
        if not text:
            continue
        out.append({
            "start": max(a, start) - start,
            "end": min(b, end) - start,
            "text": text,
        })
    return out


def _fmt_time(t: float) -> str:
    """ASS timestamp: H:MM:SS.cc"""
    if t < 0:
        t = 0.0
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:d}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def build_ass(caps: list[dict], width: int | None = None, height: int | None = None) -> str:
    w = width or config.WIDTH
    h = height or config.HEIGHT
    # Alignment 2 = bottom-center; MarginV lifts captions off the bottom edge.
    margin_v = int(h * 0.12)
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {w}\n"
        f"PlayResY: {h}\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
        "Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{config.FONT_NAME},{config.FONT_SIZE},&H00FFFFFF,&H00000000,&H00000000,"
        f"-1,0,0,0,100,100,0,0,1,4,1,2,80,80,{margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    lines = [header]
    for c in caps:
        lines.append(
            f"Dialogue: 0,{_fmt_time(c['start'])},{_fmt_time(c['end'])},Default,,0,0,0,,{_escape(c['text'])}"
        )
    return "\n".join(lines) + "\n"
