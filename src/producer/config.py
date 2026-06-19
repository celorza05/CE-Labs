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
