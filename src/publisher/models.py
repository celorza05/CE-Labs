"""Data model for a publish result."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class PublishResult:
    """The outcome of publishing one video across the platforms."""

    job_id: str
    title: str
    asset_path: str

    # YouTube
    youtube_status: str = "skipped"  # skipped | planned | uploaded | failed
    youtube_video_id: str | None = None
    youtube_url: str | None = None
    youtube_privacy: str | None = None
    youtube_error: str | None = None

    # TikTok (manual hand-off)
    tiktok_status: str = "skipped"  # skipped | prepared | failed
    tiktok_package_dir: str | None = None
    tiktok_error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
