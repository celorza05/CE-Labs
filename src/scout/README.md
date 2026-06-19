# Scout — trend-fetcher

The first agent in the CE-Labs pipeline (see [`PIPELINE.md`](../../PIPELINE.md)).
Scout discovers trending **AI/tech** topics, filters them to the niche, ranks
and de-duplicates them, and writes the result to `data/trends/`.

## What it does

```
sources ── Hacker News ─┐
           Reddit AI ───┤
           RSS (AI news)─┼─► niche filter ─► rank + de-dup ─► data/trends/latest.json
           Google Trends ┘
```

- **Hacker News** — front page + recent AI search, via the free Algolia API (no key).
- **Reddit** — hot posts from AI subreddits. Anonymous `.json` is blocked from
  many IPs, so set free OAuth credentials (see Configuration) for reliable results.
- **RSS** — AI sections of TechCrunch, The Verge, VentureBeat, Ars Technica.
- **Google Trends** — trending searches via Google's official Trending RSS feed (no key).

Every source **fails soft**: if one is down or rate-limited, Scout logs a warning
and carries on with the rest.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows (Git Bash): source .venv/Scripts/activate
pip install -r requirements.txt
```

## Run

From the **repo root**:

```bash
python -m src.scout                 # fetch, rank, write data/trends/
python -m src.scout --print         # also print the ranked list
python -m src.scout --top 10        # keep only the top 10
python -m src.scout --dry-run       # print only, write nothing
python -m src.scout -v              # verbose / debug logging
```

## Output

Writes two files to `data/trends/` (git-ignored — generated data, not source):

- `trends-YYYYMMDD-HHMMSS.json` — a timestamped snapshot
- `latest.json` — always the most recent run (this is what the **Writer** agent reads next)

Each file looks like:

```json
{
  "generated_at": "2026-06-19T12:00:00+00:00",
  "niche": "AI/tech news & tool breakdowns",
  "count": 25,
  "sources": { "hacker_news": 9, "reddit": 8, "rss": 7, "google_trends": 1 },
  "items": [
    {
      "rank": 1,
      "title": "…",
      "url": "https://…",
      "source": "hacker_news",
      "score": 0.91,
      "matched_keywords": ["llm", "openai"],
      "published": "2026-06-19T09:30:00+00:00"
    }
  ]
}
```

## Configuration

Runs with **no API keys**. Everything is tunable via environment variables —
see [`.env.example`](../../.env.example) (sources to enable, subreddits, RSS
feeds, how many trends to keep, ranking weights, per-source diversity cap).

**Reddit** is the one source that benefits from credentials: anonymous requests
are blocked from many IPs, so create a free "script" app at
<https://www.reddit.com/prefs/apps> and set `SCOUT_REDDIT_CLIENT_ID` /
`SCOUT_REDDIT_CLIENT_SECRET` to fetch via OAuth. Without them Scout still runs;
it just skips Reddit if the public endpoint blocks it.

A **per-source diversity cap** (`SCOUT_MAX_PER_SOURCE`, default 6) stops any one
feed or subreddit from dominating the final list.

## How ranking works

Each source uses a different engagement scale, so raw scores are normalised
*within* their source family, then blended with a freshness score and a
per-source trust weight:

```
score = source_weight × (0.7 × engagement_norm + 0.3 × recency_norm)
```

Sources with no engagement number (RSS, Google Trends) are scored on freshness
and source weight alone. De-duplication drops repeats by canonical URL and by
normalised title, keeping the highest-scoring copy.

## Next module

The **Writer** reads `data/trends/latest.json` and turns the top items into
short-form scripts + Higgsfield prompts.
