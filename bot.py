from __future__ import annotations

import asyncio
import logging
import os

import discord
from discord.ext import commands

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("mediabot")

INITIAL_EXTENSIONS = ("cogs.download",)


class MediaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        # Slash commands don't need message_content or presence intents at all.
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for ext in INITIAL_EXTENSIONS:
            await self.load_extension(ext)

        guild_id = os.getenv("DISCORD_GUILD_ID")
        if guild_id:
            # Guild-scoped sync propagates instantly -- use this while
            # developing against your one private server.
            guild = discord.Object(id=int(guild_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("synced app commands to guild %s", guild_id)
        else:
            # Global sync can take up to an hour to show up everywhere.
            await self.tree.sync()
            logger.info("synced app commands globally")

    async def on_ready(self):
        logger.info("logged in as %s (id=%s)", self.user, self.user.id if self.user else "?")


def main() -> None:
    if not config.DISCORD_BOT_TOKEN:
        raise SystemExit(
            "DISCORD_BOT_TOKEN is not set. Copy .env.example to .env and fill it in "
            "(see README.md's 'Create the Discord application' section)."
        )
    bot = MediaBot()
    bot.run(config.DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
