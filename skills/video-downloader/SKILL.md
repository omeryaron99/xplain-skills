---
name: video-downloader
description: Download videos from YouTube, Instagram, TikTok, Twitter/X, and other platforms. Use when a video URL is provided and needs to be downloaded locally.
---

# Video Downloader Skill

Download videos from YouTube, Instagram, TikTok, Twitter/X, and other platforms.

## Usage

When the user provides a video URL to download (for watching, analysis, or importing into Remotion), use this skill.

## Prerequisites

- **yt-dlp** must be installed (`pip install yt-dlp` or `brew install yt-dlp`)

## Config

| Setting | Description |
|---------|-------------|
| `DOWNLOAD_SCRIPT_PATH` | Path to `download_video.py` (included in this skill's `scripts/` folder) |

## How to Download

Run the download script:

```bash
python3 DOWNLOAD_SCRIPT_PATH/download_video.py "VIDEO_URL" -o "OUTPUT_DIR" -q QUALITY -f FORMAT
```

### Parameters

| Flag | Description | Default |
|------|-------------|---------|
| `-o` | Output directory | `/tmp/downloads` |
| `-q` | Quality: `best`, `1080`, `720`, `480`, `360` | `best` |
| `-f` | Format: `mp4`, `webm`, `mkv` | `mp4` |
| `-a` | Audio only (MP3) | false |

### Examples

**Download YouTube video:**
```bash
python3 DOWNLOAD_SCRIPT_PATH/download_video.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" -o /tmp/downloads
```

**Download Instagram reel:**
```bash
python3 DOWNLOAD_SCRIPT_PATH/download_video.py "https://www.instagram.com/reel/ABC123/" -o /tmp/downloads
```

**Download for Remotion project:**
```bash
python3 DOWNLOAD_SCRIPT_PATH/download_video.py "VIDEO_URL" -o YOUR_OUTPUT_DIRECTORY
```

**Download 720p quality:**
```bash
python3 DOWNLOAD_SCRIPT_PATH/download_video.py "VIDEO_URL" -q 720 -o /tmp/downloads
```

## Supported Platforms

- YouTube
- Instagram (reels, posts)
- TikTok
- Twitter/X
- Facebook
- Vimeo
- And 1000+ other sites supported by yt-dlp

## After Download

1. The script outputs the downloaded file path
2. Use that path for further processing (Remotion import, frame extraction, etc.)
3. For Remotion: copy to `public/raw/` folder or download directly there

## Workflow Integration

When user says things like:
- "Download this video: [URL]"
- "Get this reel for me: [URL]"
- "I need this video in Remotion: [URL]"

Use this skill to download, then:
1. Report the downloaded file path
2. If for Remotion, move/copy to appropriate folder
3. If for analysis, extract frames with opencv
