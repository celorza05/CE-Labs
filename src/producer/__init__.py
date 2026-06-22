"""Producer — turns Writer scripts into Higgsfield generation jobs.

This package has two halves:

* **Planner** (this module's ``planner``): reads ``data/scripts/latest.json`` and
  builds a structured generation **job** per script's ``b_roll_prompt`` — prompt,
  aspect ratio, duration, and metadata linking back to the script. This half is
  deterministic, has no external dependency, and is what the submission step
  consumes. It writes ``data/jobs/latest.json``.

* **Submission** (TBD): actually calls Higgsfield to generate each job's video
  and retrieves the finished asset. How that's wired depends on how Higgsfield is
  accessed (REST API key vs. the Cowork/MCP agent layer) — see the repo README.

See ``PIPELINE.md`` for how the Producer fits the wider pipeline.
"""

from .models import GenerationJob

__all__ = ["GenerationJob"]
