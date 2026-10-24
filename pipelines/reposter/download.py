"""Download an authorized TikTok video; no cookie or account state is bundled."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import httpx
import yt_dlp
from yt_dlp.networking.impersonate import ImpersonateTarget

_PLAYER_API = "https://www.tiktok.com/player/api/v1/items"
_VIDEO_ID_RE = re.compile(r"/video/(\d+)")


class QuietLogger:
    """Do not emit provider responses, signed URLs, or session information."""

    def debug(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass


def _select_player_url(item: dict[str, Any]) -> str:
    video_info = item.get("video_info") or {}
    profiles = video_info.get("profiles") or []
    h264_profiles = [profile for profile in profiles if profile.get("codec_type") == "h264"]
    candidates = h264_profiles or profiles
    candidates.sort(
        key=lambda profile: (profile.get("height") or 0, profile.get("bitrate") or 0),
        reverse=True,
    )

    for profile in candidates:
        urls = (profile.get("play_addr") or {}).get("url_list") or []
        if urls:
            return urls[0]

    urls = video_info.get("url_list") or []
    if urls:
        return urls[0]
    raise RuntimeError("TikTok player API returned no downloadable video URL")


def _download_from_player_api(url: str, dest_dir: Path) -> Path:
    match = _VIDEO_ID_RE.search(url)
    if not match:
        raise RuntimeError("TikTok URL does not contain a video ID")

    video_id = match.group(1)
    destination = dest_dir / "video.mp4"
    headers = {
        "Referer": f"https://www.tiktok.com/player/v1/{video_id}",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        ),
    }

    with httpx.Client(headers=headers, follow_redirects=True, timeout=60) as client:
        response = client.get(
            _PLAYER_API,
            params={
                "item_ids": video_id,
                "language": "en",
                "aid": "1459",
                "data_source": "web_core",
            },
        )
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items") or []
        if not items:
            raise RuntimeError("TikTok player API returned no video data")

        media_url = _select_player_url(items[0])
        with client.stream("GET", media_url) as media:
            media.raise_for_status()
            with destination.open("wb") as output:
                for chunk in media.iter_bytes():
                    output.write(chunk)

    if not destination.exists() or destination.stat().st_size == 0:
        raise RuntimeError("TikTok player API produced an empty video")
    return destination


def _download_with_ytdlp(url: str, dest_dir: Path) -> Path:
    out_template = str(dest_dir / "video.%(ext)s")

    opts = {
        "outtmpl": out_template,
        "format": "best[ext=mp4]/best",
        # TikTok challenges GitHub-hosted runner traffic based on its TLS
        # fingerprint. curl-cffi lets yt-dlp make this request like Chrome.
        "impersonate": ImpersonateTarget.from_str("chrome"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": QuietLogger(),
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)

    ext = info.get("ext") or "mp4"
    candidate = dest_dir / f"video.{ext}"
    if not candidate.exists():
        # Fallback: yt-dlp sometimes picks a different extension; find any video.*
        matches = list(dest_dir.glob("video.*"))
        if not matches:
            raise RuntimeError(f"yt-dlp said it downloaded but no file at {dest_dir}")
        candidate = matches[0]

    if candidate.stat().st_size == 0:
        raise RuntimeError(f"yt-dlp produced an empty file: {candidate}")

    return candidate


def download_tiktok(url: str, dest_dir: Path) -> Path:
    """Pull the video to dest_dir/video.<ext>. Returns the resulting file path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        return _download_from_player_api(url, dest_dir)
    except Exception:
        print("[download] Player download unavailable; trying yt-dlp.")
        return _download_with_ytdlp(url, dest_dir)
