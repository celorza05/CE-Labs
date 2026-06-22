"""Writer configuration.

The Writer needs an Anthropic API key (``ANTHROPIC_API_KEY``) — that's separate
from a Claude Pro subscription; create one at https://console.anthropic.com and
put it in ``.env``. Everything else has a sensible default and is env-overridable
(see ``.env.example``).
"""

from __future__ import annotations

import os

# Load a local .env file if present (so ANTHROPIC_API_KEY and overrides apply
# without exporting them). No-op if python-dotenv or the file is absent.
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


# Anthropic model. Defaults to the most capable Claude model; override with a
# cheaper one (e.g. claude-sonnet-4-6) via env if you want to trade quality for cost.
MODEL: str = os.getenv("WRITER_MODEL", "claude-opus-4-8")
MAX_TOKENS: int = _env_int("WRITER_MAX_TOKENS", 16000)

# How many scripts to produce per run (the Writer may return fewer if not enough
# trends are genuinely video-worthy).
SCRIPTS_PER_RUN: int = _env_int("WRITER_SCRIPTS_PER_RUN", 5)

# How many top-ranked trends to hand the model to choose from. Bigger pool ->
# more room to skip the off-niche ones and still fill SCRIPTS_PER_RUN.
CANDIDATE_POOL: int = _env_int("WRITER_CANDIDATE_POOL", 12)

# Voice/style key — see prompts.VOICES.
VOICE: str = os.getenv("WRITER_VOICE", "punchy")

# Don't script more than this many videos about the same company/product per run,
# so one brand can't dominate a day's content.
MAX_PER_COMPANY: int = _env_int("WRITER_MAX_PER_COMPANY", 2)

# I/O paths.
TRENDS_INPUT: str = os.getenv("WRITER_TRENDS_INPUT", "data/trends/latest.json")
OUTPUT_DIR: str = os.getenv("WRITER_OUTPUT_DIR", "data/scripts")
