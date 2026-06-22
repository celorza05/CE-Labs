# Clips Orchestrator (control room + approval gate)

The clips analogue of [`src/orchestrator`](../orchestrator/README.md) — sequences
the clips pipeline and holds the human approval gate before publishing.

```
prepare:  Sourcer ─► Transcriber ─► Clipper ─► Cutter ─► Slack ("review") ─► STOP
                                                                              │
                                                  (you review & approve)      ▼
publish:                                                       Publisher ─► Slack ("published")
```

## Commands

```bash
python -m src.clips_orchestrator prepare "<youtube-url | file | rss>" --reframe face
python -m src.clips_orchestrator publish --youtube --privacy unlisted
python -m src.clips_orchestrator status
```

- `prepare` runs Sourcer → Transcriber → Clipper → Cutter, posts a Slack summary
  (clip hooks + timestamps), and stops at `awaiting_approval`.
- `publish` runs the Publisher on the cut clips (`data/clips/out/`) — YouTube only
  with `--youtube` (private by default), TikTok hand-off packages always prepared.
- Slack is optional (reuses the main Orchestrator's `SLACK_*` config); without it,
  summaries are logged locally.

Prereqs are the clips-pipeline deps: `requirements.txt` + `requirements-clips.txt`,
`ffmpeg` on PATH, `ANTHROPIC_API_KEY`, and (for upload) YouTube OAuth.

## Slack approval gate (one-time setup)

The gate is **command-based**: `prepare` posts the clip list + the exact publish
command to Slack and stops; you review the cut clips and run that command to
approve. The simplest way to get the messages delivered is an Incoming Webhook
(no OAuth scopes, no bot user):

1. <https://api.slack.com/apps> → **Create New App** → **From scratch**. Name it
   (e.g. "CE-Labs") and pick your workspace.
2. In the app, open **Incoming Webhooks** → toggle **Activate Incoming Webhooks**
   on.
3. **Add New Webhook to Workspace** → choose the channel to post into → **Allow**.
4. Copy the **Webhook URL** (`https://hooks.slack.com/services/...`) and put it in
   your `.env`:
   ```
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
   ```

Next `prepare`/`publish` run posts to that channel (`slack_delivered: true`).
Prefer a bot token instead? Set `SLACK_BOT_TOKEN` + `SLACK_CHANNEL` (the bot needs
`chat:write` and must be invited to the channel).
