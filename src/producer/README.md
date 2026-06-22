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

## 2. Submission (Higgsfield CLI)

The submission step generates each job's video via the **official Higgsfield
CLI** and downloads the asset. The CLI is the right fit here — Higgsfield
positions it as faster/simpler than MCP for automated workflows, and it's
scriptable, so the Producer runs as a normal script (no live agent session).

One-time setup on the machine that runs this:

```bash
npm install -g @higgsfield/cli   # needs Node.js
higgsfield auth login            # cached session
```

Then:

```bash
python -m src.producer --submit --dry-run   # print the exact CLI commands, generate NOTHING
python -m src.producer --submit --limit 1   # generate just the first video (test before spending)
python -m src.producer --submit             # generate all planned videos
```

Under the hood it runs, per job:

```bash
higgsfield generate create <model> --prompt "<b_roll_prompt>" \
  --duration 5 --mode pro --sound off --aspect-ratio 9:16 --wait --json
```

parses the returned asset URL, downloads the video to `data/assets/<job_id>.mp4`,
and records `status` / `asset_url` / `asset_path` back into `data/jobs/latest.json`.

**Always run `--dry-run` first** to eyeball the exact command — the model id and
some flags (e.g. the aspect-ratio flag name) may differ for your account, and
every real generation costs credits. Adjust via the `PRODUCER_CLI_*` env vars in
[`.env.example`](../../.env.example); `higgsfield model list` shows valid models.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PRODUCER_ASPECT_RATIO` | `9:16` | Vertical short-form. |
| `PRODUCER_DURATION_SECONDS` | `5` | Per-clip length. |
| `PRODUCER_SCRIPTS_INPUT` | `data/scripts/latest.json` | Writer output to read. |
| `PRODUCER_OUTPUT_DIR` | `data/jobs` | Where the plan is written. |
| `PRODUCER_ASSETS_DIR` | `data/assets` | Where generated videos are downloaded. |
| `PRODUCER_CLI_BIN` | `higgsfield` | CLI command (alias `higgs`). |
| `PRODUCER_HIGGSFIELD_MODEL` | `kling3_0` | Video model — see `higgsfield model list`. |
| `PRODUCER_CLI_MODE` | `pro` | Generation mode flag. |
| `PRODUCER_CLI_SOUND` | `off` | Sound flag. |
| `PRODUCER_CLI_ASPECT_FLAG` | `--aspect-ratio` | Aspect-ratio flag name (blank to omit). |
| `PRODUCER_CLI_EXTRA_FLAGS` | _(blank)_ | Extra flags appended to every call. |
| `PRODUCER_CLI_TIMEOUT` | `600` | Seconds to wait per generation. |

## Next module

The **Publisher** takes approved assets and uploads them (YouTube Data API;
TikTok manual hand-off until API access is approved).
