# Sourcer (fetch long-form content)

First stage of the clips pipeline (see [`CLIPS.md`](../../CLIPS.md)). Takes a
YouTube URL, a local file, or a podcast RSS feed and produces a
`data/clips/source.json` descriptor for the Transcriber.

> Use only content you're permitted to use. Downloading from YouTube is also
> restricted by its Terms of Service regardless of ownership — prefer
> creator-provided files where you can.

## Install

```bash
pip install -r requirements-clips.txt   # yt-dlp (+ ffmpeg on PATH for local probing)
```

## Run

```bash
python -m src.sourcer "https://youtu.be/VIDEO_ID"          # YouTube (video)
python -m src.sourcer ./my-interview.mp4                    # local file
python -m src.sourcer "https://feeds.example.com/show.rss" --type podcast --episode 0
```

The type is auto-detected (existing path → local, youtube domain → youtube,
`.rss`/`.xml`/`/feed` → podcast); force it with `--type`.

## Output: `data/clips/source.json`

```json
{
  "title": "Big Motivational Pod — Ep 42",
  "url": "https://youtu.be/...",
  "source_type": "youtube",
  "media_path": "data/clips/media/VIDEO_ID.mp4",
  "has_video": true,
  "duration_seconds": 3600
}
```

`has_video` tells the Cutter whether there's a video track to cut (podcasts are
audio-only and need a visual layer added).

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `SOURCER_MEDIA_DIR` | `data/clips/media` | Where downloaded media lands. |
| `SOURCER_YTDLP_FORMAT` | `bestvideo[height<=1080]+bestaudio/best...` | yt-dlp format. |
| `SOURCER_RSS_EPISODE_INDEX` | `0` | Which podcast episode (0 = newest). |

## Next stage

The **Transcriber** reads `source.json` and produces `transcript.json` for the Clipper.
