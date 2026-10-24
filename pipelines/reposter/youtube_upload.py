"""YouTube duplicate check and upload via OAuth."""

from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from shared.env import require

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.upload",
]


def _credentials() -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=require("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=require("YOUTUBE_OAUTH_CLIENT_ID"),
        client_secret=require("YOUTUBE_OAUTH_CLIENT_SECRET"),
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds


def upload(
    video_path: Path,
    *,
    title: str,
    description: str,
    tags: list[str],
    privacy: str = "private",
    category_id: str = "22",  # 22 = People & Blogs (broad fit; 28 = Sci & Tech if narrowing)
) -> str:
    """Upload a video file. Returns the new YouTube video ID."""
    if privacy not in ("private", "unlisted", "public"):
        raise ValueError(f"Invalid privacy: {privacy}")

    yt = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)

    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:15],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[upload] {int(status.progress() * 100)}% uploaded", flush=True)

    return response["id"]


def was_reposted(source_url: str) -> bool:
    """Return whether a recent upload records this TikTok as its source."""
    yt = build("youtube", "v3", credentials=_credentials(), cache_discovery=False)
    channels = yt.channels().list(part="contentDetails", mine=True).execute()
    items = channels.get("items") or []
    if not items:
        raise RuntimeError("YouTube did not return an authenticated channel")

    uploads_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    playlist = yt.playlistItems().list(
        part="snippet",
        playlistId=uploads_id,
        maxResults=50,
    ).execute()
    marker = f"Source: {source_url}"
    return any(marker in (item.get("snippet", {}).get("description") or "") for item in playlist.get("items", []))
