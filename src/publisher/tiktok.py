"""TikTok manual hand-off.

TikTok's Content Posting API is gated (requires application + approval), so until
that's available the Publisher prepares a ready-to-post package per video: the
video file plus a ``caption.txt``. A human uploads it through the TikTok app.
"""

from __future__ import annotations

import os
import shutil


def prepare(asset_path: str, caption: str, dest_root: str, job_id: str) -> str:
    """Copy the video + write a caption file into a per-video folder.

    Returns the package directory.
    """
    if not os.path.exists(asset_path):
        raise FileNotFoundError(f"asset not found: {asset_path}")

    pkg_dir = os.path.join(dest_root, "tiktok", job_id)
    os.makedirs(pkg_dir, exist_ok=True)

    dest_video = os.path.join(pkg_dir, os.path.basename(asset_path))
    shutil.copy2(asset_path, dest_video)

    with open(os.path.join(pkg_dir, "caption.txt"), "w", encoding="utf-8") as fh:
        fh.write(caption + "\n")

    return pkg_dir
