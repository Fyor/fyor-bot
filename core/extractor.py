"""Thin async wrapper around yt-dlp.

Design notes (see README for the full write-up):

* yt-dlp does the actual scraping/extraction for every platform we support.
  Writing bespoke HTML scrapers per-platform is a losing game long-term
  (markup and API shapes change constantly); yt-dlp is updated for exactly
  that churn far faster than a bespoke scraper could be maintained here.
* Deliberately **no cookies, no login, no browser-profile import**. That
  means content that Instagram/X only serve to authenticated sessions
  (private accounts, stories/highlights in practice, some age-gated videos)
  will fail with LOGIN_REQUIRED below. That's a hard limitation of "public
  access only" scraping, not a bug.
* yt-dlp's network + parsing calls are all synchronous/blocking. Every call
  here runs inside `asyncio.to_thread` so it never blocks the bot's event
  loop (a Discord bot that blocks the loop stops answering heartbeats and
  gets disconnected by the gateway).
"""

from __future__ import annotations

import asyncio
import enum
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import yt_dlp

logger = logging.getLogger("mediabot.extractor")

DOWNLOAD_ROOT = Path(__file__).resolve().parent.parent / "downloads"


class ExtractError(enum.Enum):
    LOGIN_REQUIRED = "login_required"
    UNAVAILABLE = "unavailable"       # deleted, private, taken down
    GEO_BLOCKED = "geo_blocked"
    UNSUPPORTED = "unsupported"       # not a recognized/extractable URL
    TOO_LARGE = "too_large"           # exceeded configured max size pre-check
    RATE_LIMITED = "rate_limited"
    UNKNOWN = "unknown"


class DownloadFailure(Exception):
    def __init__(self, kind: ExtractError, detail: str):
        self.kind = kind
        self.detail = detail
        super().__init__(detail)


@dataclass
class DownloadResult:
    files: list[Path] = field(default_factory=list)
    title: str = ""
    uploader: str = ""
    webpage_url: str = ""
    job_dir: Path | None = None

    def cleanup(self) -> None:
        for f in self.files:
            f.unlink(missing_ok=True)
        if self.job_dir is not None:
            try:
                self.job_dir.rmdir()
            except OSError:
                pass  # not empty / already gone -- never crash on cleanup


_LOGIN_MARKERS = (
    "login required",
    "rate-limit reached",
    "only available for registered users",
    "private account",
    "restricted video",
    "requested content is not available",
    "this account is private",
)
_UNAVAILABLE_MARKERS = (
    "video unavailable",
    "video has been removed",
    "no longer available",
    "has been deleted",
    "content isn't available",
    "page not found",
)
_GEO_MARKERS = ("not available in your country", "geo restricted", "blocked it in your country")
_RATE_MARKERS = ("429", "too many requests")
_TOO_LARGE_MARKERS = ("max-filesize", "file is larger than")


def _classify(exc: Exception) -> DownloadFailure:
    msg = str(exc).lower()
    if any(m in msg for m in _LOGIN_MARKERS):
        return DownloadFailure(ExtractError.LOGIN_REQUIRED, str(exc))
    if any(m in msg for m in _UNAVAILABLE_MARKERS):
        return DownloadFailure(ExtractError.UNAVAILABLE, str(exc))
    if any(m in msg for m in _GEO_MARKERS):
        return DownloadFailure(ExtractError.GEO_BLOCKED, str(exc))
    if any(m in msg for m in _RATE_MARKERS):
        return DownloadFailure(ExtractError.RATE_LIMITED, str(exc))
    if any(m in msg for m in _TOO_LARGE_MARKERS):
        return DownloadFailure(ExtractError.TOO_LARGE, str(exc))
    if "unsupported url" in msg:
        return DownloadFailure(ExtractError.UNSUPPORTED, str(exc))
    return DownloadFailure(ExtractError.UNKNOWN, str(exc))


# Cap resolution to keep files closer to Discord's attachment limit before
# any compression pass is even needed. 1080p is plenty for a Discord embed.
_FORMAT = (
    "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
    "best[height<=1080][ext=mp4]/"
    "best[ext=mp4]/best"
)


def _build_opts(job_dir: Path, max_bytes: int | None) -> dict:
    opts = {
        "format": _FORMAT,
        "outtmpl": str(job_dir / "%(id)s.%(ext)s"),
        "restrictfilenames": True,
        "noplaylist": False,  # carousels/slideshows are represented as multi-entry results
        "playlistend": 20,     # sane cap so a mistaken playlist link can't fill the disk
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 3,
        "socket_timeout": 30,
        "merge_output_format": "mp4",
        "concurrent_fragment_downloads": 4,
        # Explicitly no cookies / no browser import -- public content only.
    }
    if max_bytes:
        opts["max_filesize"] = max_bytes
    return opts


async def download(url: str, *, max_bytes: int | None = None) -> DownloadResult:
    """Download the media at `url`. Runs yt-dlp in a worker thread."""
    job_dir = DOWNLOAD_ROOT / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)

    def _run() -> DownloadResult:
        opts = _build_opts(job_dir, max_bytes)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)

        entries = info.get("entries") if info.get("entries") is not None else [info]
        files: list[Path] = []
        for entry in entries:
            if not entry:
                continue
            for rd in entry.get("requested_downloads", []) or []:
                fp = rd.get("filepath")
                if fp:
                    files.append(Path(fp))
        return DownloadResult(
            files=files,
            title=info.get("title") or "",
            uploader=info.get("uploader") or info.get("channel") or "",
            webpage_url=info.get("webpage_url") or url,
            job_dir=job_dir,
        )

    start = time.monotonic()
    try:
        result = await asyncio.to_thread(_run)
    except yt_dlp.utils.DownloadError as exc:
        _rmdir_if_empty(job_dir)
        raise _classify(exc) from exc
    except Exception as exc:  # noqa: BLE001 -- surface anything unexpected as UNKNOWN
        _rmdir_if_empty(job_dir)
        raise DownloadFailure(ExtractError.UNKNOWN, str(exc)) from exc

    if not result.files:
        _rmdir_if_empty(job_dir)
        raise DownloadFailure(ExtractError.UNKNOWN, "yt-dlp reported success but produced no files")

    logger.info("downloaded %s file(s) from %s in %.1fs", len(result.files), url, time.monotonic() - start)
    return result


def _rmdir_if_empty(job_dir: Path) -> None:
    try:
        next(job_dir.iterdir())
    except StopIteration:
        job_dir.rmdir()
    except FileNotFoundError:
        pass
    except OSError:
        pass
