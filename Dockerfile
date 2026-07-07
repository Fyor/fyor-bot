FROM python:3.12-slim

# ffmpeg is required both by yt-dlp (merging separate video/audio streams,
# which YouTube in particular serves as) and by core/media.py's compression
# fallback for oversized files.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/downloads

CMD ["python", "bot.py"]
