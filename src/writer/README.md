# Writer (prompt-generator)

The second agent in the CE-Labs pipeline (see [`PIPELINE.md`](../../PIPELINE.md)).
The Writer reads the Scout's ranked trends, **judges which are genuinely
video-worthy**, and writes a punchy hook + 30–60s script + Higgsfield B-roll
prompt for the strongest ones.

## What it does

```
data/trends/latest.json ─► pick the best N (skip off-niche) ─► hook + script + Higgsfield prompt ─► data/scripts/latest.json
```

It hands the top-ranked trends to Claude and asks it to **select** the best
video-worthy ones — deliberately skipping pure politics / policy / lawsuit /
funding-only items that match "AI" as a keyword but make weak, risky shorts.
Output is structured (typed fields), so the Producer stage can consume it
directly.

## Setup

The Writer calls the **Anthropic API**, which needs an API key. This is
**separate from a Claude Pro subscription** — create one at
[console.anthropic.com](https://console.anthropic.com) and add a little credit.

```bash
pip install -r requirements.txt
cp .env.example .env          # then set ANTHROPIC_API_KEY=sk-ant-...
```

## Run

From the **repo root** (run the Scout first so `data/trends/latest.json` exists):

```bash
python -m src.scout                  # produce fresh trends
python -m src.writer --print         # generate scripts and print them
python -m src.writer --top 3         # produce up to 3 scripts
python -m src.writer --show-prompt   # print the assembled prompt only (no API call, no key needed)
```

## Output

Writes to `data/scripts/` (git-ignored — generated, not source):

- `scripts-YYYYMMDD-HHMMSS.json` — a timestamped snapshot
- `latest.json` — the most recent run (what the **Producer** reads next)

Each script:

```json
{
  "source_title": "…",
  "source_url": "https://…",
  "angle": "the sharp one-line take",
  "hook": "first 3 seconds, on screen",
  "script": "~90-150 words of 30-60s narration",
  "title": "platform title",
  "caption": "social caption",
  "hashtags": ["ai", "tech", "…"],
  "b_roll_prompt": "Higgsfield text-to-video prompt for faceless 9:16 B-roll"
}
```

## Configuration

All env-overridable (see [`.env.example`](../../.env.example)):

| Variable | Default | Meaning |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | **Required.** Your Anthropic API key. |
| `WRITER_MODEL` | `claude-opus-4-8` | Claude model. Set `claude-sonnet-4-6` to trade quality for cost. |
| `WRITER_SCRIPTS_PER_RUN` | `5` | Scripts to produce per run (may be fewer if not enough are video-worthy). |
| `WRITER_CANDIDATE_POOL` | `12` | Top trends handed to the model to choose from. |
| `WRITER_VOICE` | `punchy` | `punchy` · `neutral` · `hype`. |

## Next module

The **Producer** reads `data/scripts/latest.json` and drives **Higgsfield** to
generate the actual video from each `b_roll_prompt`.
