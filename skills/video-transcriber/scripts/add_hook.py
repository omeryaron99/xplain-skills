#!/usr/bin/env python3
"""
Add Hook Overlay - Adds a text hook overlay to the first few seconds of a video.
"""

import subprocess
import sys
import os
import argparse

REMOTION_DIR = os.path.expanduser("~/Tools/remotion-editor")


def get_video_info(video_path):
    """Get video dimensions and duration."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frames / fps if fps > 0 else 0
        cap.release()
        return {'width': width, 'height': height, 'fps': fps, 'duration': duration}
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None


def add_hook_overlay(video_path, hook_text, output_path, duration=3.0):
    """
    Add a text hook overlay to the video.

    Args:
        video_path: Input video path
        hook_text: Text to display as hook
        output_path: Output video path
        duration: How long to show the hook (default 3 seconds)
    """
    info = get_video_info(video_path)
    if not info:
        print("ERROR: Could not get video info")
        return False

    width, height = info['width'], info['height']

    # Calculate font size based on video dimensions (roughly 5% of height)
    font_size = int(height * 0.05)

    # Position: top 1/4 of screen, centered
    # y position at roughly 15-20% from top
    y_pos = int(height * 0.18)

    # Box padding
    box_padding = int(font_size * 0.5)

    # Escape special characters for ffmpeg
    escaped_text = hook_text.replace("'", "'\\''").replace(":", "\\:")

    print(f"Video: {width}x{height}")
    print(f"Hook text: \"{hook_text}\"")
    print(f"Duration: {duration}s")
    print(f"Font size: {font_size}px")

    # Build the drawtext filter
    # - White text with black semi-transparent box behind it
    # - Centered horizontally
    # - Positioned in top 1/4
    # - Only visible for first N seconds
    drawtext_filter = (
        f"drawtext="
        f"text='{escaped_text}':"
        f"fontfile=/System/Library/Fonts/Helvetica.ttc:"
        f"fontsize={font_size}:"
        f"fontcolor=white:"
        f"x=(w-text_w)/2:"
        f"y={y_pos}:"
        f"box=1:"
        f"boxcolor=black@0.7:"
        f"boxborderw={box_padding}:"
        f"enable='lt(t,{duration})'"
    )

    cmd = [
        "npx", "remotion", "ffmpeg",
        "-i", video_path,
        "-vf", drawtext_filter,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "copy",
        "-y",
        output_path
    ]

    print("\nAdding hook overlay...")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REMOTION_DIR)

    if result.returncode != 0:
        print(f"ERROR: {result.stderr[-500:]}")
        return False

    return True


def main():
    parser = argparse.ArgumentParser(description="Add a text hook overlay to the first seconds of a video")
    parser.add_argument("video", help="Video file path")
    parser.add_argument("--hook", "-t", required=True, help="Hook text to display")
    parser.add_argument("--duration", "-d", type=float, default=3.0, help="Duration to show hook (default: 3 seconds)")
    parser.add_argument("--output", "-o", help="Output path (default: adds -hook suffix)")

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"ERROR: Video not found: {args.video}")
        sys.exit(1)

    # Output path
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(args.video)
        output_path = f"{base}-hook{ext}"

    if add_hook_overlay(args.video, args.hook, output_path, args.duration):
        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print(f"Output: {output_path}")
    else:
        print("ERROR: Failed to add hook overlay")
        sys.exit(1)


if __name__ == "__main__":
    main()
