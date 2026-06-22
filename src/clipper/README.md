# Clipper (clip selection)

The "brain" of the clips pipeline (see [`CLIPS.md`](../../CLIPS.md)). Reads a
timestamped transcript and asks Claude to pick the best short-form moments,
returning exact start/end timestamps + a hook, title, caption, and hashtags for
each. The **Cutter** then uses those timestamps to cut the real footage.

```
data/clips/transcript.json ─► Claude picks the best moments ─► data/clips/clips.json
```

## Why timestamps, not "most replayed"

YouTube's "most replayed" heatmap isn't exposed by the API, so the Clipper
approximates it: Claude reads the full transcript and selects the most quotable,
high-impact, self-contained moments (which is what actually drives clip
performance). If a video shows the replay graph publicly, you can eyeball it and
adjust the picks.

## Input: transcript format

The Clipper reads `data/clips/transcript.json` (produced by the Transcriber):

```json
{
  "source": { "title": "Big Motivational Pod", "url": "https://...", "duration_seconds": 3600 },
  "segments": [
    { "start": 0.0,   "end": 5.0,   "text": "Welcome back to the show." },
    { "start": 120.5, "end": 150.0, "text": "The only thing standing between you and your goal is..." }
  ]
}
```

`start` / `end` are seconds from the source start.

## Run

Needs `ANTHROPIC_API_KEY` (see [`.env.example`](../../.env.example)). From the repo root:

```bash
python -m src.clipper --print          # select clips and print them
python -m src.clipper --top 3          # pick up to 3
python -m src.clipper --show-prompt    # print the prompt only (no API call, no key needed)
```

## Output: `data/clips/clips.json`

```json
{
  "source": { "title": "...", "url": "..." },
  "clips": [
    {
      "start_seconds": 120.5,
      "end_seconds": 150.0,
      "hook": "Your story is the wall.",
      "title": "The Wall Is Your Story",
      "caption": "Mindset shift.",
      "hashtags": ["motivation", "mindset"],
      "reason": "Counterintuitive mic-drop line."
    }
  ]
}
```

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required.** |
| `CLIPPER_MODEL` | `claude-opus-4-8` | Claude model. |
| `CLIPPER_CLIPS_PER_RUN` | `5` | Clips to pick per source. |
| `CLIPPER_CLIP_MIN_SECONDS` | `20` | Min clip length. |
| `CLIPPER_CLIP_MAX_SECONDS` | `60` | Max clip length. |

## Pipeline neighbours

- **Before:** Transcriber (produces `transcript.json`) — not built yet.
- **After:** Cutter (ffmpeg-cuts the source video at each clip's timestamps,
  reframes to 9:16, burns captions) — not built yet — then the existing
  **Publisher**.
