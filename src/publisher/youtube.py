"""YouTube Data API v3 upload.

Uploads a local video via ``videos.insert`` (resumable). Auth is OAuth 2.0:
the first run opens a browser to authorize, then the token is cached and
refreshed automatically.

The google libraries are imported lazily so the rest of the Publisher works
without them installed.

One-time setup:
  1. Google Cloud Console -> create a project -> enable "YouTube Data API v3".
  2. Create an OAuth client ID of type "Desktop app"; download the JSON.
  3. Save it as the path in PUBLISHER_YOUTUBE_CLIENT_SECRET (default client_secret.json).
"""

from __future__ import annotations

import logging
import os

from . import config

log = logging.getLogger("publisher.youtube")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_service():
    """Build an authenticated YouTube API client, running OAuth if needed."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - depends on optional libs
        raise RuntimeError(
            "YouTube upload needs the Google API libraries. Install them: "
            "pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
        ) from exc

    creds = None
    token_file = config.YOUTUBE_TOKEN_FILE
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(config.YOUTUBE_CLIENT_SECRET):
                raise RuntimeError(
                    f"OAuth client secret not found at {config.YOUTUBE_CLIENT_SECRET}. "
                    "Create an OAuth Desktop client in Google Cloud Console and save the JSON there."
                )
            flow = InstalledAppFlow.from_client_secrets_file(config.YOUTUBE_CLIENT_SECRET, SCOPES)
            creds = flow.run_local_server(port=0)
        os.makedirs(os.path.dirname(token_file) or ".", exist_ok=True)
        with open(token_file, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy: str,
    category_id: str | None = None,
    made_for_kids: bool | None = None,
) -> tuple[str, str]:
    """Upload one video. Returns (video_id, watch_url)."""
    from googleapiclient.http import MediaFileUpload

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"asset not found: {video_path}")

    service = _get_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id or config.YOUTUBE_CATEGORY_ID,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": (
                config.YOUTUBE_MADE_FOR_KIDS if made_for_kids is None else made_for_kids
            ),
        },
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/*")
    request = service.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info("uploading %s: %d%%", os.path.basename(video_path), int(status.progress() * 100))

    video_id = response["id"]
    return video_id, f"https://youtu.be/{video_id}"
