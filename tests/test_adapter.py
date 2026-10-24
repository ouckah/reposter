from pipelines.reposter.adapter import adapt_for_youtube


def test_adapts_caption_without_an_llm() -> None:
    result = adapt_for_youtube("when the code works first try #compsci #Python")

    assert result.title == "when the code works first try #shorts #compsci #Python"
    assert result.description == "when the code works first try #compsci #Python"
    assert result.tags == ["shorts", "compsci", "python"]


def test_shorts_is_first_and_the_fifth_tiktok_hashtag_is_removed() -> None:
    result = adapt_for_youtube("a developer walks into standup #cs #swe #coding #career #college")

    assert result.title == "a developer walks into standup #shorts #cs #swe #coding #career"
    assert result.tags == ["shorts", "cs", "swe", "coding", "career"]
    assert "#college" not in result.title


def test_empty_caption_has_safe_defaults() -> None:
    result = adapt_for_youtube("   ")

    assert result.title == "Computer science moment #shorts"
    assert result.description == "Computer science moment"
    assert result.tags == ["shorts"]
