from pathlib import Path
from unittest.mock import MagicMock, patch

from pipelines.reposter.download import _select_player_url, download_tiktok


def test_download_tiktok_uses_browser_impersonation(tmp_path: Path) -> None:
    downloaded = tmp_path / "video.mp4"
    downloaded.write_bytes(b"video")

    downloader = MagicMock()
    downloader.__enter__.return_value = downloader
    downloader.extract_info.return_value = {"ext": "mp4"}

    with (
        patch(
            "pipelines.reposter.download._download_from_player_api",
            side_effect=RuntimeError("player unavailable"),
        ),
        patch("pipelines.reposter.download.yt_dlp.YoutubeDL", return_value=downloader) as factory,
    ):
        result = download_tiktok("https://www.tiktok.com/@demo_creator/video/123", tmp_path)

    assert result == downloaded
    impersonate = factory.call_args.args[0]["impersonate"]
    assert impersonate.client == "chrome"
    downloader.extract_info.assert_called_once_with(
        "https://www.tiktok.com/@demo_creator/video/123", download=True
    )


def test_select_player_url_prefers_highest_h264_profile() -> None:
    item = {
        "video_info": {
            "profiles": [
                {
                    "codec_type": "h265",
                    "height": 1920,
                    "bitrate": 900,
                    "play_addr": {"url_list": ["https://cdn.test/h265.mp4"]},
                },
                {
                    "codec_type": "h264",
                    "height": 720,
                    "bitrate": 1200,
                    "play_addr": {"url_list": ["https://cdn.test/h264.mp4"]},
                },
            ]
        }
    }

    assert _select_player_url(item) == "https://cdn.test/h264.mp4"
