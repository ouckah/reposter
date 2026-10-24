"""Discover the latest TikTok directly through TikTok's official API."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from shared.env import require

TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"


@dataclass(frozen=True)
class TikTokPost:
    id: str
    url: str
    caption: str
    created_at: int
    is_photo_post: bool


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=20), reraise=True)
def _access_token() -> str:
    response = httpx.post(
        TOKEN_URL,
        data={
            "client_key": require("TIKTOK_OAUTH_CLIENT_KEY"),
            "client_secret": require("TIKTOK_OAUTH_CLIENT_SECRET"),
            "refresh_token": require("TIKTOK_OAUTH_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError("TikTok token response did not contain an access token")
    return str(token)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=20), reraise=True)
def _recent_videos(access_token: str) -> list[dict]:
    response = httpx.post(
        f"{VIDEO_LIST_URL}?fields=id,title,video_description,share_url,create_time,duration",
        headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
        json={"max_count": 20},
        timeout=15,
    )
    response.raise_for_status()
    return list((response.json().get("data") or {}).get("videos") or [])


def find_latest() -> TikTokPost:
    videos = _recent_videos(_access_token())
    candidates = [_from_api(video) for video in videos if video.get("share_url")]
    if not candidates:
        raise RuntimeError("TikTok returned no recent videos")
    return max(candidates, key=lambda post: post.created_at)


def find_by_url(url: str) -> TikTokPost:
    canonical = _canonical_url(url)
    for video in _recent_videos(_access_token()):
        post = _from_api(video)
        if post.url == canonical:
            return post
    raise RuntimeError("The requested URL was not found in TikTok's 20 most recent videos")


def _from_api(video: dict) -> TikTokPost:
    return TikTokPost(
        id=str(video.get("id") or ""),
        url=_canonical_url(str(video.get("share_url") or "")),
        caption=str(video.get("video_description") or video.get("title") or "").strip(),
        created_at=int(video.get("create_time") or 0),
        # TikTok's Display API reports a zero duration for photo posts.
        is_photo_post=video.get("duration") == 0,
    )


def _canonical_url(url: str) -> str:
    return url.split("?", 1)[0].rstrip("/")
