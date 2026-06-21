# CLIPS.md — Motivational Clips Pipeline (concept / sub-project)

> **Status: planning.** A second pipeline, branched off the main AI-generated
> pipeline (see [`PIPELINE.md`](PIPELINE.md)). Instead of *generating* video, this
> one takes long-form motivational content, cuts the best moments into vertical
> clips, and posts them to TikTok / YouTube Shorts — with an eventual goal of
> monetizing the audience (e.g. supplements).

---

## 0. One-paragraph summary

Ingest a long-form source (podcast / talk / interview **that you have the rights
to use**), transcribe it, let Claude pick the most compelling 20–60s moments,
cut + reframe them to vertical 9:16 with burned-in captions, and publish via the
existing Publisher — behind the same human approval gate.

---

## 1. ⚠️ The decision that gates everything: content rights

This pipeline reposts third-party content, so **copyright is the central risk**,
not a footnote. Clip-and-repost of copyrighted podcasts/videos without a license
or permission is infringement; platforms enforce it (YouTube Content ID, TikTok
copyright detection), and monetizing it — especially selling supplements —
increases strike/ban/legal exposure. "Transformation" / fair-use is narrow and
**not** a reliable shield once you're monetizing.

**Source only rights-cleared content.** Options, roughly best-first:

- **Your own recordings** — interviews/talks you produce. Zero rights risk.
- **Creators who permit clipping** — many podcasters run clip/affiliate/partner
  programs or grant permission on request (often for a credit + link).
- **Licensed / Creative Commons / public-domain** material (e.g. historic speeches).
- **Revenue-share / permission deals** — reach out, offer attribution or a cut.

The technical pipeline below is identical regardless of source — but **which
source you choose determines whether the account survives.** This is the open
question to settle before building the Sourcer (see §5).

---

## 2. How much we reuse from the main pipeline

| Capability | Reuse? |
|---|---|
| **Publisher** (YouTube upload / TikTok hand-off) | ✅ reuse as-is (`src/publisher/`) |
| **Orchestrator** pattern (sequence + Slack + approval gate) | ✅ reuse the pattern |
| `data/`-flow between stages, `.env` config, dotenv loading | ✅ reuse conventions |
| Scout / Writer / Producer | ❌ replaced by clip-specific stages |

So roughly half the work is already done.

---

## 3. Architecture

```
source (rights-cleared) ─► Transcribe ─► Select clips (Claude) ─► Cut + reframe + caption ─► Publish
   (Sourcer)               (Transcriber)   (Clipper)              (Cutter)                  (Publisher ♻)
```

### Stages (new unless noted)

| Stage | Job | Tooling | Status |
|-------|-----|---------|--------|
| **Sourcer** | Take a rights-cleared source file/URL; pull the audio/video. | YouTube (`yt-dlp`), local files, podcast RSS | ✅ `src/sourcer/` |
| **Transcriber** | Timestamped transcript of the audio. | local OpenAI Whisper | ✅ `src/transcriber/` |
| **Clipper** | Claude reads the transcript and picks the strongest 20–60s moments → clip specs. | Anthropic API | ✅ `src/clipper/` |
| **Cutter** | Cut each segment, reframe to 9:16 (face-follow), burn in captions, platform-safe encode. | `ffmpeg` + OpenCV | ✅ `src/cutter/` |
| **Publisher** ♻ | Upload to YouTube / TikTok. | existing `src/publisher/` (`--clips`) | ✅ reuse |
| **Orchestrator** | Sequence the stages + Slack approval gate. | `src/clips_orchestrator/` | ✅ |

### End-to-end

```bash
python -m src.clips_orchestrator prepare "https://youtu.be/VIDEO" --reframe face
#   ... review data/clips/out/ ...
python -m src.clips_orchestrator publish --youtube
```

### Shortcut: Higgsfield already has clip tooling
Higgsfield's CLI/MCP exposes **`clipify`**, **`personal_clipper`**, **`reframe`**
(aspect-ratio change), **`virality_predictor`**, and **`video_analysis`** — which
could do much of the Clipper/Cutter/reframe work instead of hand-rolling ffmpeg.
Worth evaluating once the Higgsfield plan is active (same plan gate as the main
pipeline).

---

## 4. Monetization (later phase)

The "sell supplements" goal is a layer on top of a working channel, not a code
module:

- **TikTok Shop / affiliate links / link-in-bio** to the product.
- Build audience + trust first; products convert on an engaged following.
- **Compliance:** supplements carry FTC rules on health claims and platform-
  specific ad/commerce policies (TikTok Shop has supplement restrictions). Get
  the claims and disclosures right — this is its own checklist before selling.

---

## 5. Open decisions (settle before building)

- [ ] **Content source** (the gating one — see §1): own recordings? permitted
      creators? licensed/CC/public-domain?
- [ ] **Clip length & style** — 20–60s? captions burned in? B-roll/music behind?
- [ ] **Cutter tooling** — ffmpeg (full control, free) vs. Higgsfield clip tools
      (less code, needs the plan).
- [ ] **Transcription** — local Whisper (free, needs setup) vs. API (paid, simple).
- [ ] **Cadence & volume** — clips per source, posts per day.

---

## 6. Suggested build order

1. **Transcriber + Clipper** first (works on any audio you legally have; proves the
   "Claude picks great moments" core cheaply).
2. **Cutter** (ffmpeg or Higgsfield).
3. Wire into the existing **Publisher** + an Orchestrator variant with the approval gate.
4. Monetization layer once a channel is live and growing.
