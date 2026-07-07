"""URL recognition for supported platforms.

This module is pure pattern-matching logic with no network calls, so it can
be exercised in full by the test suite regardless of sandboxing. It exists
separately from the extractor so the bot can:

  * reject unsupported links before spending a network round trip
  * pick a human-readable label ("Instagram Reel", "TikTok Slideshow", ...)
    for status messages
  * flag content types that are known to require a logged-in session
    (Instagram/Facebook stories & highlights) so the bot can warn the user
    up front instead of failing confusingly after a delay.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Platform(str, Enum):
    YOUTUBE = "YouTube"
    TIKTOK = "TikTok"
    INSTAGRAM = "Instagram"
    TWITTER = "X / Twitter"


class ContentType(str, Enum):
    VIDEO = "video"
    SHORT_FORM = "short-form video"  # Shorts / Reels / TikTok videos
    PHOTO_POST = "photo post"  # TikTok photo mode, IG carousel of images
    STORY = "story"
    HIGHLIGHT = "highlight"
    LIVE = "live stream"
    UNKNOWN = "post"


@dataclass(frozen=True)
class MatchResult:
    platform: Platform
    content_type: ContentType
    # True if this content type is only reliably reachable with an
    # authenticated session cookie, which this bot deliberately does not use.
    requires_login_usually: bool = False

    @property
    def label(self) -> str:
        return f"{self.platform.value} {self.content_type.value}"


# Order matters: more specific patterns are listed before generic fallbacks.
_PATTERNS: list[tuple[re.Pattern, Platform, ContentType, bool]] = [
    # --- YouTube -----------------------------------------------------
    (re.compile(r"(?:youtube\.com|youtu\.be)/shorts/[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.SHORT_FORM, False),
    (re.compile(r"youtube\.com/live/[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.LIVE, False),
    (re.compile(r"(?:m\.|www\.|music\.)?youtube\.com/watch\?.*\bv=[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.VIDEO, False),
    (re.compile(r"youtu\.be/[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.VIDEO, False),

    # --- TikTok --------------------------------------------------------
    (re.compile(r"tiktok\.com/@[\w.\-]+/photo/\d+", re.I),
     Platform.TIKTOK, ContentType.PHOTO_POST, False),
    (re.compile(r"tiktok\.com/@[\w.\-]+/video/\d+", re.I),
     Platform.TIKTOK, ContentType.SHORT_FORM, False),
    # Short-link redirectors (vm.tiktok.com/XXXX, vt.tiktok.com/XXXX,
    # tiktok.com/t/XXXX) resolve to one of the above after a redirect that
    # yt-dlp follows itself; classify generically here.
    (re.compile(r"(?:vm|vt)\.tiktok\.com/[\w-]+", re.I),
     Platform.TIKTOK, ContentType.UNKNOWN, False),
    (re.compile(r"tiktok\.com/t/[\w-]+", re.I),
     Platform.TIKTOK, ContentType.UNKNOWN, False),

    # --- Instagram -------------------------------------------------------
    (re.compile(r"instagram\.com/stories/highlights/\d+", re.I),
     Platform.INSTAGRAM, ContentType.HIGHLIGHT, True),
    (re.compile(r"instagram\.com/stories/[\w.\-]+/\d+", re.I),
     Platform.INSTAGRAM, ContentType.STORY, True),
    (re.compile(r"instagram\.com/reels?/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.SHORT_FORM, False),
    (re.compile(r"instagram\.com/tv/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.SHORT_FORM, False),
    (re.compile(r"instagram\.com/p/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.PHOTO_POST, False),
    (re.compile(r"instagram\.com/share/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.UNKNOWN, False),

    # --- X / Twitter -------------------------------------------------
    (re.compile(r"(?:x\.com|twitter\.com|mobile\.twitter\.com)/[\w]+/status/\d+", re.I),
     Platform.TWITTER, ContentType.VIDEO, False),
    (re.compile(r"(?:x\.com|twitter\.com)/i/spaces/[\w]+", re.I),
     Platform.TWITTER, ContentType.LIVE, True),
]

# Domains we recognize even if the specific path pattern above didn't match
# (e.g. a shape of URL the platform introduced after this file was written).
_DOMAIN_FALLBACKS: list[tuple[re.Pattern, Platform]] = [
    (re.compile(r"(?:youtube\.com|youtu\.be)", re.I), Platform.YOUTUBE),
    (re.compile(r"tiktok\.com", re.I), Platform.TIKTOK),
    (re.compile(r"instagram\.com", re.I), Platform.INSTAGRAM),
    (re.compile(r"(?:x\.com|twitter\.com)", re.I), Platform.TWITTER),
]


def identify(url: str) -> MatchResult | None:
    """Classify a URL. Returns None if it doesn't belong to a supported site."""
    url = url.strip()
    for pattern, platform, content_type, needs_login in _PATTERNS:
        if pattern.search(url):
            return MatchResult(platform, content_type, needs_login)
    for pattern, platform in _DOMAIN_FALLBACKS:
        if pattern.search(url):
            return MatchResult(platform, ContentType.UNKNOWN, False)
    return None


URL_RE = re.compile(r"https?://\S+")


def first_url(text: str) -> str | None:
    """Pull the first http(s) URL out of a free-form command argument."""
    match = URL_RE.search(text)
    return match.group(0) if match else None
