#!/usr/bin/env python3
"""
Cut Dead Space - Removes silence/gaps from video based on transcript timestamps.
"""

import subprocess
import sys
import os
import json
import argparse
import tempfile
import shutil

REMOTION_DIR = os.path.expanduser("~/Tools/remotion-editor")


def get_speech_segments(json_path, min_gap_ms=500, padding_ms=100):
    """
    Extract speech segments from transcript JSON.

    Args:
        json_path: Path to timestamps JSON
        min_gap_ms: Minimum gap (ms) to consider as dead space (default 500ms)
        padding_ms: Padding to add around speech (default 100ms)

    Returns:
        List of (start_ms, end_ms) tuples for speech segments
    """
    with open(json_path, 'r') as f:
        data = json.load(f)

    if 'transcription' not in data:
        print("ERROR: No transcription data found")
        return []

    segments = []

    for item in data['transcription']:
        start = item['offsets']['from']
        end = item['offsets']['to']
        text = item['text'].strip()

        # Skip blank audio markers
        if not text or text == '[BLANK_AUDIO]':
            continue

        segments.append((start, end))

    if not segments:
        return []

    # Merge segments that are close together (less than min_gap_ms apart)
    merged = []
    current_start, current_end = segments[0]

    for start, end in segments[1:]:
        gap = start - current_end

        if gap < min_gap_ms:
            # Extend current segment
            current_end = end
        else:
            # Save current and start new
            merged.append((
                max(0, current_start - padding_ms),
                current_end + padding_ms
            ))
            current_start, current_end = start, end

    # Don't forget the last segment
    merged.append((
        max(0, current_start - padding_ms),
        current_end + padding_ms
    ))

    return merged


def format_time(ms):
    """Convert milliseconds to ffmpeg time format (HH:MM:SS.mmm)"""
    seconds = ms / 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def cut_and_concat(video_path, segments, output_path):
    """
    Cut video to keep only speech segments and concatenate.

    Uses ffmpeg filter_complex for seamless cutting.
    """
    if not segments:
        print("ERROR: No segments to keep")
        return False

    print(f"\nCutting {len(segments)} speech segments...")

    # Create temp directory for segment files
    temp_dir = tempfile.mkdtemp(prefix="deadspace_")
    segment_files = []

    try:
        # Cut each segment
        for i, (start_ms, end_ms) in enumerate(segments):
            segment_file = os.path.join(temp_dir, f"segment_{i:04d}.mp4")
            segment_files.append(segment_file)

            duration_ms = end_ms - start_ms

            print(f"  Segment {i+1}/{len(segments)}: {format_time(start_ms)} -> {format_time(end_ms)} ({duration_ms/1000:.1f}s)")

            cmd = [
                "npx", "remotion", "ffmpeg",
                "-ss", format_time(start_ms),
                "-i", video_path,
                "-t", format_time(duration_ms),
                "-c:v", "libx264",
                "-preset", "fast",
                "-c:a", "aac",
                "-avoid_negative_ts", "make_zero",
                "-y",
                segment_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=REMOTION_DIR)

            if result.returncode != 0:
                print(f"    ERROR cutting segment: {result.stderr[:200]}")
                return False

        # Create concat list file
        concat_list = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_list, 'w') as f:
            for seg_file in segment_files:
                f.write(f"file '{seg_file}'\n")

        # Concatenate all segments
        print(f"\nConcatenating {len(segment_files)} segments...")

        concat_cmd = [
            "npx", "remotion", "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-y",
            output_path
        ]

        result = subprocess.run(concat_cmd, capture_output=True, text=True, cwd=REMOTION_DIR)

        if result.returncode != 0:
            print(f"ERROR concatenating: {result.stderr[:500]}")
            return False

        return True

    finally:
        # Clean up temp files
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_video_duration(video_path):
    """Get video duration in seconds using opencv."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frames / fps if fps > 0 else 0
        cap.release()
        return duration
    except:
        return 0


def main():
    parser = argparse.ArgumentParser(description="Remove dead space from video based on transcript")
    parser.add_argument("project_dir", help="Project directory containing video and timestamps JSON")
    parser.add_argument("--min-gap", type=int, default=500, help="Minimum gap (ms) to cut (default: 500)")
    parser.add_argument("--padding", type=int, default=100, help="Padding (ms) around speech (default: 100)")
    parser.add_argument("--output", help="Output filename (default: adds '-cut' suffix)")

    args = parser.parse_args()

    project_dir = args.project_dir

    # Find video and timestamps files
    video_file = None
    timestamps_file = None

    for f in os.listdir(project_dir):
        if f.endswith('-timestamps.json'):
            timestamps_file = os.path.join(project_dir, f)
        elif f.endswith(('.mp4', '.mov', '.webm', '.mkv')) and '-cut' not in f:
            video_file = os.path.join(project_dir, f)

    if not video_file:
        print("ERROR: No video file found in project directory")
        sys.exit(1)

    if not timestamps_file:
        print("ERROR: No timestamps JSON found. Run transcribe.py first.")
        sys.exit(1)

    print(f"Video: {video_file}")
    print(f"Timestamps: {timestamps_file}")

    # Get original duration
    original_duration = get_video_duration(video_file)
    print(f"Original duration: {original_duration:.1f}s")

    # Extract speech segments
    segments = get_speech_segments(
        timestamps_file,
        min_gap_ms=args.min_gap,
        padding_ms=args.padding
    )

    if not segments:
        print("ERROR: No speech segments found")
        sys.exit(1)

    # Calculate expected duration
    total_speech_ms = sum(end - start for start, end in segments)
    print(f"Speech segments: {len(segments)}")
    print(f"Expected output duration: {total_speech_ms/1000:.1f}s")
    print(f"Removing: {original_duration - total_speech_ms/1000:.1f}s of dead space")

    # Determine output path
    if args.output:
        output_path = os.path.join(project_dir, args.output)
    else:
        base, ext = os.path.splitext(video_file)
        output_path = f"{base}-cut{ext}"

    # Cut and concatenate
    if cut_and_concat(video_file, segments, output_path):
        # Verify output
        new_duration = get_video_duration(output_path)
        saved = original_duration - new_duration

        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print(f"\nOutput: {output_path}")
        print(f"Original: {original_duration:.1f}s")
        print(f"New: {new_duration:.1f}s")
        print(f"Saved: {saved:.1f}s ({saved/original_duration*100:.0f}% reduction)")
    else:
        print("\nERROR: Failed to process video")
        sys.exit(1)


if __name__ == "__main__":
    main()
