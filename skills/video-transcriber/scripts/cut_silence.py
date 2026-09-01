#!/usr/bin/env python3
"""
Cut Silence - Removes actual silence from video using audio amplitude analysis.
Much more accurate than transcript-based cutting.
"""

import subprocess
import sys
import os
import argparse
import tempfile
import shutil
import re

REMOTION_DIR = os.path.expanduser("~/Tools/remotion-editor")


def detect_silence_ffmpeg(video_path, silence_threshold_db=-35, min_silence_duration=0.1):
    """
    Use ffmpeg silencedetect filter to find silent parts.

    Args:
        video_path: Path to video
        silence_threshold_db: Volume threshold for silence (default -30dB)
        min_silence_duration: Minimum silence duration in seconds (default 0.15s)

    Returns:
        List of (start, end) tuples for silent sections
    """
    print(f"Detecting silence (threshold: {silence_threshold_db}dB, min duration: {min_silence_duration}s)...")

    cmd = [
        "npx", "remotion", "ffmpeg",
        "-i", video_path,
        "-vn",  # Disable video processing for audio analysis
        "-af", f"silencedetect=noise={silence_threshold_db}dB:d={min_silence_duration}",
        "-f", "null", "/dev/null"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REMOTION_DIR)

    # Parse silencedetect output from stderr
    output = result.stderr

    silences = []
    silence_start = None

    for line in output.split('\n'):
        if 'silence_start:' in line:
            match = re.search(r'silence_start:\s*([\d.]+)', line)
            if match:
                silence_start = float(match.group(1))
        elif 'silence_end:' in line and silence_start is not None:
            match = re.search(r'silence_end:\s*([\d.]+)', line)
            if match:
                silence_end = float(match.group(1))
                silences.append((silence_start, silence_end))
                silence_start = None

    return silences


def get_speech_segments(video_duration, silences, padding=0.01):
    """
    Convert silence periods to speech segments.

    Args:
        video_duration: Total video duration in seconds
        silences: List of (start, end) tuples for silent parts
        padding: Small padding to avoid cutting into speech (default 0.02s = 20ms)

    Returns:
        List of (start, end) tuples for speech segments
    """
    if not silences:
        return [(0, video_duration)]

    segments = []
    current_pos = 0

    for silence_start, silence_end in sorted(silences):
        # Speech segment before this silence
        speech_end = silence_start + padding  # Slight padding into silence
        if speech_end > current_pos:
            segments.append((current_pos, min(speech_end, silence_start)))

        # Move position to end of silence
        current_pos = max(silence_end - padding, silence_start)  # Slight padding into silence

    # Final segment after last silence
    if current_pos < video_duration:
        segments.append((current_pos, video_duration))

    # Filter out tiny segments
    segments = [(s, e) for s, e in segments if e - s > 0.1]

    return segments


def format_time(seconds):
    """Convert seconds to ffmpeg time format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def get_video_duration(video_path):
    """Get video duration in seconds."""
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


def cut_and_concat_fast(video_path, segments, output_path):
    """
    Cut video segments and concatenate using stream copy where possible.
    Falls back to re-encoding for precise cuts.
    """
    if not segments:
        print("ERROR: No segments to keep")
        return False

    print(f"\nCutting {len(segments)} speech segments...")

    temp_dir = tempfile.mkdtemp(prefix="silence_cut_")
    segment_files = []

    try:
        for i, (start, end) in enumerate(segments):
            segment_file = os.path.join(temp_dir, f"seg_{i:04d}.mp4")
            segment_files.append(segment_file)

            duration = end - start
            print(f"  [{i+1}/{len(segments)}] {format_time(start)} -> {format_time(end)} ({duration:.2f}s)")

            # Use re-encoding for precise cuts (stream copy can miss keyframes)
            cmd = [
                "npx", "remotion", "ffmpeg",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(duration),
                "-c:v", "libx264",
                "-preset", "ultrafast",  # Fast encoding
                "-crf", "18",  # Good quality
                "-c:a", "aac",
                "-avoid_negative_ts", "make_zero",
                "-y",
                segment_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=REMOTION_DIR)
            if result.returncode != 0:
                print(f"    ERROR: {result.stderr[:200]}")
                return False

        # Create concat list
        concat_list = os.path.join(temp_dir, "list.txt")
        with open(concat_list, 'w') as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        print(f"\nConcatenating...")

        concat_cmd = [
            "npx", "remotion", "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",  # Fast concat since segments are already encoded
            "-y",
            output_path
        ]

        result = subprocess.run(concat_cmd, capture_output=True, text=True, cwd=REMOTION_DIR)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr[:500]}")
            return False

        return True

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Remove silence from video using audio analysis")
    parser.add_argument("video", help="Video file path")
    parser.add_argument("--threshold", type=int, default=-35,
                       help="Silence threshold in dB (default: -35, lower = more sensitive)")
    parser.add_argument("--min-silence", type=float, default=0.1,
                       help="Minimum silence duration to cut in seconds (default: 0.1)")
    parser.add_argument("--padding", type=float, default=0.01,
                       help="Padding around speech in seconds (default: 0.01)")
    parser.add_argument("--output", help="Output path (default: adds -cut suffix)")

    args = parser.parse_args()

    video_path = args.video
    if not os.path.exists(video_path):
        print(f"ERROR: Video not found: {video_path}")
        sys.exit(1)

    # Get duration
    duration = get_video_duration(video_path)
    print(f"Video: {video_path}")
    print(f"Duration: {duration:.1f}s")

    # Detect silence
    silences = detect_silence_ffmpeg(
        video_path,
        silence_threshold_db=args.threshold,
        min_silence_duration=args.min_silence
    )

    print(f"Found {len(silences)} silent sections:")
    total_silence = 0
    for i, (start, end) in enumerate(silences):
        dur = end - start
        total_silence += dur
        print(f"  {i+1}. {format_time(start)} -> {format_time(end)} ({dur:.2f}s)")

    if not silences:
        print("\nNo silence detected. Try lowering --threshold (e.g., -35 or -40)")
        sys.exit(0)

    # Convert to speech segments
    segments = get_speech_segments(duration, silences, padding=args.padding)

    speech_duration = sum(e - s for s, e in segments)
    print(f"\nSpeech segments: {len(segments)}")
    print(f"Total silence to remove: {total_silence:.2f}s")
    print(f"Expected output: {speech_duration:.1f}s")

    # Output path
    if args.output:
        output_path = args.output
    else:
        base, ext = os.path.splitext(video_path)
        output_path = f"{base}-cut{ext}"

    # Cut and concat
    if cut_and_concat_fast(video_path, segments, output_path):
        new_duration = get_video_duration(output_path)
        saved = duration - new_duration

        print("\n" + "=" * 50)
        print("SUCCESS!")
        print("=" * 50)
        print(f"Output: {output_path}")
        print(f"Original: {duration:.1f}s")
        print(f"New: {new_duration:.1f}s")
        print(f"Removed: {saved:.1f}s ({saved/duration*100:.0f}%)")
    else:
        print("ERROR: Failed to process video")
        sys.exit(1)


if __name__ == "__main__":
    main()
