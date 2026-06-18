# PIPELINE.md — AI-Generated Short-Form Content Pipeline

> **Source of truth.** Every agent and script in this project reads from this
> document. If behavior and this spec disagree, this spec wins — fix the code
> or fix the spec, don't let them drift.

---

## 0. One-paragraph summary

An automated pipeline that finds trending **AI/tech** topics, turns them into
short-form video prompts, generates faceless text-on-screen + B-roll videos via
**Higgsfield**, and publishes to **YouTube Shorts** and **TikTok** — with a
human approval gate in Slack before anything goes live. Code is versioned in
**GitHub**; orchestration and approvals happen in **Slack**.

---

## 1. Niche (locked)

**AI/tech news & tool breakdowns.**

Decided after comparing AI vs. finance vs. sports for a faceless, AI-generated,
automatable pipeline:

| Niche | Verdict | Why |
|-------|---------|-----|
| **AI/tech** | ✅ **Chosen** | Fastest-growing trending niche; faceless format is native (nobody expects a human face in a tool demo); topic supply is infinite and self-refreshing (every model/tool launch is a video); low liability. The pipeline *is* AI tools, so it makes content about the exact thing it uses. |
| Finance | ❌ | Highest CPM, but rewards a human face/trust signals and carries real liability — AI-generated financial "advice" that's wrong is the fastest way to get flagged. |
| Sports | ❌ | Value is tied to live moments, real footage, and real athletes — copyright/likeness landmines with generated video. Didn't surface as a top automatable niche. |

**The edge is a sharp angle, not throughput.** YouTube doesn't ban automation,
but it does suppress low-quality, misleading, or repetitive content regardless
of how it's made. AI should sharpen a unique take, not replace one.

---

## 2. Content format (locked)

- **Faceless**, text-on-screen + AI-generated B-roll explainers.
- **Length:** 30–60 seconds.
- **Structure:** Hook (first 3 seconds is make-or-break), 1 clear idea, payoff/CTA.
- **One idea per video.** Each trending item = one short.

---

## 3. Three-phase architecture

    PLANNING            BUILDING              EXECUTING
    (Claude chat)       (Claude Code)         (Cowork + Slack)
    ----------          -------------         ----------------
    decisions &         versioned,            run on cadence,
    this PIPELINE.md -> rerunnable scripts -> approve in Slack,
                        committed to GitHub   publish

### Phase 1 — Planning (Claude chat)
Decisions and documents, no running code. **Output:** this `PIPELINE.md`.
Settles niche, format, cadence, channel identity. **Status: complete** (this doc).

### Phase 2 — Building (Claude Code, terminal)
Where the versioned scripts get written and committed. See §5 for the modules.

### Phase 3 — Executing (Claude Cowork + Slack)
Cowork runs the pipeline on a cadence, posts status to Slack
("3 videos generated, awaiting approval"), and waits for human approve/reject
**before** the publish step. Slack is the control room and approval gate.

---

## 4. Agents (roles, not separate AI entities)

Each is a script or a Cowork task with exactly one job. Clean handoffs make the
system debuggable when one stage breaks.

| Agent | Job | Phase | Reads | Writes |
|-------|-----|-------|-------|--------|
| **Scout** | Discover trending AI/tech topics | Building | trend sources | `data/trends/*.json` |
| **Writer** | Turn a trend into a short-form script + Higgsfield prompt | Building | a trend item | `data/scripts/*.json` |
| **Producer** | Drive Higgsfield generation, retrieve assets | Building | a script/prompt | `data/assets/*.mp4` |
| **Publisher** | Upload to YouTube / TikTok | Building | an approved asset | platform post IDs |
| **Orchestrator** | Sequence the agents, report to Slack, hold the approval gate | Executing | all of the above | Slack messages |

---

## 5. Build modules (Phase 2 backlog)

Status legend: [ ] not started · [~] in progress · [x] done

| Module | Maps to | Status | Notes |
|--------|---------|--------|-------|
| `trend-fetcher` | Scout | [ ] | Pull from AI-specific sources, filter to niche, dedupe, rank. Runs on a schedule. |
| `prompt-generator` | Writer | [ ] | Calls the Anthropic API so Claude writes the hook + script + Higgsfield prompt. |
| `higgsfield-client` | Producer | [ ] | Calls Higgsfield generation API, polls for completion, downloads finished assets. |
| `upload-youtube` | Publisher | [ ] | YouTube Data API v3 (`videos.insert`). Real, scriptable API. |
| `upload-tiktok` | Publisher | [ ] | **Gated** — see §6. Manual hand-off until/unless API access is approved. |
| `orchestrator` | Orchestrator | [ ] | Sequences stages, posts to Slack, enforces approval gate. Lives in Cowork. |

### Suggested repo layout

    CE-Labs/
      PIPELINE.md            # this file — source of truth
      README.md
      src/
        scout/              # trend-fetcher
        writer/             # prompt-generator
        producer/           # higgsfield-client
        publisher/          # upload-youtube, upload-tiktok
        orchestrator/
      data/
        trends/             # Scout output
        scripts/            # Writer output
        assets/             # Producer output (gitignored — large/binary)
      .env.example          # API keys (never commit real keys)

---

## 6. Reality checks (the honest constraints)

1. **No native "upload to TikTok/YouTube" connector exists in this setup.**
   - **YouTube:** has a real, scriptable API (Data API v3). This automates cleanly.
   - **TikTok:** the Content Posting API is **gated** — you must apply for access
     and it's restrictive. Until approved, TikTok is a **manual hand-off**: the
     pipeline produces the file + caption, a human posts it.
2. **Human approval gate is mandatory before publish.** The Orchestrator must
   stop and wait for a Slack approval before the Publisher runs. This is the
   safety checkpoint for the one irreversible, outward-facing step.
3. **Automation is not spam.** Volume without a unique angle gets suppressed.
   Quality gate belongs in the Writer (is the angle sharp?) and the human approval step.
4. **Secrets never get committed.** API keys go in `.env` (gitignored); commit
   only `.env.example` with placeholder names.

---

## 7. Required credentials (collect during Building)

| Service | Used by | Access notes |
|---------|---------|--------------|
| Anthropic API | Writer | Pro plan covers Claude Code; API key from console for scripts. |
| Higgsfield API | Producer | Generation + asset retrieval. |
| YouTube Data API v3 | Publisher | OAuth client + token; `videos.insert` scope. |
| TikTok Content Posting API | Publisher | **Apply for access** — gated. Manual until approved. |
| Slack | Orchestrator | Bot token for status messages + approval interactions. |
| GitHub | all | Already connected for version control. |

---

## 8. Open decisions (Phase 1 leftovers to confirm)

These don't block scaffolding but should be pinned before going live:

- [ ] **Posting cadence** — how many videos/day per platform?
- [ ] **Channel identity** — names, handles, avatars, descriptions for each platform.
- [ ] **Trend sources** — confirm the exact source list for the Scout
      (e.g. product launches, Hacker News, AI subreddits, model-release feeds).
- [ ] **Approval policy** — approve each video individually, or batch-approve a day's run?

---

## 9. Definition of done (v1)

The pipeline is "v1 live" when:
1. Scout produces a ranked daily list of AI/tech trends.
2. Writer turns the top N into hooks + scripts + Higgsfield prompts.
3. Producer generates the videos and stores assets.
4. Orchestrator posts them to Slack and waits for approval.
5. On approval, Publisher uploads to YouTube (TikTok manual until API approved).

Everything before the publish step automates end-to-end; the publish step keeps
a human in the loop by design.
