"""Tests for the generic CDN-URL scraping logic -- no network involved.

The provider fetch/download functions do hit the network and can't be
exercised here (see README's "Instagram story/highlight workaround"
section for how to verify those live). This covers the part that's pure
logic: pulling real Instagram CDN media URLs out of arbitrary provider
HTML/JSON without depending on any provider's exact markup.
"""

from core.instagram_proxy import _extract_media_urls


def test_extracts_video_url_from_html():
    html = '<a href="https://scontent-lax3-1.cdninstagram.com/v/abc_n.mp4?_nc_ht=x">dl</a>'
    result = _extract_media_urls(html)
    assert result == [("https://scontent-lax3-1.cdninstagram.com/v/abc_n.mp4?_nc_ht=x", "mp4")]


def test_extracts_image_url_and_normalizes_jpeg_extension():
    html = 'data-url="https://scontent.fbcdn.net/v/t51/abc_n.jpeg?x=1"'
    result = _extract_media_urls(html)
    assert result == [("https://scontent.fbcdn.net/v/t51/abc_n.jpeg?x=1", "jpg")]


def test_dedupes_repeated_urls():
    url = "https://scontent.cdninstagram.com/v/abc_n.mp4"
    html = f'<a href="{url}">1</a><a href="{url}">2</a>'
    assert _extract_media_urls(html) == [(url, "mp4")]


def test_ignores_non_instagram_cdn_urls():
    html = '<a href="https://example.com/video.mp4">not instagram</a>'
    assert _extract_media_urls(html) == []


def test_extracts_multiple_distinct_urls_in_order():
    html = (
        '<a href="https://scontent.cdninstagram.com/v/a_n.jpg">1</a>'
        '<a href="https://scontent.cdninstagram.com/v/b_n.mp4">2</a>'
    )
    result = _extract_media_urls(html)
    assert result == [
        ("https://scontent.cdninstagram.com/v/a_n.jpg", "jpg"),
        ("https://scontent.cdninstagram.com/v/b_n.mp4", "mp4"),
    ]
