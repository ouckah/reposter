"""Authorize locally; save the refresh token privately without printing or pushing it."""

from __future__ import annotations

import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from pipelines.reposter.youtube_upload import SCOPES
from shared.env import load_env, require


def save_token(token: str, destination: Path) -> None:
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Exclusive creation avoids overwriting an existing token or following a symlink.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(token)


def main() -> None:
    destination = Path(".secrets/youtube-refresh-token.txt")
    if destination.exists():
        raise RuntimeError("A saved token already exists; manage it privately before reauthorizing.")
    load_env()
    flow = InstalledAppFlow.from_client_config({"installed": {
        "client_id": require("YOUTUBE_OAUTH_CLIENT_ID"),
        "client_secret": require("YOUTUBE_OAUTH_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost"],
    }}, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", authorization_prompt_message="",
                                  success_message="Authorization complete. You may close this window.")
    if not creds.refresh_token:
        raise RuntimeError("No refresh token returned.")
    save_token(creds.refresh_token, destination)
    print("Saved token to .secrets/youtube-refresh-token.txt. "
          "Privately copy its value to YOUTUBE_REFRESH_TOKEN in your local .env. "
          "No GitHub secrets were changed.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Authorization failed. Check your local settings and existing token file. "
                         "Provider details are withheld to protect credentials.") from None
