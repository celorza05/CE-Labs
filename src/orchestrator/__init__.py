"""Orchestrator — sequences the pipeline and holds the human approval gate.

The control room from ``PIPELINE.md`` (Phase 3). It runs the stages in order and
keeps a human checkpoint right before the irreversible publish step:

* ``prepare`` — Scout -> Writer -> Producer (plan, and optionally generate), then
  posts a summary to Slack and **stops**, awaiting your review.
* ``publish`` — runs the Publisher. You only run this *after* approving what
  ``prepare`` produced. This is the approval gate: publishing is a deliberate,
  separate human action.
* ``status`` — shows where the last run left off.

Each stage is imported lazily, so this package loads even if a given stage's
dependencies aren't installed.
"""
