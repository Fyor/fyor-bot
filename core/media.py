"""Discord attachment-size handling: probing and ffmpeg re-encode fallback.

Discord's per-attachment upload cap depends on the *server's* boost level
(25 MB with no boost, 50 MB at level 2, 100 MB at level 3 as of this
writing -- Discord has changed these numbers before, so it's configurable
via DISCORD_UPLOAD_LIMIT_MB rather than hard-coded). When yt-dlp hands back
a file bigger than that, we re-encode it down with ffmpeg instead of just
failing, since a lot of source video is uploaded at a far higher bitrate
than a Discord embed needs anyway.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger("mediabot.media")

DEFAULT_LIMIT_BYTES = 25 * 1024 * 1024


async def _run(*args: str) -> tuple[int, bytes, bytes]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode, stdout, stderr


async def probe_duration(path: Path) -> float | None:
    code, out, _ = await _run(
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)
    )
    if code != 0:
        return None
    try:
        data = json.loads(out)
        return float(data["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError):
        return None


def _scale_filter_for_bitrate(video_kbps: float) -> str | None:
    if video_kbps < 400:
        return "scale=-2:480"
    if video_kbps < 900:
        return "scale=-2:720"
    return None


async def compress_to_fit(path: Path, max_bytes: int, *, attempts: int = 2) -> Path | None:
    """Re-encode `path` in place (new file alongside it) to fit under max_bytes.

    Returns the path to the compressed file, or None if ffmpeg isn't
    available / compression couldn't hit the target after a couple of tries.
    Caller is responsible for deleting the original if it swaps files.
    """
    duration = await probe_duration(path)
    if not duration or duration <= 0:
        return None

    target = path.with_name(path.stem + "_compressed.mp4")
    safety = 0.92
    remaining_bytes = max_bytes

    for attempt in range(1, attempts + 1):
        total_kbps = (remaining_bytes * 8 / 1000) / duration * safety
        audio_kbps = 128 if total_kbps > 160 else 64
        video_kbps = max(total_kbps - audio_kbps, 100)

        args = [
            "ffmpeg", "-y", "-i", str(path),
            "-c:v", "libx264",
            "-b:v", f"{video_kbps:.0f}k",
            "-maxrate", f"{video_kbps * 1.5:.0f}k",
            "-bufsize", f"{video_kbps * 2:.0f}k",
            "-c:a", "aac", "-b:a", f"{audio_kbps:.0f}k",
            "-movflags", "+faststart",
        ]
        scale = _scale_filter_for_bitrate(video_kbps)
        if scale:
            args += ["-vf", scale]
        args.append(str(target))

        code, _, stderr = await _run(*args)
        if code != 0:
            logger.warning("ffmpeg compression attempt %d failed: %s", attempt, stderr.decode(errors="replace")[-500:])
            return None

        if target.stat().st_size <= max_bytes:
            return target

        # Overshot -- tighten the target and try again.
        remaining_bytes = int(remaining_bytes * 0.8)

    return target if target.exists() and target.stat().st_size <= max_bytes else None


def ffmpeg_available() -> bool:
    import shutil
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
