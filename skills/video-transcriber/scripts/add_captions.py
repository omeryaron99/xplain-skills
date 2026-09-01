#!/usr/bin/env python3
"""
Add Captions - Renders video with TikTok-style captions using Remotion.
"""

import subprocess
import sys
import os
import argparse
import json
import shutil

REMOTION_DIR = os.path.expanduser("~/Tools/remotion-editor")
PUBLIC_DIR = os.path.join(REMOTION_DIR, "public")


def convert_whisper_to_remotion(whisper_json_path):
    """
    Convert Whisper transcript JSON to Remotion caption format.

    Whisper format:
    {
        "transcription": [
            {"timestamps": {"from": "00:00:00,000", "to": "00:00:05,000"}, "text": " word word"}
        ]
    }

    Remotion format:
    [
        {"text": "word", "startMs": 0, "endMs": 500, "timestampMs": 0, "confidence": 1}
    ]
    """
    with open(whisper_json_path, 'r') as f:
        data = json.load(f)

    captions = []

    if 'transcription' not in data:
        print("ERROR: No transcription found in JSON")
        return None

    for segment in data['transcription']:
        text = segment.get('text', '').strip()
        if not text or text == '[BLANK_AUDIO]':
            continue

        # Parse timestamps
        start_ms = segment['offsets']['from']
        end_ms = segment['offsets']['to']

        # Split into words and distribute timing
        words = text.split()
        if not words:
            continue

        duration_ms = end_ms - start_ms
        ms_per_word = duration_ms / len(words) if words else 0

        for i, word in enumerate(words):
            word_start = start_ms + int(i * ms_per_word)
            word_end = start_ms + int((i + 1) * ms_per_word)

            captions.append({
                "text": word + " ",
                "startMs": word_start,
                "endMs": word_end,
                "timestampMs": word_start,
                "confidence": 1
            })

    return captions


def setup_remotion_files(video_path, captions, video_name):
    """Copy video and captions to Remotion public folder."""
    # Ensure public directory exists
    os.makedirs(PUBLIC_DIR, exist_ok=True)

    # Copy video
    ext = os.path.splitext(video_path)[1]
    public_video = os.path.join(PUBLIC_DIR, f"{video_name}{ext}")
    print(f"Copying video to {public_video}")
    shutil.copy2(video_path, public_video)

    # Write captions JSON
    public_captions = os.path.join(PUBLIC_DIR, f"{video_name}.json")
    print(f"Writing captions to {public_captions}")
    with open(public_captions, 'w') as f:
        json.dump(captions, f, indent=2)

    return f"{video_name}{ext}"


def render_with_captions(video_filename, output_path):
    """Render the video with captions using Remotion."""
    print("\nRendering with Remotion...")

    # The composition expects src to be the public file path (staticFile format)
    src = video_filename  # Just the filename, Remotion adds the path

    cmd = [
        "npx", "remotion", "render",
        "CaptionedVideo",
        output_path,
        "--props", json.dumps({"src": src}),
        "--log=verbose"
    ]

    print(f"Running: {' '.join(cmd[:5])}...")

    result = subprocess.run(
        cmd,
        cwd=REMOTION_DIR,
        capture_output=False  # Show output in real-time
    )

    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="Add TikTok-style captions to video using Remotion")
    parser.add_argument("video", help="Video file path")
    parser.add_argument("--transcript", "-t", help="Whisper transcript JSON (default: looks for -timestamps.json)")
    parser.add_argument("--output", "-o", help="Output path (default: adds -captioned suffix)")

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"ERROR: Video not found: {args.video}")
        sys.exit(1)

    # Find transcript
    if args.transcript:
        transcript_path = args.transcript
    else:
        # Look for -timestamps.json in same directory
        base = os.path.splitext(args.video)[0]
        transcript_path = f"{base.replace('-trimmed', '').replace('-final', '')}-timestamps.json"
        if not os.path.exists(transcript_path):
            # Try same name but .json
            transcript_path = base + ".json"

    if not os.path.exists(transcript_path):
        print(f"ERROR: Transcript not found: {transcript_path}")
        print("Provide --transcript path or ensure -timestamps.json exists")
        sys.exit(1)

    print(f"Video: {args.video}")
    print(f"Transcript: {transcript_path}")

    # Convert captions
    print("\nConverting transcript to Remotion format...")
    captions = convert_whisper_to_remotion(transcript_path)
    if not captions:
        sys.exit(1)
    print(f"Generated {len(captions)} word captions")

    # Setup files in Remotion public folder
    video_name = os.path.splitext(os.path.basename(args.video))[0]
    video_name = video_name.replace(' ', '-')  # Sanitize
    video_filename = setup_remotion_files(args.video, captions, video_name)

    # Output path
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(args.video)
        output_path = f"{base}-captioned.mp4"

    # Render
    if render_with_captions(video_filename, output_path):
        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print(f"Output: {output_path}")
    else:
        print("\nERROR: Rendering failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
