"""Pure URL-classification tests -- no network access needed or used.

(The sandbox this project was originally scaffolded in blocks outbound
requests to social platforms entirely, so anything that touches the network
has to be verified by hand after deployment -- see README's "Testing"
section. These tests cover the part that doesn't need the network: routing
a URL to the right platform/content-type before we ever call yt-dlp.)
"""

from core.platforms import ContentType, Platform, first_url, identify


def test_youtube_watch_url():
    m = identify("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert m.platform is Platform.YOUTUBE
    assert m.content_type is ContentType.VIDEO


def test_youtube_short_link():
    m = identify("https://youtu.be/dQw4w9WgXcQ")
    assert m.platform is Platform.YOUTUBE
    assert m.content_type is ContentType.VIDEO


def test_youtube_shorts():
    m = identify("https://www.youtube.com/shorts/abc123XYZ_-")
    assert m.platform is Platform.YOUTUBE
    assert m.content_type is ContentType.SHORT_FORM


def test_youtube_live_link_treated_as_normal_video():
    # /live/<id> is how YouTube links a stream's VOD once it has ended; if
    # it's still actually live, yt-dlp fails on its own and that's surfaced
    # as a normal extraction error rather than a special-cased content type.
    m = identify("https://www.youtube.com/live/abc123XYZ_-")
    assert m.content_type is ContentType.VIDEO


def test_tiktok_video():
    m = identify("https://www.tiktok.com/@someuser/video/7123456789012345678")
    assert m.platform is Platform.TIKTOK
    assert m.content_type is ContentType.SHORT_FORM


def test_tiktok_photo_post():
    m = identify("https://www.tiktok.com/@someuser/photo/7123456789012345678")
    assert m.platform is Platform.TIKTOK
    assert m.content_type is ContentType.PHOTO_POST


def test_tiktok_short_link():
    m = identify("https://vm.tiktok.com/ZMabcdefg/")
    assert m.platform is Platform.TIKTOK


def test_instagram_post():
    m = identify("https://www.instagram.com/p/Cabc123XYZ/")
    assert m.platform is Platform.INSTAGRAM
    assert m.content_type is ContentType.PHOTO_POST
    assert m.requires_login_usually is False


def test_instagram_reel():
    m = identify("https://www.instagram.com/reel/Cabc123XYZ/")
    assert m.content_type is ContentType.SHORT_FORM
    assert m.requires_login_usually is False


def test_instagram_story_flags_login_required_and_captures_username():
    m = identify("https://www.instagram.com/stories/someuser/3123456789012345678/")
    assert m.content_type is ContentType.STORY
    assert m.requires_login_usually is True
    assert m.identifier == "someuser"


def test_instagram_highlight_flags_login_required_and_captures_id():
    m = identify("https://www.instagram.com/stories/highlights/17123456789012345/")
    assert m.content_type is ContentType.HIGHLIGHT
    assert m.requires_login_usually is True
    assert m.identifier == "17123456789012345"


def test_twitter_status_x_domain():
    m = identify("https://x.com/someuser/status/1712345678901234567")
    assert m.platform is Platform.TWITTER
    assert m.content_type is ContentType.VIDEO


def test_twitter_status_legacy_domain():
    m = identify("https://twitter.com/someuser/status/1712345678901234567")
    assert m.platform is Platform.TWITTER


def test_unsupported_domain_returns_none():
    assert identify("https://example.com/video/123") is None


def test_first_url_extracts_from_surrounding_text():
    assert first_url("check this out https://x.com/a/status/123 nice") == "https://x.com/a/status/123"


def test_first_url_returns_none_without_url():
    assert first_url("no link here") is None
