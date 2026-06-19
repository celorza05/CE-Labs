# Transcriber (local Whisper)

Second stage of the clips pipeline (see [`CLIPS.md`](../../CLIPS.md)). Reads the
Sourcer's `data/clips/source.json`, transcribes the media with **local Whisper**,
and writes `data/clips/transcript.json` for the Clipper. Free (no per-use cost).

## Install

```bash
pip install -r requirements-clips.txt   # pulls in openai-whisper (+ torch)
```

Also needs **ffmpeg** on your PATH (Whisper uses it to read audio). On Windows,
install ffmpeg and ensure `ffmpeg -version` works in your shell.

## Run

```bash
python -m src.transcriber          # source.json -> transcript.json
```

First run downloads the Whisper model (cached after that). Transcription speed
depends on the model size and your CPU/GPU — on a CPU, `base` is a sensible
default; bump to `small`/`medium` for accuracy if you can wait.

## Output: `data/clips/transcript.json`

```json
{
  "source": { "title": "...", "url": "...", "duration_seconds": 3600 },
  "segments": [
    { "start": 0.0, "end": 3.2, "text": "Welcome back." },
    { "start": 120.55, "end": 150.0, "text": "The story you tell yourself." }
  ]
}
```

This is exactly what the **Clipper** consumes.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `TRANSCRIBER_WHISPER_MODEL` | `base` | `tiny`·`base`·`small`·`medium`·`large`. |
| `TRANSCRIBER_LANGUAGE` | _(auto)_ | Language hint, e.g. `en`. |
