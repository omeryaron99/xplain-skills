---
name: video-transcriber
description: Transcribe video files using Whisper. Use when you need a transcript from a video file — accepts a local file path or pairs with /video-downloader for URLs.
---

# Video Transcriber Skill

Process raw videos: transcribe, clean, and trim dead space automatically.

## When to Use

When the user:
- Says he recorded new videos
- Provides a video file path
- Provides a video URL (YouTube, Instagram, TikTok)
- Asks to "process", "transcribe", or "trim" a video

## How to Run

## Config

| Setting | Description |
|---------|-------------|
| `TRANSCRIBE_SCRIPT_PATH` | Path to `transcribe.py` (included in this skill's `scripts/` folder) |

```bash
python3 TRANSCRIBE_SCRIPT_PATH/transcribe.py "VIDEO_PATH_OR_URL" --title "Title"
```

**Required:**
- `VIDEO_PATH_OR_URL` - The video file or URL
- `--title` - A short title for the video (used for folder/file names)

**Optional:**
- `--no-trim` - Skip dead space trimming

## What It Does

1. Downloads video (if URL)
2. Transcribes with Whisper
3. Fixes domain-specific spelling (customizable in the script)
4. Removes false starts and repeated takes
5. Trims dead space (pauses > 0.4s)
6. Outputs everything to a project folder

## Output

Creates folder in `~/your-project/raw-videos/`:

```
Title-Name/
├── Title-Name.mov              (original)
├── Title-Name-trimmed.mov      (USE THIS - dead space removed)
├── Title-Name-transcript.txt   (readable transcript)
└── Title-Name-timestamps.json  (for captions/editing)
```

## Example Prompts

- "Process this video: ~/Downloads/video.mov"
- "I just recorded a video about Claude Code, it's in my downloads"
- "Transcribe and trim: https://instagram.com/reel/xyz"

## After Running

Tell the user:
1. Where the trimmed video is
2. How much time was saved
3. Show transcript preview
