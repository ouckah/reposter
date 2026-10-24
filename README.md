# reposter by ouckah

A small TikTok → YouTube Shorts pipeline. No LLM, database, or dashboard:
find a video, format its caption, check for a recent duplicate, and upload it.

This is a standalone public edition. It contains no production
credentials, account data, private Git history, or scheduled publishing workflow.

## Try it without accounts

Python 3.11+ is required. From this directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pipelines.reposter.main --demo
```

The demo formats a synthetic caption entirely offline. It does not read `.env`,
contact TikTok/YouTube, download a video, or upload anything.

If you use uv, `uv sync --locked --extra dev` installs the checked-in lockfile.
Python 3.12 or newer is recommended for a new environment.

## Connect your own accounts

Only repost videos you own or have permission to redistribute, including their
music. A TikTok music license does not automatically grant YouTube rights.
Follow each platform's terms and API requirements.

1. Copy `.env.example` to `.env` and keep it private.
2. Register your own TikTok app and obtain authorization for `video.list` using
   the [official Display API setup](https://developers.tiktok.com/docs/en/display-api-get-started).
   Set your client key, client secret, and refresh token. Configure a redirect
   endpoint you control; do not send authorization codes to a shared callback service.
   This project does not host a TikTok OAuth callback or provide a TikTok app.
3. Enable the YouTube Data API in your own Google Cloud project and create a
   Desktop OAuth client. Configure its consent screen and permitted test users
   as required by Google. Set `YOUTUBE_OAUTH_CLIENT_ID` and
   `YOUTUBE_OAUTH_CLIENT_SECRET` in `.env`.
4. Run `python -m scripts.youtube_auth` locally. Sign into the intended channel.
   The helper stores the refresh token in `.secrets/youtube-refresh-token.txt`
   with owner-only file permissions on POSIX systems. Privately copy that value
   into `YOUTUBE_REFRESH_TOKEN` in `.env`. It never prints tokens or pushes GitHub
   secrets. An existing token file is not overwritten.

The YouTube scopes are `youtube.readonly` (duplicate checks) and `youtube.upload`.
Check Google's current [upload guide](https://developers.google.com/youtube/data/guides/uploading_a_video)
for project authorization, quota, and upload requirements. No platform approval is bundled.

## Preview, then opt in

```bash
# Live discovery, but no downloads or uploads. Metadata stays out of logs.
python -m pipelines.reposter.main

# Optional local preview; its output contains your caption and source URL.
python -m pipelines.reposter.main --dry-run --show-metadata

# First real upload: private by default. Verify it in YouTube Studio.
python -m pipelines.reposter.main --upload

# Publishing publicly requires both explicit switches.
python -m pipelines.reposter.main --upload --privacy public --confirm-public
```

Use `--tiktok-url` with a full URL to select one of the authorized account's
20 most recent videos. Photo carousels are skipped. There is no force-duplicate
flag. Change the visibility of an existing test upload in Studio rather than
uploading it again.

## How it works and where it stops

- Discovery uses TikTok's official API and the account you authorize.
- The caption formatter adds `#shorts` and up to four contextual hashtags.
- Duplicate detection searches the **50 most recent YouTube uploads** for a
  source marker. It is not a complete archive or an atomic lock: run only one
  uploader at a time, and avoid using this tool to backfill older videos.
- Downloads try TikTok's public player endpoint, then `yt-dlp`. The player
  endpoint is not a stable supported download API; either path may stop working.
  No browser cookies are included or extracted.
- It uploads the source video unchanged. It does not crop, transcode, remove
  watermarks, or guarantee that YouTube classifies the result as a Short.
- Tokens expire or may be rotated by providers. This minimal edition does not
  persist rotated TikTok refresh tokens; manage reauthorization privately.
- Errors deliberately omit raw provider responses and signed URLs. For diagnosis,
  inspect privately, never paste credentials or unredacted logs into an issue.

## Development and publication

```bash
python -m pytest -q
python -m ruff check .
python scripts/check_public.py
```

Tests block real network connections. Public CI only runs tests, the synthetic
demo, lint, and the release-content guard; it has no production secrets or cron.
Keep production execution in a separate private repository. Do not wire
unreviewed public contributions to production credentials.

See [SECURITY.md](SECURITY.md) and [PUBLISHING.md](PUBLISHING.md) before publishing changes.
Released under the [MIT License](LICENSE). Contact: ouckah@gmail.com.
