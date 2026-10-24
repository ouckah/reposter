from unittest.mock import patch

import pytest

from pipelines.reposter.discovery import TikTokPost
from pipelines.reposter.main import cli, main

POST = TikTokPost("123", "https://www.tiktok.com/@demo_creator/video/123",
                  "synthetic caption", 0, False)


@pytest.fixture
def services():
    with (
        patch("pipelines.reposter.main.load_env") as env,
        patch("pipelines.reposter.main.discovery.find_latest", return_value=POST) as latest,
        patch("pipelines.reposter.main.discovery.find_by_url", return_value=POST) as by_url,
        patch("pipelines.reposter.main.youtube_upload.was_reposted", return_value=False) as duplicate,
        patch("pipelines.reposter.main.download.download_tiktok") as download,
        patch("pipelines.reposter.main.youtube_upload.upload") as upload,
    ):
        yield env, latest, by_url, duplicate, download, upload


def test_demo_never_loads_credentials_or_calls_services(services, capsys):
    main(["--demo"])
    for service in services:
        service.assert_not_called()
    assert "#shorts" in capsys.readouterr().out


@pytest.mark.parametrize("args", [[], ["--dry-run"], ["--privacy", "public"], ["--confirm-public"]])
def test_preview_is_default(services, capsys, args):
    main(args)
    for service in services[3:]:
        service.assert_not_called()
    output = capsys.readouterr().out
    assert POST.caption not in output
    assert POST.url not in output


def test_public_upload_needs_confirmation_before_credentials(services):
    with pytest.raises(SystemExit) as exc:
        main(["--upload", "--privacy", "public"])
    assert exc.value.code == 2
    for service in services:
        service.assert_not_called()


@pytest.mark.parametrize("args", [["--demo", "--upload"], ["--dry-run", "--upload"],
                                  ["--demo", "--tiktok-url", POST.url]])
def test_conflicting_modes_rejected(services, args):
    with pytest.raises(SystemExit):
        main(args)
    for service in services:
        service.assert_not_called()


def test_upload_defaults_to_private(services):
    main(["--upload"])
    services[3].assert_called_once_with(POST.url)
    services[5].assert_called_once()
    assert services[5].call_args.kwargs["privacy"] == "private"


def test_explicit_public_upload(services):
    main(["--upload", "--privacy", "public", "--confirm-public"])
    assert services[5].call_args.kwargs["privacy"] == "public"


def test_duplicate_blocks_download_and_upload(services):
    services[3].return_value = True
    main(["--upload"])
    services[4].assert_not_called()
    services[5].assert_not_called()


def test_photo_blocks_download_and_upload(services):
    services[1].return_value = TikTokPost("123", POST.url, POST.caption, 0, True)
    main(["--upload"])
    for service in services[3:]:
        service.assert_not_called()


def test_override_is_verified_through_authorized_discovery(services):
    main(["--tiktok-url", POST.url])
    services[1].assert_not_called()
    services[2].assert_called_once_with(POST.url)


def test_provider_error_is_not_printed(capsys):
    with patch("pipelines.reposter.main.main", side_effect=RuntimeError("PRIVATE_PROVIDER_RESPONSE")):
        assert cli() == 1
    captured = capsys.readouterr()
    assert "PRIVATE_PROVIDER_RESPONSE" not in captured.out + captured.err
    assert "[error]" in captured.err
