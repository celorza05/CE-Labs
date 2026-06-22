# Publisher (YouTube upload / TikTok hand-off)

The fourth agent in the CE-Labs pipeline (see [`PIPELINE.md`](../../PIPELINE.md)).
Takes the Producer's finished videos and the Writer's metadata and publishes each.

```
data/jobs/latest.json (assets) ─┐
                                ├─► YouTube upload (Data API v3, private by default)
data/scripts/latest.json (meta) ┘   TikTok hand-off package (manual post)
```

## Safe by default

This is the only irreversible, outward-facing stage, so it won't post publicly
without you asking:

- Running it **prepares the TikTok hand-off** and **plans** the YouTube upload —
  but does **not** upload to YouTube unless you pass `--youtube`.
- YouTube uploads default to **private**. Use `--privacy unlisted|public` to change.
- `--dry-run` previews titles/descriptions and does nothing at all.

(The Orchestrator will gate `--youtube` behind a Slack human approval.)

## YouTube setup (one-time)

1. [Google Cloud Console](https://console.cloud.google.com) → create a project.
2. Enable **YouTube Data API v3**.
3. Create an **OAuth client ID** of type **Desktop app**; download the JSON.
4. Save it as `client_secret.json` in the repo root (or set
   `PUBLISHER_YOUTUBE_CLIENT_SECRET`).
5. First `--youtube` run opens a browser to authorize; the token is cached to
   `data/publish/youtube_token.json` and auto-refreshed after that.

Install the Google libraries (already in `requirements.txt`):

```bash
pip install -r requirements.txt
```

## Run

From the **repo root** (after the Producer has downloaded assets):

```bash
python -m src.publisher --dry-run                     # preview only
python -m src.publisher                                # prepare TikTok; plan YouTube
python -m src.publisher --youtube --limit 1           # upload 1 to YouTube (private)
python -m src.publisher --youtube --privacy unlisted  # upload all as unlisted
```

## TikTok

TikTok's Content Posting API is gated (apply + approval). Until that's granted,
each video gets a hand-off folder at `data/publish/tiktok/<job_id>/` containing
the `.mp4` and a `caption.txt` — a human posts it through the TikTok app.

## Output

- YouTube: uploaded videos (status/url recorded in the report).
- TikTok: per-video packages under `data/publish/tiktok/`.
- `data/publish/latest.json`: a report of what was published / planned.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `PUBLISHER_YOUTUBE_ENABLED` | `true` | Enable the YouTube path. |
| `PUBLISHER_YOUTUBE_CLIENT_SECRET` | `client_secret.json` | OAuth client JSON. |
| `PUBLISHER_YOUTUBE_TOKEN_FILE` | `data/publish/youtube_token.json` | Cached token. |
| `PUBLISHER_YOUTUBE_PRIVACY` | `private` | `private` · `unlisted` · `public`. |
| `PUBLISHER_YOUTUBE_CATEGORY_ID` | `28` | 28 = Science & Technology. |
| `PUBLISHER_TIKTOK_ENABLED` | `true` | Prepare TikTok hand-off packages. |

## Next module

The **Orchestrator** sequences Scout → Writer → Producer → Publisher, posts
status to Slack, and holds the human approval gate before this stage publishes.
