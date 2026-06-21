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
