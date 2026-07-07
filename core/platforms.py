"""URL recognition for supported platforms.

This module is pure pattern-matching logic with no network calls, so it can
be exercised in full by the test suite regardless of sandboxing. It exists
separately from the extractor so the bot can:

  * reject unsupported links before spending a network round trip
  * pick a human-readable label ("Instagram Reel", "TikTok Slideshow", ...)
    for status messages
  * flag content types that normally require a logged-in session
    (Instagram stories/highlights) so the bot can route them to the
    third-party proxy workaround (see core/instagram_proxy.py) instead of
    yt-dlp, which can't fetch them directly
  * pull the username/highlight-id straight out of the URL for that proxy
    path, instead of re-parsing it later
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
    UNKNOWN = "post"


@dataclass(frozen=True)
class MatchResult:
    platform: Platform
    content_type: ContentType
    # True if this content type is only reliably reachable with an
    # authenticated session cookie on the platform itself. The bot never
    # authenticates as a real account -- for Instagram stories/highlights it
    # instead routes through a third-party proxy workaround.
    requires_login_usually: bool = False
    # Username (story) or highlight id (highlight), pulled straight out of
    # the URL for use by core/instagram_proxy.py. None for everything else.
    identifier: str | None = None

    @property
    def label(self) -> str:
        return f"{self.platform.value} {self.content_type.value}"


# Instagram stories/highlights get their own regexes (rather than living in
# the generic table below) because we need to capture the username/id, not
# just classify the URL.
_IG_HIGHLIGHT_RE = re.compile(r"instagram\.com/stories/highlights/(?P<id>\d+)", re.I)
_IG_STORY_RE = re.compile(r"instagram\.com/stories/(?P<username>[\w.\-]+)/(?P<id>\d+)", re.I)

# Order matters: more specific patterns are listed before generic fallbacks.
_PATTERNS: list[tuple[re.Pattern, Platform, ContentType]] = [
    # --- YouTube ---------------------------------------------------------
    (re.compile(r"(?:youtube\.com|youtu\.be)/shorts/[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.SHORT_FORM),
    # /live/<id> is just how YouTube links a stream's VOD once it has ended;
    # if it's still actually live, yt-dlp will fail on its own and the bot
    # surfaces that as a normal extraction error.
    (re.compile(r"youtube\.com/live/[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.VIDEO),
    (re.compile(r"(?:m\.|www\.|music\.)?youtube\.com/watch\?.*\bv=[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.VIDEO),
    (re.compile(r"youtu\.be/[\w-]+", re.I),
     Platform.YOUTUBE, ContentType.VIDEO),

    # --- TikTok ------------------------------------------------------------
    (re.compile(r"tiktok\.com/@[\w.\-]+/photo/\d+", re.I),
     Platform.TIKTOK, ContentType.PHOTO_POST),
    (re.compile(r"tiktok\.com/@[\w.\-]+/video/\d+", re.I),
     Platform.TIKTOK, ContentType.SHORT_FORM),
    # Short-link redirectors (vm.tiktok.com/XXXX, vt.tiktok.com/XXXX,
    # tiktok.com/t/XXXX) resolve to one of the above after a redirect that
    # yt-dlp follows itself; classify generically here.
    (re.compile(r"(?:vm|vt)\.tiktok\.com/[\w-]+", re.I),
     Platform.TIKTOK, ContentType.UNKNOWN),
    (re.compile(r"tiktok\.com/t/[\w-]+", re.I),
     Platform.TIKTOK, ContentType.UNKNOWN),

    # --- Instagram (posts/reels/tv -- stories/highlights handled above) ----
    (re.compile(r"instagram\.com/reels?/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.SHORT_FORM),
    (re.compile(r"instagram\.com/tv/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.SHORT_FORM),
    (re.compile(r"instagram\.com/p/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.PHOTO_POST),
    (re.compile(r"instagram\.com/share/[\w-]+", re.I),
     Platform.INSTAGRAM, ContentType.UNKNOWN),

    # --- X / Twitter -------------------------------------------------------
    (re.compile(r"(?:x\.com|twitter\.com|mobile\.twitter\.com)/[\w]+/status/\d+", re.I),
     Platform.TWITTER, ContentType.VIDEO),
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

    m = _IG_HIGHLIGHT_RE.search(url)
    if m:
        return MatchResult(Platform.INSTAGRAM, ContentType.HIGHLIGHT, True, identifier=m.group("id"))
    m = _IG_STORY_RE.search(url)
    if m:
        return MatchResult(Platform.INSTAGRAM, ContentType.STORY, True, identifier=m.group("username"))

    for pattern, platform, content_type in _PATTERNS:
        if pattern.search(url):
            return MatchResult(platform, content_type)
    for pattern, platform in _DOMAIN_FALLBACKS:
        if pattern.search(url):
            return MatchResult(platform, ContentType.UNKNOWN)
    return None


URL_RE = re.compile(r"https?://\S+")


def first_url(text: str) -> str | None:
    """Pull the first http(s) URL out of a free-form command argument."""
    match = URL_RE.search(text)
    return match.group(0) if match else None
