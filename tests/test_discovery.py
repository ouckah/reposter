from pipelines.reposter.discovery import _canonical_url, _from_api


def test_canonical_url_removes_tracking_and_trailing_slash() -> None:
    assert (
        _canonical_url("https://www.tiktok.com/@demo_creator/video/123/?utm_source=test")
        == "https://www.tiktok.com/@demo_creator/video/123"
    )


def test_api_video_becomes_post() -> None:
    post = _from_api(
        {
            "id": "123",
            "share_url": "https://www.tiktok.com/@demo_creator/video/123?lang=en",
            "video_description": "hello #cs",
            "create_time": 42,
            "duration": 15,
        }
    )

    assert post.id == "123"
    assert post.url == "https://www.tiktok.com/@demo_creator/video/123"
    assert post.caption == "hello #cs"
    assert post.created_at == 42
    assert post.is_photo_post is False


def test_api_photo_carousel_is_identified_by_zero_duration() -> None:
    post = _from_api(
        {
            "id": "456",
            "share_url": "https://www.tiktok.com/@demo_creator/video/456",
            "video_description": "swipe through",
            "create_time": 43,
            "duration": 0,
        }
    )

    assert post.is_photo_post is True


def test_missing_duration_is_not_assumed_to_be_a_photo_carousel() -> None:
    post = _from_api(
        {
            "id": "789",
            "share_url": "https://www.tiktok.com/@demo_creator/video/789",
            "create_time": 44,
        }
    )

    assert post.is_photo_post is False
