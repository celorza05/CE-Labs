# Producer (Higgsfield generation)

The third agent in the CE-Labs pipeline (see [`PIPELINE.md`](../../PIPELINE.md)).
The Producer turns the Writer's scripts into actual video via **Higgsfield**.

It has two halves:

```
data/scripts/latest.json ──► [planner] ──► data/jobs/latest.json ──► [submission] ──► video assets
                              (this module)                          (Higgsfield)
```

## 1. Planner (built)

Reads `data/scripts/latest.json` and turns each script's `b_roll_prompt` into a
structured **generation job** — prompt, aspect ratio (9:16), duration, and the
metadata to tie the finished asset back to its script. Deterministic, no external
dependency.

```bash
python -m src.producer --print      # build data/jobs/latest.json
```

Each job:

```json
{
  "job_id": "01-photoshop-now-has-a-chatbot",
  "source_title": "…",
  "source_url": "https://…",
  "prompt": "the script's b_roll_prompt",
  "aspect_ratio": "9:16",
  "duration_seconds": 5,
  "model": "",
  "script_title": "…",
  "hook": "…",
  "status": "pending",
  "higgsfield_job_id": null,
  "asset_url": null
}
```

## 2. Submission (pending access decision)

The submission step actually calls Higgsfield to generate each job's video and
fills in `status` / `higgsfield_job_id` / `asset_url`. **How** it calls
Higgsfield depends on how the account is accessed:

- **REST API key** → a standalone `HiggsfieldClient` in this package, run like the
  Scout/Writer (submit job → poll status → download asset).
- **Connected app / MCP integration** → generation runs through the Cowork/agent
  layer that holds the Higgsfield tools; the planner's `data/jobs/latest.json` is
  the work queue it consumes.

This half is intentionally not implemented until the access method is confirmed,
to avoid coding against an unverified interface.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PRODUCER_ASPECT_RATIO` | `9:16` | Vertical short-form. |
| `PRODUCER_DURATION_SECONDS` | `5` | Per-clip length. |
| `PRODUCER_HIGGSFIELD_MODEL` | _(blank)_ | Higgsfield model id; resolved at submission. |
| `PRODUCER_SCRIPTS_INPUT` | `data/scripts/latest.json` | Writer output to read. |
| `PRODUCER_OUTPUT_DIR` | `data/jobs` | Where the plan is written. |

## Next module

The **Publisher** takes approved assets and uploads them (YouTube Data API;
TikTok manual hand-off until API access is approved).
