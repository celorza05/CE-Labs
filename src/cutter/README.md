# Cutter (ffmpeg: cut + reframe + captions)

Fourth stage of the clips pipeline (see [`CLIPS.md`](../../CLIPS.md)). Turns the
Clipper's timestamps into finished vertical clips: cut the segment, reframe to
9:16, and **burn in captions** from the transcript. Output → `data/clips/out/`.

```
clips.json + source media + transcript ─► ffmpeg (cut, crop 9:16, ASS captions) ─► data/clips/out/<clip>.mp4
```

Free and local — needs **ffmpeg** on your PATH.

## Install ffmpeg

- **Windows:** `winget install Gyan.FFmpeg` (or download from ffmpeg.org and add to PATH). Verify with `ffmpeg -version`.
- **macOS:** `brew install ffmpeg`
- **Linux:** `sudo apt install ffmpeg`

## Run

```bash
python -m src.cutter --dry-run     # print the ffmpeg commands; cut nothing
python -m src.cutter --limit 1     # cut just the first clip (check it looks right)
python -m src.cutter               # cut all clips
```

## What it does per clip

- **Cut** `[start, end]` from the source (fast input seek).
- **Reframe to 9:16** — center-crop to vertical, scale to 1080×1920. (Simple
  center-crop; good for centered talking-head footage. Face-tracking crop is a
  future upgrade if framing isn't tight enough — or switch the Cutter to
  Higgsfield's `reframe`.)
- **Burn captions** — transcript segments inside the clip window, re-timed to the
  clip and rendered as styled ASS subtitles (big, bold, centered, outlined).
- **Audio-only sources** (podcasts): renders captions over a solid background so
  there's still a postable vertical video.

## Output

- `data/clips/out/<NN>-<slug>.mp4` — the finished clips (git-ignored).
- `data/clips/out/report.json` — per-clip status.

These feed the **Publisher** (`src/publisher/`) — point it at the clip files, or
adapt the Publisher's job input to `data/clips/out/`.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CUTTER_FFMPEG_BIN` | `ffmpeg` | ffmpeg command. |
| `CUTTER_WIDTH` / `CUTTER_HEIGHT` | `1080` / `1920` | Output canvas. |
| `CUTTER_FONT_NAME` / `CUTTER_FONT_SIZE` | `Arial` / `72` | Caption style. |
| `CUTTER_BG_COLOR` | `black` | Background for audio-only sources. |
