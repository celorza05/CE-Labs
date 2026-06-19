"""Orchestrator configuration. All env-overridable (see ``.env.example``)."""

from __future__ import annotations

import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# --- Slack (status + approval prompts) ------------------------------------
# Simplest option: an Incoming Webhook URL (no scopes). Alternatively a bot
# token + channel. If neither is set, messages are just logged locally.
SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL: str = os.getenv("SLACK_CHANNEL", "#content-pipeline")

# Whether `prepare` also generates videos via Higgsfield (costs credits / needs
# a paid plan). Off by default so `prepare` is safe and free.
GENERATE_BY_DEFAULT: bool = _env_bool("ORCHESTRATOR_GENERATE", False)

# Where run state is recorded.
STATE_DIR: str = os.getenv("ORCHESTRATOR_STATE_DIR", "data/orchestrator")
