# Orchestrator (control room + approval gate)

The fifth and final agent in the CE-Labs pipeline (see [`PIPELINE.md`](../../PIPELINE.md)).
It sequences the other stages, posts status to **Slack**, and holds the
**human approval gate** before anything publishes.

```
prepare:  Scout ─► Writer ─► Producer ─► Slack ("ready for review") ─► STOP
                                                                         │
                                              (you review & approve)     ▼
publish:                                              Publisher ─► Slack ("published")
```

## The approval gate

Publishing is the one irreversible, outward-facing action, so it's a **separate,
deliberate command**. `prepare` does everything up to (and optionally including)
video generation, posts a summary to Slack, and **stops**. You review, then run
`publish` yourself. Nothing reaches a platform without that second step.

## Commands

```bash
python -m src.orchestrator prepare              # Scout->Writer->Producer (plan only; free)
python -m src.orchestrator prepare --generate   # also generate videos via Higgsfield (needs plan/credits)
python -m src.orchestrator publish              # prepare TikTok hand-offs; plan YouTube
python -m src.orchestrator publish --youtube --privacy unlisted
python -m src.orchestrator status               # where the last run left off
```

`prepare` is safe and free by default — it plans generation jobs but doesn't
spend credits unless you pass `--generate` (set `ORCHESTRATOR_GENERATE=true` to
flip the default). `publish` mirrors the Publisher's safety: YouTube uploads only
with `--youtube`, private by default.

## Slack

Set one of these in `.env` and the Orchestrator posts run summaries and approval
prompts there:

- `SLACK_WEBHOOK_URL` — an [Incoming Webhook](https://api.slack.com/messaging/webhooks) URL (simplest, no scopes), **or**
- `SLACK_BOT_TOKEN` + `SLACK_CHANNEL` — a bot token with `chat:write`.

If neither is set, the pipeline still runs — messages are just logged locally.

## State

`data/orchestrator/state.json` records the last run's stage
(`awaiting_approval` → `published`), counts, and whether Slack delivery
succeeded. `status` prints it.

## Putting it together (typical run)

```bash
# 1. produce content and get notified in Slack
python -m src.orchestrator prepare --generate
# 2. review the scripts (data/scripts/latest.json) and videos (data/assets/)
# 3. approve by publishing
python -m src.orchestrator publish --youtube
```
