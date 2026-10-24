"""Preview by default; upload only with explicit opt-in."""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from pipelines.reposter import adapter, discovery, download, youtube_upload
from shared.env import load_env


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--demo", action="store_true", help="Offline synthetic example; no credentials or network.")
    mode.add_argument("--upload", action="store_true", help="Enable a real download and YouTube upload.")
    mode.add_argument("--dry-run", action="store_true", help="Preview live discovery (the default); no upload.")
    parser.add_argument("--tiktok-url", default="", help="Full URL of one of your 20 most recent TikToks.")
    parser.add_argument("--privacy", choices=["private", "unlisted", "public"], default="private")
    parser.add_argument("--confirm-public", action="store_true", help="Required in addition to --upload for public uploads.")
    parser.add_argument("--show-metadata", action="store_true", help="Print caption/title/URL; keep such logs private.")
    args = parser.parse_args(argv)
    if args.upload and args.privacy == "public" and not args.confirm_public:
        parser.error("Public uploads require --confirm-public.")
    if args.demo and args.tiktok_url:
        parser.error("--demo cannot use a live TikTok URL.")

    if args.demo:
        post = discovery.TikTokPost(
            id="123", url="https://www.tiktok.com/@demo_creator/video/123",
            caption="when the tests pass on the first try #coding #python",
            created_at=0, is_photo_post=False,
        )
        print("[demo] Synthetic example; no network or credentials used.")
    else:
        load_env()
        post = discovery.find_by_url(args.tiktok_url) if args.tiktok_url else discovery.find_latest()
        print("[discovery] Found a candidate on the authorized account.")

    if post.is_photo_post:
        print("[reposter] Skipping photo carousel: only videos are supported.")
        return

    adapted = adapter.adapt_for_youtube(post.caption)
    if args.show_metadata or args.demo:
        print(f"[preview] Source: {post.url}")
        print(f"[preview] Title: {adapted.title}")
        print(f"[preview] Description: {adapted.description}")

    if not args.upload:
        print("[preview] No duplicate check, download, or upload. Use --upload to opt in.")
        return

    if youtube_upload.was_reposted(post.url):
        print("[reposter] Already present in recent uploads; skipped.")
        return

    with tempfile.TemporaryDirectory() as tmp:
        video_path = download.download_tiktok(post.url, Path(tmp))
        youtube_upload.upload(
            video_path, title=adapted.title,
            description=f"{adapted.description}\n\nSource: {post.url}",
            tags=adapted.tags, privacy=args.privacy,
        )
    print(f"[upload] Complete ({args.privacy}). Check your YouTube Studio.")


def cli() -> int:
    try:
        main()
    except Exception:
        # Provider exceptions may contain signed URLs, tokens, or account data.
        print("[error] Reposter failed. Check local configuration, permissions, and service availability. "
              "Provider details are intentionally withheld from logs.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
