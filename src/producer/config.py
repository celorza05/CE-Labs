"""Producer configuration. All env-overridable (see ``.env.example``)."""

from __future__ import annotations

import os

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


# Generation defaults applied to every job (mapped to Higgsfield params at
# submission time).
ASPECT_RATIO: str = os.getenv("PRODUCER_ASPECT_RATIO", "9:16")
DURATION_SECONDS: int = _env_int("PRODUCER_DURATION_SECONDS", 5)
# Higgsfield model id. Left blank until the access method is confirmed; the
# submission step resolves a sensible default if this is empty.
MODEL: str = os.getenv("PRODUCER_HIGGSFIELD_MODEL", "")

# I/O paths.
SCRIPTS_INPUT: str = os.getenv("PRODUCER_SCRIPTS_INPUT", "data/scripts/latest.json")
OUTPUT_DIR: str = os.getenv("PRODUCER_OUTPUT_DIR", "data/jobs")
ASSETS_DIR: str = os.getenv("PRODUCER_ASSETS_DIR", "data/assets")

# --- Higgsfield CLI submission ----------------------------------------------
# Official CLI: `npm install -g @higgsfield/cli`, then `higgsfield auth login`.
# Command name (alias: "higgs").
CLI_BIN: str = os.getenv("PRODUCER_CLI_BIN", "higgsfield")
# Video model id. `higgsfield model list` shows what's available.
CLI_MODEL: str = os.getenv("PRODUCER_HIGGSFIELD_MODEL", "kling3_0")
CLI_MODE: str = os.getenv("PRODUCER_CLI_MODE", "pro")
CLI_SOUND: str = os.getenv("PRODUCER_CLI_SOUND", "off")
# Aspect-ratio flag name. Higgsfield params are passed as --<param_name>, and the
# param is `aspect_ratio` (underscore) — verified via `higgsfield model get kling3_0`.
# Set blank to omit if a model derives ratio another way.
CLI_ASPECT_FLAG: str = os.getenv("PRODUCER_CLI_ASPECT_FLAG", "--aspect_ratio")
# How long the CLI's own --wait blocks for a generation to finish (CLI duration
# string, e.g. "15m"). Blank to omit the flag and use the CLI's default.
CLI_WAIT_TIMEOUT: str = os.getenv("PRODUCER_CLI_WAIT_TIMEOUT", "15m")
# Any extra flags to append, space-separated (e.g. "--quality high").
CLI_EXTRA_FLAGS: str = os.getenv("PRODUCER_CLI_EXTRA_FLAGS", "")
# Our subprocess kill deadline (seconds). Keep above CLI_WAIT_TIMEOUT.
CLI_TIMEOUT: int = _env_int("PRODUCER_CLI_TIMEOUT", 1080)
