"""Publisher — uploads finished videos to YouTube and prepares TikTok hand-offs.

Takes the Producer's completed assets (``data/jobs/latest.json`` -> asset paths)
plus the Writer's metadata (``data/scripts/latest.json`` -> title, caption,
hashtags) and publishes each one:

* **YouTube** — real upload via the YouTube Data API v3 (uploads as *private* by
  default; nothing goes public without an explicit privacy choice).
* **TikTok** — the content-posting API is gated, so this prepares a manual
  hand-off package (the video + a caption file) for a human to post.

This is the one irreversible, outward-facing stage, so it is safe by default:
running it prepares the TikTok hand-off and *plans* the YouTube upload, but only
actually uploads to YouTube when you pass ``--youtube``.

See ``PIPELINE.md`` for how the Publisher fits the wider pipeline.
"""

from .models import PublishResult

__all__ = ["PublishResult"]
