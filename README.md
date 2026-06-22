# CE-Labs

An automated pipeline for AI-generated short-form video on the **AI/tech** niche.
It finds trending topics, writes punchy scripts, generates faceless vertical
video via Higgsfield, and publishes to YouTube/TikTok — with a human approval
gate before anything goes live.

See [`PIPELINE.md`](PIPELINE.md) for the full spec.

## The agents

| Stage | Agent | Does | Docs |
|-------|-------|------|------|
| 1 | **Scout** | Pulls trending AI/tech topics (Hacker News, RSS, Google Trends), filters, ranks, de-dupes. | [`src/scout`](src/scout/README.md) |
| 2 | **Writer** | Picks the video-worthy trends and writes hook + 30–60s script + Higgsfield prompt (Claude). | [`src/writer`](src/writer/README.md) |
| 3 | **Producer** | Generates the vertical video per script via the Higgsfield CLI; downloads assets. | [`src/producer`](src/producer/README.md) |
| 4 | **Publisher** | Uploads to YouTube (Data API) and prepares TikTok hand-offs. Safe by default. | [`src/publisher`](src/publisher/README.md) |
| 5 | **Orchestrator** | Sequences it all, posts to Slack, holds the approval gate. | [`src/orchestrator`](src/orchestrator/README.md) |

Data flows through `data/` between stages (`trends/` → `scripts/` → `jobs/` +
`assets/` → `publish/`). Generated data is git-ignored.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in the keys you need (see below)
```

Credentials, all optional depending on which stages you run:

- **Writer** → `ANTHROPIC_API_KEY` ([console.anthropic.com](https://console.anthropic.com))
- **Producer** → Higgsfield CLI: `npm install -g @higgsfield/cli` then `higgsfield auth login` (needs a Basic+ plan to generate)
- **Publisher** → YouTube OAuth client (`client_secret.json` from Google Cloud)
- **Orchestrator** → `SLACK_WEBHOOK_URL` (or bot token) for notifications

## Run

Per stage (each writes to `data/` for the next):

```bash
python -m src.scout --print
python -m src.writer --print
python -m src.producer --submit --limit 1      # generate one video (dry-run with --dry-run)
python -m src.publisher --dry-run
```

Or end-to-end via the Orchestrator, with the approval gate:

```bash
python -m src.orchestrator prepare --generate   # produce + post to Slack, then stop
#   ... review the scripts and videos ...
python -m src.orchestrator publish --youtube     # publish only after you approve
```

## Safety notes

- **Approval gate:** the Orchestrator stops after `prepare`; publishing is a
  separate, deliberate `publish` step.
- **YouTube** uploads are **private** by default (`--privacy` to change), and only
  with `--youtube`.
- **TikTok** is a manual hand-off (its posting API is gated).
- Secrets (`.env`, `client_secret.json`, tokens) are git-ignored.
