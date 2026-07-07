# Discord Media Downloader

A private Discord bot with one job: take a link to a public TikTok, Instagram,
YouTube, or X/Twitter post and reply with the actual media file(s) — no
platform login, no personal account credentials, public content only.

```
/download url:<link>
```

---

## How it actually works

There is no bespoke scraper per platform in here. Instead:

1. **`core/platforms.py`** matches the URL against known patterns for each
   platform and classifies the *content type* (video / short-form /
   photo-post / story / highlight), purely with regex — no network call.
   This lets the bot reject junk links instantly and route Instagram
   stories/highlights to the proxy workaround (below) instead of yt-dlp.
2. **`core/extractor.py`** hands everything else to
   **[yt-dlp](https://github.com/yt-dlp/yt-dlp)**, which does the real
   extraction/scraping. yt-dlp maintains hundreds of site-specific
   extractors and — critically — gets updated within days whenever a
   platform changes its API/HTML, which a bespoke scraper written once here
   never could keep up with on its own.
3. **`core/instagram_proxy.py`** handles Instagram stories/highlights
   specifically, since yt-dlp (like everything else with no login) can't
   reach those. See **Instagram story/highlight workaround** below.
4. **`core/media.py`** checks the downloaded file(s) against Discord's
   attachment size limit and, if needed, re-encodes with `ffmpeg` to fit.
5. **`cogs/download.py`** is the Discord-facing slash command: it defers the
   interaction (downloads can take longer than Discord's 3s ack window),
   runs the download in a bounded semaphore (so one bot can't get itself
   rate-limited/IP-banned by hammering a platform with concurrent requests),
   and uploads whatever comes out.

### Why yt-dlp instead of hand-written scrapers

Writing a raw HTML/regex scraper per platform *feels* simpler at first, but:

* TikTok, Instagram, and X all serve their pages via JS-rendered
  client-side apps with signed/obfuscated API calls that change routinely —
  a hand-rolled scraper breaks every few months and needs constant repair.
* yt-dlp already solves format selection (merging separate video+audio
  streams, picking the best quality under a size/resolution cap),
  redirects/short-links, and carousel/slideshow (multi-file) posts.
* It's what virtually every serious "Discord media downloader" project in
  the wild is built on, for the reasons above.

The tradeoff: you inherit yt-dlp's release cadence. When a platform breaks
extraction, `pip install -U yt-dlp` is usually the fix within a few days.
See **Maintenance** below.

---

## Per-platform capability matrix

This bot deliberately runs with **no cookies, no saved login, no browser
profile import**. That is a hard requirement from the project brief ("no
keys of my own account, only what's public") and it has real consequences:

| Platform | Content type | Works without login? | Notes |
|---|---|---|---|
| YouTube | Standard video | Yes | |
| YouTube | Shorts | Yes | |
| YouTube | Age-restricted / members-only | No | Requires a logged-in session; will fail with a login-required message |
| TikTok | Standard video | Yes | |
| TikTok | Photo-mode / slideshow post | Yes | Downloaded as multiple image files (+ audio track when present) |
| Instagram | Public post / carousel | Yes | |
| Instagram | Reel | Yes | |
| Instagram | IGTV | Yes | |
| Instagram | **Story** | **Via proxy workaround** | See below — best-effort, not guaranteed |
| Instagram | **Highlight** | **Via proxy workaround** | Same as story, when the proxy provider supports highlight lookup |
| Instagram | Private account (anything) | No | Proxy providers can't get at these either -- they're scraping public-facing pages too |
| X / Twitter | Tweet with video/GIF | Yes | |

---

## Instagram story/highlight workaround

Instagram's story/highlight endpoint (`reels_media`, under the hood) only
serves media to requests carrying an authenticated session cookie —
**even for fully public accounts**. This isn't a yt-dlp limitation, it's
how Instagram's backend is gated; tools like `instaloader` hit the same
wall and require a login for this one content type specifically. There is
no first-party unauthenticated path around it.

**The workaround** (`core/instagram_proxy.py`): a handful of free,
ad-supported "Instagram story viewer" websites do this same authenticated
fetch *server-side*, using their own pool of logged-in accounts, and expose
the resulting media as plain CDN links on a public page. The bot fetches
that page and pulls the real `cdninstagram.com` / `fbcdn.net` URLs out of
it with a regex, then downloads them directly. **You still never provide
any login of your own** — the third-party site's backend is the one
holding a session, not you or this bot.

This is, by construction, the least stable part of the whole project:

- These are unofficial, undocumented sites. They rename routes, add
  captchas, rate-limit aggressively, or vanish entirely without notice.
- `PROVIDERS` in `core/instagram_proxy.py` lists several (currently
  `storiesig.info`, `imginn.com`, `anonyig.com`) tried in order, so one
  going down doesn't kill the feature — but all of them going down at once
  is entirely possible.
- Extraction doesn't parse any provider's specific page structure/JSON
  schema. It scans whatever comes back for literal Instagram CDN URLs,
  which is the most change-resistant thing to key off (the markup around
  it drifts constantly; the CDN URL shape itself does not).

**This could not be verified live** while building it — the sandbox this
was built in has no general internet access (only package registries are
reachable), so none of the three providers above have been confirmed
working against real Instagram content yet.

**After deploying somewhere with real internet access, check it directly**
without needing the whole bot running:

```bash
python -m core.instagram_proxy story <a public account's username>
python -m core.instagram_proxy highlight <a highlight id, from a stories/highlights/<id> URL>
```

This prints every media URL each provider finds, or says none did. If all
three come back empty:

1. Open one of the provider sites in a real browser and confirm *it*
   still works for that username manually — if the site itself is down or
   redesigned, that explains it.
2. If the site works in a browser but the script finds nothing, the page
   is probably now rendering results via client-side JS the plain HTTP
   fetch never executes. Open browser devtools → Network tab while using
   the site, find the actual XHR/fetch request that returns the media
   URLs, and add that as a new template (or swap in a different provider)
   in `PROVIDERS`.
3. Add a currently-working provider by appending a `Provider(...)` entry —
   no other code needs to change, since extraction is the same generic
   regex scan regardless of provider.

If you'd rather not depend on these at all, the only fully-reliable
alternative is providing a real Instagram session cookie (`cookiefile` in
yt-dlp) — which is exactly the "keys of my own account" this project was
built to avoid, so it isn't wired in here. It's a one-line change in
`core/extractor.py`'s `_build_opts` (`opts["cookiefile"] = "..."`) if you
ever decide that tradeoff is worth it for your own use.

---

## Common pitfalls (and how this project handles them)

- **Platforms change constantly, breaking extraction.** Mitigation: pin
  loosely (`yt-dlp>=...`) and re-run `pip install -U yt-dlp` regularly — see
  Maintenance. There is no way to fully insulate against this; it's the
  nature of unofficial API access.
- **Discord's 3-second interaction ack window.** A video download routinely
  takes longer than that. The command calls `interaction.response.defer()`
  immediately and does all the real work before a `followup.send()`.
- **Blocking the bot's event loop.** yt-dlp's network/extraction calls are
  synchronous. Every call goes through `asyncio.to_thread(...)` so the bot
  keeps responding to Discord's gateway heartbeat while a download runs.
- **Discord's attachment size limit.** Defaults to 25 MB (no server boost);
  50 MB / 100 MB at higher boost levels. Configurable via
  `DISCORD_UPLOAD_LIMIT_MB`. Oversized files get one re-encode pass via
  `ffmpeg` (bitrate + resolution reduced to target); if still too big, that
  file is skipped with a clear message instead of silently failing.
- **Getting your server's IP rate-limited or blocked by a platform.** A
  bot that fires off unlimited concurrent scrapes looks like abuse.
  Mitigations here: a bot-wide semaphore (`MAX_CONCURRENT_DOWNLOADS`,
  default 3) and a per-user cooldown (`COOLDOWN_SECONDS`, default 15s) on
  the slash command.
  If you still get blocked, the current session simply fails until the
  block lifts — there's no proxy rotation built in on purpose (adds
  complexity/cost and starts trending toward ToS-evasion, which is out of
  scope for a private personal-use bot).
  If you *have* a proxy or VPN and want to route yt-dlp through it, set the
  standard `HTTP_PROXY`/`HTTPS_PROXY` environment variables — yt-dlp
  respects them automatically. Nothing else needs to change.
- **Disk filling up.** Files download to a per-request temp directory under
  `downloads/` and are deleted immediately after being sent to Discord
  (success or failure). A hard ceiling (`MAX_SOURCE_MB`, default 500MB) also
  stops a mistaken link to a multi-hour video from filling the disk before
  the size check ever runs.
- **Carousels/slideshows (multiple files per link).** Handled generically:
  yt-dlp returns a multi-entry result for these, and the bot uploads up to
  10 files per Discord message (Discord's own attachment cap), batching
  into multiple messages if there are more.
- **Instagram stories/highlights need a workaround, not just a login-required
  error.** See the dedicated section above — this is the most fragile
  integration in the project because it depends on third-party sites this
  bot doesn't control.
- **Legal/ToS considerations.** Downloading media from these platforms is
  against most of their Terms of Service even when the content is public.
  This bot is intended for personal, private-server use (e.g., saving a
  clip a friend shared, archiving your own content) — not redistribution.
  You are responsible for how it's used on your server.

---

## Setup

### 1. Requirements

- Python 3.10+
- `ffmpeg` on PATH (needed by yt-dlp itself for merging video+audio, and by
  the size-compression fallback)
- A Discord account with permission to add bots to your private server

### 2. Create the Discord application (this is *not* your personal account)

The bot needs its own application/token to connect to Discord at all — this
is unrelated to "logging in" to TikTok/Instagram/etc., which this project
never does.

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**.
2. Name it, then open **Bot** in the sidebar → **Reset Token** → copy it.
   This goes in `.env` as `DISCORD_BOT_TOKEN`. Treat it like a password —
   anyone with it can control the bot.
3. No privileged intents are required (the bot only uses slash commands,
   not message content), so leave those toggles off.
4. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot permissions: `Send Messages`, `Attach Files`, `Embed Links`,
     `Read Message History`, `Use Slash Commands`
5. Copy the generated URL, open it in your browser, pick your private
   server, and authorize it.
6. (Recommended for development) Right-click your server in Discord →
   **Copy Server ID** (enable Developer Mode in Discord settings if you
   don't see this) → put it in `.env` as `DISCORD_GUILD_ID`. This makes
   slash commands sync to your server instantly instead of waiting up to an
   hour for a global sync.

### 3. Configure and install

```bash
cp .env.example .env
# edit .env: paste DISCORD_BOT_TOKEN, DISCORD_GUILD_ID, adjust limits if you want

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Install ffmpeg if you don't have it:

```bash
# Debian/Ubuntu
sudo apt-get install ffmpeg
# macOS (Homebrew)
brew install ffmpeg
```

### 4. Run it

```bash
python bot.py
```

You should see `synced app commands to guild <id>` and `logged in as
<botname>` in the logs. In your private server, typing `/download` should
now show the command with an autocomplete description.

### 5. Deploy to a private server (Docker — recommended for "leave it running")

```bash
docker compose up -d --build
```

This builds the image (Python + ffmpeg + deps), runs the bot with
`restart: unless-stopped`, and mounts `./downloads` so temp files are
visible on the host if you ever need to debug a stuck job (they're deleted
automatically in normal operation).

To update after a `yt-dlp` release fixes a broken extractor:

```bash
docker compose build --no-cache && docker compose up -d
```

#### Without Docker (systemd, e.g. a home server or VPS)

```ini
# /etc/systemd/system/media-bot.service
[Unit]
Description=Discord Media Downloader
After=network.target

[Service]
WorkingDirectory=/path/to/discord-media-downloader
ExecStart=/path/to/discord-media-downloader/.venv/bin/python bot.py
Restart=on-failure
EnvironmentFile=/path/to/discord-media-downloader/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now media-bot
journalctl -u media-bot -f   # tail logs
```

---

## Testing

`tests/test_platforms.py` and `tests/test_instagram_proxy.py` cover
URL-to-platform/content-type classification and the CDN-URL scraping regex
with plain unit tests (no network involved):

```bash
pip install pytest
pytest tests/ -v
```

**What unit tests can't cover:** actually calling yt-dlp or the Instagram
proxy providers against live sites requires real internet access to those
domains. (This project was built in a sandboxed environment with egress
restricted to package registries only, so none of this could be exercised
live there.) Once you've deployed this somewhere with normal internet
access, sanity-check each platform once, e.g.:

```bash
# Should print JSON metadata without downloading anything
yt-dlp -j "https://www.youtube.com/watch?v=<some public video>"
yt-dlp -j "https://www.tiktok.com/@<user>/video/<id>"
yt-dlp -j "https://www.instagram.com/reel/<shortcode>/"
yt-dlp -j "https://x.com/<user>/status/<id>"

# Instagram story/highlight proxy workaround -- see the dedicated section above
python -m core.instagram_proxy story <username>
python -m core.instagram_proxy highlight <highlight id>
```

If the yt-dlp checks fail with an extractor error (not a login/availability
error), it's almost always fixed by updating yt-dlp (see Maintenance). If
the proxy checks come back empty, see the troubleshooting steps in the
workaround section above. Then run `/download` with one link per platform
in your actual server to confirm the whole path — Discord upload included.

---

## Maintenance

yt-dlp ships frequent releases to keep up with platform changes. When a
previously-working link suddenly fails with an extractor-looking error:

```bash
pip install -U yt-dlp        # bare-metal
# or
docker compose build --no-cache && docker compose up -d   # docker
```

Consider a periodic reminder (weekly cron, or just doing it whenever
something breaks) to update rather than pinning an exact version forever.

---

## Configuration reference (`.env`)

| Variable | Default | Meaning |
|---|---|---|
| `DISCORD_BOT_TOKEN` | *(required)* | The bot application's token |
| `DISCORD_GUILD_ID` | *(unset = global sync)* | Your private server's ID, for instant command sync |
| `DISCORD_UPLOAD_LIMIT_MB` | 25 | Match your server's actual boost-tier upload cap |
| `MAX_CONCURRENT_DOWNLOADS` | 3 | Bot-wide concurrency cap |
| `COOLDOWN_SECONDS` | 15 | Per-user cooldown on `/download` |
| `MAX_SOURCE_MB` | 500 | Safety ceiling on the source file before compression |

---

## Project layout

```
bot.py                    entrypoint: intents, extension loading, command sync
config.py                 env var loading
core/
  platforms.py            URL -> (platform, content type) classification
  extractor.py            async yt-dlp wrapper + error classification
  instagram_proxy.py       story/highlight workaround via third-party proxies
  media.py                 ffprobe/ffmpeg size-compression fallback
cogs/
  download.py              the /download slash command
tests/
  test_platforms.py        classification unit tests
  test_instagram_proxy.py  CDN-URL scraping regex unit tests
```
