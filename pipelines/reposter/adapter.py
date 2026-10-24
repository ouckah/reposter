"""Deterministically format a TikTok caption for YouTube Shorts."""

from __future__ import annotations

import re
from dataclasses import dataclass

HASHTAG_RE = re.compile(r"#([A-Za-z0-9_]+)")
MAX_CONTEXTUAL_HASHTAGS = 4
YOUTUBE_TITLE_LIMIT = 100


@dataclass(frozen=True)
class AdaptedPost:
    title: str
    description: str
    tags: list[str]


def adapt_for_youtube(caption: str) -> AdaptedPost:
    clean = " ".join(caption.split()).strip()
    title_text = HASHTAG_RE.sub("", clean)
    title_text = " ".join(title_text.split()).strip(" -–—|")
    title_text = title_text or "Computer science moment"

    contextual: list[str] = []
    seen = {"shorts"}
    for match in HASHTAG_RE.findall(clean):
        normalized = match.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        contextual.append(match)
        if len(contextual) == MAX_CONTEXTUAL_HASHTAGS:
            break

    visible_hashtags = ["#shorts", *(f"#{tag}" for tag in contextual)]
    suffix = " ".join(visible_hashtags)
    available_title_length = YOUTUBE_TITLE_LIMIT - len(suffix) - 1
    while contextual and available_title_length < 1:
        contextual.pop()
        visible_hashtags.pop()
        suffix = " ".join(visible_hashtags)
        available_title_length = YOUTUBE_TITLE_LIMIT - len(suffix) - 1

    visible_title = title_text[:available_title_length].rstrip()
    title = f"{visible_title} {suffix}"
    tags = ["shorts", *(tag.lower() for tag in contextual)]
    description = clean or title_text
    return AdaptedPost(title=title, description=description, tags=tags)
