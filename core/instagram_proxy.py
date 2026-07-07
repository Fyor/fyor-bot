"""Workaround for Instagram stories/highlights: no direct public API exists.

Instagram's own servers only return story/highlight media (the
`reels_media` endpoint, under the hood) to requests carrying an
authenticated session cookie -- this is true even for fully public
accounts, and it's why tools like instaloader also require a login for
this specific content type. There is no unauthenticated first-party path.

The workaround: a handful of ad-supported "Instagram story viewer" websites
do this same authenticated fetch server-side, using their own pool of
logged-in accounts, and expose the resulting media as plain CDN links on a
public page. We proxy through one of those instead -- the bot itself still
never authenticates as anyone's account, which is the point, but by
construction this is the least stable part of the project:

  * These are unofficial, undocumented, ad-monetized sites. They rename
    routes, add captchas, rate-limit, or disappear outright with no notice.
  * Multiple providers are tried in order (PROVIDERS below) so one going
    down doesn't take the feature out entirely.
  * Extraction doesn't parse a specific JSON schema per provider; it scans
    whatever the provider returns (HTML or JSON) for literal Instagram CDN
    URLs (`cdninstagram.com` / `fbcdn.net`) via regex. That's deliberately
    the most change-resistant thing to key off -- the page markup around it
    will drift constantly, the underlying CDN URL shape does not.

Maintenance: run `python -m core.instagram_proxy story <username>` (or
`highlight <id>`) to see which providers currently work, without spinning
up the whole bot. See README's "Instagram story/highlight workaround"
section.
"""

from __future__ import annotations

import logging
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import aiohttp

from core.extractor import DownloadFailure, DownloadResult, ExtractError, DOWNLOAD_ROOT

logger = logging.getLogger("mediabot.instagram_proxy")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
}
_TIMEOUT = aiohttp.ClientTimeout(total=20)

_CDN_URL_RE = re.compile(
    r'https?://[a-zA-Z0-9.\-]*(?:cdninstagram\.com|fbcdn\.net)[^\s"\'<>\\]+',
    re.I,
)
_EXT_RE = re.compile(r"\.(mp4|jpg|jpeg|webp|png)(?:\?|$)", re.I)


@dataclass(frozen=True)
class Provider:
    name: str
    # {username} / {id} get substituted in. Multiple candidates per kind
    # because these sites don't publish a stable route contract -- if the
    # first shape 404s or comes back empty we just try the next.
    story_url_templates: tuple[str, ...]
    highlight_url_templates: tuple[str, ...]


PROVIDERS: tuple[Provider, ...] = (
    Provider(
        name="storiesig",
        story_url_templates=(
            "https://storiesig.info/en/stories/{username}",
            "https://storiesig.info/stories/{username}",
        ),
        highlight_url_templates=(
            "https://storiesig.info/en/highlights/{id}",
        ),
    ),
    Provider(
        name="imginn",
        story_url_templates=(
            "https://imginn.com/stories/{username}/",
            "https://imginn.com/{username}/",
        ),
        highlight_url_templates=(
            "https://imginn.com/highlights/{id}/",
        ),
    ),
    Provider(
        name="anonyig",
        story_url_templates=(
            "https://anonyig.com/en/stories/{username}/",
            "https://anonyig.com/en/{username}/",
        ),
        highlight_url_templates=(),
    ),
)


def _extract_media_urls(text: str) -> list[tuple[str, str]]:
    """Return deduped (url, ext) pairs found in `text`."""
    seen: dict[str, str] = {}
    for match in _CDN_URL_RE.finditer(text):
        url = match.group(0).rstrip(").,")
        ext_match = _EXT_RE.search(url)
        ext = ext_match.group(1).lower() if ext_match else "jpg"
        if ext == "jpeg":
            ext = "jpg"
        seen[url] = ext
    return list(seen.items())


async def _try_provider(
    session: aiohttp.ClientSession, provider: Provider, kind: str, identifier: str
) -> list[tuple[str, str]]:
    templates = provider.story_url_templates if kind == "story" else provider.highlight_url_templates
    for template in templates:
        page_url = template.format(username=identifier, id=identifier)
        try:
            async with session.get(page_url, headers=_HEADERS, timeout=_TIMEOUT, allow_redirects=True) as resp:
                if resp.status != 200:
                    continue
                text = await resp.text(errors="ignore")
        except (aiohttp.ClientError, TimeoutError) as exc:
            logger.info("provider %s template %s failed: %s", provider.name, page_url, exc)
            continue

        media = _extract_media_urls(text)
        if media:
            logger.info("provider %s found %d media URL(s) for %s", provider.name, len(media), identifier)
            return media
    return []


async def find_media_urls(kind: str, identifier: str) -> list[tuple[str, str]]:
    """Try every provider in order; return the first non-empty result."""
    async with aiohttp.ClientSession() as session:
        for provider in PROVIDERS:
            media = await _try_provider(session, provider, kind, identifier)
            if media:
                return media
    return []


async def _download_media(urls: list[tuple[str, str]], job_dir: Path) -> list[Path]:
    files: list[Path] = []
    async with aiohttp.ClientSession() as session:
        for i, (url, ext) in enumerate(urls):
            try:
                async with session.get(url, headers=_HEADERS, timeout=_TIMEOUT) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.read()
            except (aiohttp.ClientError, TimeoutError) as exc:
                logger.warning("failed to fetch media url %s: %s", url, exc)
                continue
            path = job_dir / f"{i:02d}.{ext}"
            path.write_bytes(data)
            files.append(path)
    return files


async def download(kind: str, identifier: str, *, label: str) -> DownloadResult:
    """kind is 'story' or 'highlight'; identifier is a username or highlight id."""
    media = await find_media_urls(kind, identifier)
    if not media:
        raise DownloadFailure(
            ExtractError.LOGIN_REQUIRED,
            f"No proxy provider could retrieve this {kind} for '{identifier}'. Instagram "
            f"{kind}s normally require a logged-in session, and every fallback proxy "
            "provider either had nothing for this link or is currently down/blocked.",
        )

    job_dir = DOWNLOAD_ROOT / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)
    files = await _download_media(media, job_dir)
    if not files:
        try:
            job_dir.rmdir()
        except OSError:
            pass
        raise DownloadFailure(
            ExtractError.UNKNOWN,
            f"A proxy provider listed media for this {kind} but none of the files downloaded.",
        )

    return DownloadResult(files=files, title=f"Instagram {label}", uploader=identifier, job_dir=job_dir)


if __name__ == "__main__":
    import asyncio

    if len(sys.argv) != 3 or sys.argv[1] not in ("story", "highlight"):
        print("usage: python -m core.instagram_proxy <story|highlight> <username-or-id>")
        raise SystemExit(1)

    async def _main():
        found = await find_media_urls(sys.argv[1], sys.argv[2])
        if not found:
            print("No provider returned any media URLs.")
        for url, ext in found:
            print(f"[{ext}] {url}")

    asyncio.run(_main())
