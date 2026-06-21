"""Clips Orchestrator — sequences the clips pipeline with the approval gate.

The clips analogue of ``src/orchestrator`` (see ``CLIPS.md``):

* ``prepare <source>`` — Sourcer -> Transcriber -> Clipper -> Cutter, then posts
  a summary to Slack and **stops** for your review.
* ``publish`` — runs the Publisher on the cut clips (after you approve).
* ``status`` — shows where the last run left off.

Reuses the main Orchestrator's Slack + state helpers. Stages are imported lazily.
"""
