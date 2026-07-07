from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

import config
from core import instagram_proxy, media, platforms
from core.extractor import DownloadFailure, ExtractError, download

logger = logging.getLogger("mediabot.download")

_ERROR_MESSAGES = {
    ExtractError.LOGIN_REQUIRED: (
        "That content only serves media to a logged-in session (private "
        "account or age-gated video). This bot only reads publicly "
        "accessible content, so it can't fetch this one."
    ),
    ExtractError.UNAVAILABLE: "That post looks like it's been deleted or made private.",
    ExtractError.GEO_BLOCKED: "That content is geo-restricted and isn't reachable from this bot's server region.",
    ExtractError.UNSUPPORTED: "I couldn't find any downloadable media at that link.",
    ExtractError.TOO_LARGE: "That source file is larger than this bot's safety ceiling -- too big to download.",
    ExtractError.RATE_LIMITED: "The platform is rate-limiting requests right now. Try again in a bit.",
    ExtractError.UNKNOWN: "Something went wrong pulling that link. It may be a new URL format this bot doesn't know yet.",
}


class DownloadCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_DOWNLOADS)

    @app_commands.command(name="download", description="Download public media (video/image) from a supported link")
    @app_commands.describe(url="A YouTube, TikTok, Instagram, or X/Twitter link")
    @app_commands.checks.cooldown(1, config.COOLDOWN_SECONDS, key=lambda i: i.user.id)
    async def download_cmd(self, interaction: discord.Interaction, url: str):
        clean_url = platforms.first_url(url) or url
        match = platforms.identify(clean_url)

        if match is None:
            await interaction.response.send_message(
                "That doesn't look like a YouTube, TikTok, Instagram, or X/Twitter link.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(thinking=True)

        is_story_workaround = match.content_type in (platforms.ContentType.STORY, platforms.ContentType.HIGHLIGHT)
        if is_story_workaround:
            await interaction.followup.send(
                f"{match.label.capitalize()} links aren't reachable through normal public "
                "access -- trying a fallback proxy service instead. This is best-effort and "
                "can fail if every proxy provider is currently down."
            )

        async with self._semaphore:
            try:
                if is_story_workaround:
                    kind = "story" if match.content_type is platforms.ContentType.STORY else "highlight"
                    result = await instagram_proxy.download(kind, match.identifier, label=match.content_type.value)
                else:
                    result = await download(clean_url, max_bytes=config.MAX_SOURCE_MB * 1024 * 1024)
            except DownloadFailure as fail:
                await interaction.followup.send(_ERROR_MESSAGES.get(fail.kind, _ERROR_MESSAGES[ExtractError.UNKNOWN]))
                return
            except Exception:  # noqa: BLE001
                logger.exception("unexpected failure downloading %s", clean_url)
                await interaction.followup.send("Unexpected error while downloading that link.")
                return

        try:
            await self._send_result(interaction, match, result)
        finally:
            result.cleanup()

    async def _send_result(self, interaction: discord.Interaction, match: platforms.MatchResult, result) -> None:
        ready: list[Path] = []
        skipped = 0

        for f in result.files:
            path = f
            if path.stat().st_size > config.UPLOAD_LIMIT_BYTES:
                if media.ffmpeg_available() and path.suffix.lower() in (".mp4", ".mov", ".mkv", ".webm"):
                    compressed = await media.compress_to_fit(path, config.UPLOAD_LIMIT_BYTES)
                    if compressed is not None:
                        path.unlink(missing_ok=True)
                        result.files[result.files.index(f)] = compressed
                        path = compressed
                if path.stat().st_size > config.UPLOAD_LIMIT_BYTES:
                    skipped += 1
                    continue
            ready.append(path)

        if not ready:
            await interaction.followup.send(
                "Downloaded the media, but every file was too large for this server's "
                f"upload limit ({config.UPLOAD_LIMIT_BYTES // (1024 * 1024)} MB) even after compression."
            )
            return

        title = result.title or match.label
        header = f"**{title}**" + (f" — {result.uploader}" if result.uploader else "")
        if skipped:
            header += f"\n_(skipped {skipped} file(s) that were too large)_"

        for i in range(0, len(ready), config.MAX_FILES_PER_REQUEST):
            chunk = ready[i : i + config.MAX_FILES_PER_REQUEST]
            files = [discord.File(str(p), filename=p.name) for p in chunk]
            await interaction.followup.send(content=header if i == 0 else None, files=files)

    @download_cmd.error
    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"Slow down -- try again in {error.retry_after:.0f}s."
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return
        logger.exception("unhandled app command error", exc_info=error)
        msg = "Something went wrong handling that command."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(DownloadCog(bot))
