"""Scout configuration.

Everything here has a sensible default so the Scout runs out of the box with no
API keys. Any value can be overridden with an environment variable (see
``.env.example``), which keeps secrets and per-environment tweaks out of the code.
"""

from __future__ import annotations

import os

# Load a local .env file if one exists, so credentials and overrides in .env
# take effect without being exported into the shell. No-op if python-dotenv
# isn't installed or there's no .env.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# How many ranked trends to keep in the final output.
TOP_N: int = _env_int("SCOUT_TOP_N", 25)

# HTTP behaviour shared by every source.
HTTP_TIMEOUT: int = _env_int("SCOUT_HTTP_TIMEOUT", 15)
USER_AGENT: str = os.getenv(
    "SCOUT_USER_AGENT",
    "CE-Labs-Scout/0.1 (+https://github.com/celorza05/CE-Labs)",
)

# --- Source toggles -------------------------------------------------------
ENABLE_HACKER_NEWS: bool = _env_bool("SCOUT_ENABLE_HACKER_NEWS", True)
# Reddit is off by default: it needs OAuth credentials (a free "script" app)
# because anonymous requests are IP-blocked. Set SCOUT_ENABLE_REDDIT=true plus
# the credentials below to turn it on.
ENABLE_REDDIT: bool = _env_bool("SCOUT_ENABLE_REDDIT", False)
ENABLE_RSS: bool = _env_bool("SCOUT_ENABLE_RSS", True)
ENABLE_GOOGLE_TRENDS: bool = _env_bool("SCOUT_ENABLE_GOOGLE_TRENDS", True)

# --- Reddit ---------------------------------------------------------------
SUBREDDITS: list[str] = _env_list(
    "SCOUT_SUBREDDITS",
    ["LocalLLaMA", "artificial", "MachineLearning", "OpenAI", "singularity"],
)
REDDIT_LIMIT: int = _env_int("SCOUT_REDDIT_LIMIT", 25)
# Reddit blocks anonymous JSON from many IPs. Set these (free "script" app at
# https://www.reddit.com/prefs/apps) to fetch via authenticated OAuth instead.
REDDIT_CLIENT_ID: str = os.getenv("SCOUT_REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET: str = os.getenv("SCOUT_REDDIT_CLIENT_SECRET", "")

# --- RSS ------------------------------------------------------------------
RSS_FEEDS: list[str] = _env_list(
    "SCOUT_RSS_FEEDS",
    [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://venturebeat.com/category/ai/feed/",
        "https://arstechnica.com/ai/feed/",
    ],
)

# --- Google Trends --------------------------------------------------------
# pytrends is unofficial and occasionally flaky; the source degrades gracefully.
GOOGLE_TRENDS_GEO: str = os.getenv("SCOUT_GOOGLE_TRENDS_GEO", "US")

# --- Ranking --------------------------------------------------------------
# Relative trust per source family, used as a multiplier on the blended score.
SOURCE_WEIGHTS: dict[str, float] = {
    "hacker_news": 1.0,
    "reddit": 0.9,
    "rss": 0.8,
    "google_trends": 0.7,
}
# How the blended score splits between engagement and freshness.
ENGAGEMENT_WEIGHT: float = 0.7
RECENCY_WEIGHT: float = 0.3
# Age (hours) at which the recency score decays to roughly zero.
RECENCY_HALFLIFE_HOURS: float = float(os.getenv("SCOUT_RECENCY_HALFLIFE_HOURS", "36"))
# Diversity cap: at most this many items from any single source (e.g. one RSS
# feed or one subreddit) in the final ranked list. 0 disables the cap.
MAX_PER_SOURCE: int = _env_int("SCOUT_MAX_PER_SOURCE", 6)

# Where ranked trends are written.
OUTPUT_DIR: str = os.getenv("SCOUT_OUTPUT_DIR", "data/trends")
