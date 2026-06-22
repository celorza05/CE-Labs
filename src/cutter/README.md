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
python -m src.cutter --dry-run            # print the ffmpeg commands; cut nothing
python -m src.cutter --limit 1            # cut just the first clip (check it looks right)
python -m src.cutter --reframe face --limit 1   # face-following crop (needs opencv-python)
python -m src.cutter                      # cut all clips (center crop)
```

## What it does per clip

- **Cut** `[start, end]` from the source (fast input seek).
- **Reframe to 9:16** — two modes:
  - **`center`** (default): fixed center-crop. Fast; good when the speaker is centered.
  - **`face`**: follows the speaker's face via OpenCV (`--reframe face`, needs
    `opencv-python`). It samples the face position and **splits the clip into
    shots wherever the face jumps and stays** (a left↔right camera cut), giving
    one stable crop per shot. The crop switches exactly when the speaker does and
    holds still within a shot — no lag-flash, no mid-shot jitter. (Detecting the
    switch from the *face position* rather than a full-frame scene score is robust
    to podcasts where both shots share the same studio background.)
    *(In a static two-shot where both are on screen at once, it picks the larger
    face, not necessarily the talker — that's where Higgsfield's reframe would do
    better. Tune switch sensitivity with `CUTTER_REFRAME_JUMP_FRACTION`.)*
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
