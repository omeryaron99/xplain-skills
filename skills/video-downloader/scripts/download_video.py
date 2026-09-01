#!/usr/bin/env python3
"""
Video Downloader - Downloads videos from YouTube, Instagram, TikTok, and more.
Uses yt-dlp as the backend.
"""

import subprocess
import sys
import os
import argparse
import json

def check_yt_dlp():
    """Check if yt-dlp is installed, install if not."""
    try:
        subprocess.run([sys.executable, "-m", "yt_dlp", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing yt-dlp...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--user", "yt-dlp"], check=True)
        return True

def get_video_info(url):
    """Get video metadata without downloading."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--dump-json", "--no-playlist", url],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting video info: {e.stderr}")
        return None

def download_video(url, output_dir, quality="best", format="mp4", audio_only=False):
    """Download video with specified settings."""

    os.makedirs(output_dir, exist_ok=True)

    # Build yt-dlp command (use python module for compatibility)
    cmd = [sys.executable, "-m", "yt_dlp", "--no-playlist"]

    # Output template
    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")
    cmd.extend(["-o", output_template])

    if audio_only:
        cmd.extend(["-x", "--audio-format", "mp3"])
    else:
        # Quality selection - prefer pre-merged formats (best) to avoid ffmpeg requirement
        # Fall back to separate streams only if needed
        if quality == "best":
            format_str = "best[ext=mp4]/best"  # Prefer single stream mp4
        elif quality in ["1080", "1080p"]:
            format_str = "best[height<=1080][ext=mp4]/best[height<=1080]/best"
        elif quality in ["720", "720p"]:
            format_str = "best[height<=720][ext=mp4]/best[height<=720]/best"
        elif quality in ["480", "480p"]:
            format_str = "best[height<=480][ext=mp4]/best[height<=480]/best"
        elif quality in ["360", "360p"]:
            format_str = "best[height<=360][ext=mp4]/best[height<=360]/best"
        else:
            format_str = "best"

        cmd.extend(["-f", format_str])

    # Add URL
    cmd.append(url)

    # Get video info first
    print(f"Fetching video info...")
    info = get_video_info(url)
    if info:
        print(f"Title: {info.get('title', 'Unknown')}")
        print(f"Duration: {info.get('duration', 'Unknown')} seconds")
        print(f"Uploader: {info.get('uploader', 'Unknown')}")
        print()

    # Download
    print(f"Downloading to: {output_dir}")
    print(f"Quality: {quality}, Format: {'mp3' if audio_only else format}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, check=True)

        # Find the downloaded file
        if info:
            title = info.get('title', 'video')
            # Sanitize title for filename matching
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            ext = "mp3" if audio_only else format

            # Look for the file
            for f in os.listdir(output_dir):
                if f.endswith(f".{ext}"):
                    filepath = os.path.join(output_dir, f)
                    print("-" * 50)
                    print(f"SUCCESS! Downloaded to:")
                    print(filepath)
                    return filepath

        print("-" * 50)
        print(f"Download complete! Check: {output_dir}")
        return output_dir

    except subprocess.CalledProcessError as e:
        print(f"Download failed: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Download videos from various platforms")
    parser.add_argument("url", help="Video URL to download")
    parser.add_argument("-o", "--output", default="/tmp/downloads", help="Output directory")
    parser.add_argument("-q", "--quality", default="best",
                       choices=["best", "1080", "1080p", "720", "720p", "480", "480p", "360", "360p"],
                       help="Video quality")
    parser.add_argument("-f", "--format", default="mp4",
                       choices=["mp4", "webm", "mkv"],
                       help="Output format")
    parser.add_argument("-a", "--audio-only", action="store_true",
                       help="Download audio only as MP3")

    args = parser.parse_args()

    # Check yt-dlp
    check_yt_dlp()

    # Download
    result = download_video(
        url=args.url,
        output_dir=args.output,
        quality=args.quality,
        format=args.format,
        audio_only=args.audio_only
    )

    if result:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
