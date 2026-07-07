"""Centralized environment configuration. Nothing here is a personal
account credential -- DISCORD_BOT_TOKEN is the bot application's own token
(required for any Discord bot to connect at all), not a user login."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")

# Discord's per-attachment cap depends on the server's boost level. Default
# assumes no boost. Bump this in .env if your private server is boosted.
UPLOAD_LIMIT_BYTES: int = _int_env("DISCORD_UPLOAD_LIMIT_MB", 25) * 1024 * 1024

MAX_CONCURRENT_DOWNLOADS: int = _int_env("MAX_CONCURRENT_DOWNLOADS", 3)
COOLDOWN_SECONDS: int = _int_env("COOLDOWN_SECONDS", 15)
MAX_FILES_PER_REQUEST: int = _int_env("MAX_FILES_PER_REQUEST", 10)  # Discord caps 10 attachments/message

# Hard safety ceiling on the *source* file yt-dlp is allowed to fetch, well
# above the Discord upload limit, so a mistaken link to a multi-hour stream
# can't fill the disk before the compression step ever runs.
MAX_SOURCE_MB: int = _int_env("MAX_SOURCE_MB", 500)
