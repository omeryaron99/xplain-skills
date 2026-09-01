#!/usr/bin/env python3
"""
Video Transcriber - Downloads/copies video, transcribes it, trims dead space, and organizes into project folder.
"""

import subprocess
import sys
import os
import argparse
import json
import re
import shutil
import tempfile

# Paths
REMOTION_DIR = os.path.expanduser("~/Tools/remotion-editor")
WHISPER_BIN = os.path.join(REMOTION_DIR, "whisper.cpp/main")
WHISPER_MODEL = os.path.join(REMOTION_DIR, "whisper.cpp/ggml-medium.en.bin")
DEFAULT_OUTPUT = os.path.expanduser("~/Noe-Work/NoeVarnerAI/Content/PB-Videos")
DOWNLOADER_SCRIPT = os.path.expanduser("~/.claude/skills/video-downloader/scripts/download_video.py")

# Silence detection settings
SILENCE_THRESHOLD_DB = -35
MIN_SILENCE_DURATION = 0.4  # Only cut pauses longer than this (preserves natural speech rhythm)
SPEECH_PADDING = 0.05  # Small padding around speech
SKIP_START_SECONDS = 0.4  # Skip first X seconds to avoid black frames

# Common transcription corrections for tech/AI terms
# Format: "misheard": "correct"
CORRECTIONS = {
    # AI Tools & Companies
    "claud": "Claude",
    "claud's": "Claude's",
    "claude code": "Claude Code",
    "claud code": "Claude Code",
    "cloud code": "Claude Code",
    "anthropic": "Anthropic",
    "open ai": "OpenAI",
    "openai": "OpenAI",
    "chat gpt": "ChatGPT",
    "chatgpt": "ChatGPT",
    "gpt4": "GPT-4",
    "gpt 4": "GPT-4",
    "gemini": "Gemini",
    "mid journey": "Midjourney",
    "midjourney": "Midjourney",
    "stable diffusion": "Stable Diffusion",
    "dall-e": "DALL-E",
    "dolly": "DALL-E",

    # Automation & Dev Tools
    "n8n": "n8n",
    "natan": "n8n",
    "neightn": "n8n",
    "n-8-n": "n8n",
    "nate n": "n8n",
    "remotion": "Remotion",
    "remote in": "Remotion",
    "zapier": "Zapier",
    "zappier": "Zapier",
    "make.com": "Make.com",
    "airtable": "Airtable",
    "air table": "Airtable",
    "supabase": "Supabase",
    "super base": "Supabase",
    "superbase": "Supabase",
    "vercel": "Vercel",
    "netlify": "Netlify",
    "github": "GitHub",
    "git hub": "GitHub",

    # Social Media
    "tiktok": "TikTok",
    "tik tok": "TikTok",
    "tick tock": "TikTok",
    "instagram": "Instagram",
    "insta": "Instagram",
    "youtube": "YouTube",
    "you tube": "YouTube",
    "twitter": "Twitter",
    "x.com": "X",

    # Tech Terms
    "api": "API",
    "apis": "APIs",
    "ai": "AI",
    "llm": "LLM",
    "llms": "LLMs",
    "saas": "SaaS",
    "ui": "UI",
    "ux": "UX",
    "css": "CSS",
    "html": "HTML",
    "javascript": "JavaScript",
    "java script": "JavaScript",
    "typescript": "TypeScript",
    "type script": "TypeScript",
    "python": "Python",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "react": "React",
    "nextjs": "Next.js",
    "next js": "Next.js",
}


def fix_transcription(text):
    """Fix common transcription errors for tech terms."""
    fixed = text

    # Apply corrections (case-insensitive matching, preserve sentence structure)
    for wrong, correct in CORRECTIONS.items():
        # Match whole words only, case insensitive
        pattern = r'\b' + re.escape(wrong) + r'\b'
        fixed = re.sub(pattern, correct, fixed, flags=re.IGNORECASE)

    return fixed


def normalize_for_comparison(text):
    """Normalize text for similarity comparison."""
    # Lowercase, remove punctuation, extra spaces
    normalized = text.lower()
    normalized = re.sub(r'[^\w\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized


def get_word_overlap(text1, text2):
    """Calculate word overlap ratio between two texts."""
    words1 = set(normalize_for_comparison(text1).split())
    words2 = set(normalize_for_comparison(text2).split())

    if not words1 or not words2:
        return 0

    overlap = len(words1 & words2)
    smaller_set = min(len(words1), len(words2))

    return overlap / smaller_set if smaller_set > 0 else 0


def is_incomplete_sentence(text):
    """Check if sentence appears to be cut off mid-thought."""
    text = text.strip()

    # Too short to be complete
    if len(text.split()) < 3:
        return True

    # Ends with words that suggest continuation
    incomplete_endings = [
        ' the', ' a', ' an', ' to', ' of', ' in', ' on', ' at', ' for',
        ' and', ' but', ' or', ' with', ' that', ' this', ' is', ' are',
        ' was', ' were', ' be', ' been', ' being', ' have', ' has', ' had',
        ' do', ' does', ' did', ' will', ' would', ' could', ' should',
        ' can', ' may', ' might', ' must', ' i', ' you', ' we', ' they',
        ' it', ' my', ' your', ' our', ' their', ' its', ' so', ' because',
        ' when', ' where', ' which', ' who', ' what', ' how', ' if',
    ]

    lower_text = text.lower()
    for ending in incomplete_endings:
        if lower_text.endswith(ending):
            return True

    return False


def starts_similarly(text1, text2, threshold=0.6):
    """Check if two texts start with similar words."""
    words1 = normalize_for_comparison(text1).split()[:5]  # First 5 words
    words2 = normalize_for_comparison(text2).split()[:5]

    if not words1 or not words2:
        return False

    # Check if first few words match
    matches = sum(1 for w1, w2 in zip(words1, words2) if w1 == w2)
    return matches >= min(len(words1), len(words2)) * threshold


def remove_false_starts_and_repeats(segments):
    """
    Remove false starts and repeated takes, keeping the final/best version.

    Logic:
    1. If a segment is incomplete and the next one starts similarly -> drop incomplete
    2. If two consecutive segments are very similar -> keep the later one
    3. If a segment is cut off mid-sentence and repeated -> keep the complete version
    """
    if not segments:
        return segments

    cleaned = []
    i = 0

    while i < len(segments):
        current = segments[i]
        current_text = current['text'].strip()

        # Look ahead to check for repeats/restarts
        is_repeat = False

        if i + 1 < len(segments):
            next_seg = segments[i + 1]
            next_text = next_seg['text'].strip()

            # Case 1: Current is incomplete and next starts similarly (false start)
            if is_incomplete_sentence(current_text) and starts_similarly(current_text, next_text):
                print(f"  [Removing false start]: \"{current_text[:50]}...\"")
                is_repeat = True

            # Case 2: Very similar content (repeated take)
            elif get_word_overlap(current_text, next_text) > 0.7:
                print(f"  [Removing repeated take]: \"{current_text[:50]}...\"")
                is_repeat = True

            # Case 3: Current starts the same as next but is shorter (partial repeat)
            elif starts_similarly(current_text, next_text) and len(current_text) < len(next_text) * 0.7:
                print(f"  [Removing partial take]: \"{current_text[:50]}...\"")
                is_repeat = True

        if not is_repeat:
            cleaned.append(current)

        i += 1

    return cleaned


def slugify(title):
    """Convert title to folder-safe name."""
    # Replace spaces with hyphens, remove special chars
    slug = re.sub(r'[^\w\s-]', '', title)
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug.strip('-')


def is_url(path):
    """Check if path is a URL."""
    return path.startswith('http://') or path.startswith('https://')


def get_video_info(video_path):
    """Get video metadata using opencv."""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frames / fps if fps > 0 else 0
        cap.release()
        return {
            'duration': duration,
            'width': width,
            'height': height,
            'fps': fps
        }
    except Exception as e:
        print(f"Warning: Could not get video info: {e}")
        return None


def download_video(url, output_dir):
    """Download video using video-downloader skill."""
    print(f"Downloading video from URL...")
    result = subprocess.run([
        sys.executable, DOWNLOADER_SCRIPT,
        url, "-o", output_dir
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Download error: {result.stderr}")
        return None

    # Find the downloaded file
    for f in os.listdir(output_dir):
        if f.endswith(('.mp4', '.mov', '.webm', '.mkv')):
            return os.path.join(output_dir, f)

    return None


def extract_audio(video_path, audio_path):
    """Extract audio from video for transcription."""
    print("Extracting audio...")
    cmd = [
        "npx", "remotion", "ffmpeg",
        "-i", video_path,
        "-ar", "16000",
        audio_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REMOTION_DIR)
    return result.returncode == 0


def transcribe_audio(audio_path, output_json):
    """Transcribe audio using Whisper."""
    print("Transcribing with Whisper...")
    cmd = [
        WHISPER_BIN,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "-oj",
        "-of", output_json.replace('.json', '')  # Whisper adds .json
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def format_timestamp(ms):
    """Convert milliseconds to MM:SS format."""
    seconds = int(ms / 1000)
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def create_transcript_txt(json_path, txt_path, title, video_info):
    """Convert Whisper JSON to readable transcript."""
    with open(json_path, 'r') as f:
        data = json.load(f)

    lines = [f"{title.upper()} - Transcript", "=" * (len(title) + 14), ""]

    # Group transcription segments
    if 'transcription' in data:
        segments = data['transcription']

        # Remove false starts and repeated takes
        print("Checking for false starts and repeated takes...")
        original_count = len(segments)
        segments = remove_false_starts_and_repeats(segments)
        removed_count = original_count - len(segments)
        if removed_count > 0:
            print(f"  Removed {removed_count} false starts/repeats")

        for segment in segments:
            start = format_timestamp(segment['offsets']['from'])
            end = format_timestamp(segment['offsets']['to'])
            text = segment['text'].strip()
            if text:
                # Fix common transcription errors
                text = fix_transcription(text)
                lines.append(f"[{start} - {end}]")
                lines.append(text)
                lines.append("")

    # Add video info
    lines.append("---")
    if video_info:
        lines.append(f"Duration: {video_info['duration']:.1f} seconds")
        lines.append(f"Resolution: {video_info['width']}x{video_info['height']}")
        lines.append(f"FPS: {video_info['fps']:.0f}")

    with open(txt_path, 'w') as f:
        f.write('\n'.join(lines))

    return lines


def detect_silence(video_path):
    """Detect silent sections in video using ffmpeg silencedetect."""
    print(f"Detecting silence (threshold: {SILENCE_THRESHOLD_DB}dB, min duration: {MIN_SILENCE_DURATION}s)...")

    cmd = [
        "npx", "remotion", "ffmpeg",
        "-i", video_path,
        "-vn",  # Disable video for audio analysis
        "-af", f"silencedetect=noise={SILENCE_THRESHOLD_DB}dB:d={MIN_SILENCE_DURATION}",
        "-f", "null", "/dev/null"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REMOTION_DIR)

    silences = []
    silence_start = None

    for line in result.stderr.split('\n'):
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


def get_speech_segments(duration, silences):
    """Convert silence periods to speech segments."""
    segments = []
    current_pos = SKIP_START_SECONDS  # Start after initial black frame

    for silence_start, silence_end in sorted(silences):
        if silence_start > current_pos:
            segments.append((current_pos, silence_start))
        current_pos = silence_end

    if current_pos < duration:
        segments.append((current_pos, duration))

    # Filter tiny segments
    segments = [(s, e) for s, e in segments if e - s > 0.1]

    return segments


def trim_dead_space(video_path, output_path, video_info):
    """Remove dead space from video using audio analysis."""
    duration = video_info['duration']

    # Detect silence
    silences = detect_silence(video_path)

    if not silences:
        print("No significant silence detected - skipping trim")
        shutil.copy2(video_path, output_path)
        return video_info['duration']

    print(f"Found {len(silences)} silent sections")

    # Get speech segments
    segments = get_speech_segments(duration, silences)

    if not segments:
        print("No speech segments found - skipping trim")
        shutil.copy2(video_path, output_path)
        return video_info['duration']

    total_speech = sum(e - s for s, e in segments)
    total_silence = duration - total_speech

    print(f"Speech segments: {len(segments)}")
    print(f"Removing: {total_silence:.1f}s of dead space")

    # Cut and concatenate segments
    temp_dir = tempfile.mkdtemp(prefix="trim_")
    segment_files = []

    try:
        print(f"\nCutting {len(segments)} segments...")
        for i, (start, end) in enumerate(segments):
            segment_file = os.path.join(temp_dir, f"seg_{i:04d}.mp4")
            segment_files.append(segment_file)

            cmd = [
                "npx", "remotion", "ffmpeg",
                "-ss", str(start),
                "-i", video_path,
                "-t", str(end - start),
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "18",
                "-c:a", "aac",
                "-avoid_negative_ts", "make_zero",
                "-y",
                segment_file
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=REMOTION_DIR)
            if result.returncode != 0:
                print(f"  Error cutting segment {i+1}")
                return None
            print(f"  [{i+1}/{len(segments)}] {start:.2f}s -> {end:.2f}s")

        # Create concat list
        concat_list = os.path.join(temp_dir, "list.txt")
        with open(concat_list, 'w') as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")

        print("Concatenating...")

        concat_cmd = [
            "npx", "remotion", "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list,
            "-c", "copy",
            "-y",
            output_path
        ]

        result = subprocess.run(concat_cmd, capture_output=True, text=True, cwd=REMOTION_DIR)
        if result.returncode != 0:
            print(f"Error concatenating: {result.stderr[:200]}")
            return None

        # Get new duration
        new_info = get_video_info(output_path)
        return new_info['duration'] if new_info else total_speech

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Transcribe, trim, and organize video")
    parser.add_argument("video", help="Video file path or URL")
    parser.add_argument("--title", required=True, help="Title for the video")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Base output directory")
    parser.add_argument("--no-trim", action="store_true", help="Skip dead space trimming")

    args = parser.parse_args()

    # Create slugified folder name
    folder_name = slugify(args.title)
    project_dir = os.path.join(args.output, folder_name)
    os.makedirs(project_dir, exist_ok=True)

    print(f"Project folder: {project_dir}")

    # Get video file
    if is_url(args.video):
        # Download from URL
        temp_dir = "/tmp/video_download"
        os.makedirs(temp_dir, exist_ok=True)
        video_path = download_video(args.video, temp_dir)
        if not video_path:
            print("ERROR: Failed to download video")
            sys.exit(1)
    else:
        video_path = args.video
        if not os.path.exists(video_path):
            print(f"ERROR: Video file not found: {video_path}")
            sys.exit(1)

    # Get video info
    video_info = get_video_info(video_path)

    # Determine output video extension
    ext = os.path.splitext(video_path)[1].lower()
    if not ext:
        ext = ".mp4"

    # Copy/move video to project folder
    final_video_path = os.path.join(project_dir, f"{folder_name}{ext}")
    print(f"Copying video to {final_video_path}")
    shutil.copy2(video_path, final_video_path)

    # Extract audio
    audio_path = "/tmp/transcribe_audio.wav"
    if not extract_audio(final_video_path, audio_path):
        print("ERROR: Failed to extract audio")
        sys.exit(1)

    # Transcribe
    json_path = os.path.join(project_dir, f"{folder_name}-transcript.json")
    if not transcribe_audio(audio_path, json_path):
        print("ERROR: Failed to transcribe")
        sys.exit(1)

    # Create readable transcript
    txt_path = os.path.join(project_dir, f"{folder_name}-transcript.txt")
    transcript_lines = create_transcript_txt(json_path, txt_path, args.title, video_info)

    # Keep JSON for video cutting (has precise timestamps)
    # Rename to indicate it's for editing
    edit_json_path = os.path.join(project_dir, f"{folder_name}-timestamps.json")
    if os.path.exists(json_path):
        shutil.move(json_path, edit_json_path)
        print(f"Timestamps saved: {edit_json_path}")

    # Clean up temp files
    if os.path.exists(audio_path):
        os.remove(audio_path)

    # Trim dead space (unless --no-trim)
    trimmed_path = None
    if not args.no_trim:
        print("\n" + "-" * 50)
        print("TRIMMING DEAD SPACE")
        print("-" * 50)

        base, ext = os.path.splitext(final_video_path)
        trimmed_path = f"{base}-trimmed{ext}"

        new_duration = trim_dead_space(final_video_path, trimmed_path, video_info)

        if new_duration:
            saved = video_info['duration'] - new_duration
            print(f"\nOriginal: {video_info['duration']:.1f}s")
            print(f"Trimmed: {new_duration:.1f}s")
            print(f"Removed: {saved:.1f}s ({saved/video_info['duration']*100:.0f}%)")
        else:
            print("Warning: Trimming failed, original video preserved")
            trimmed_path = None

    print("\n" + "=" * 50)
    print("SUCCESS!")
    print("=" * 50)
    print(f"\nProject folder: {project_dir}")
    print(f"Original video: {final_video_path}")
    if trimmed_path:
        print(f"Trimmed video: {trimmed_path}")
    print(f"Transcript: {txt_path}")
    print("\nTranscript preview:")
    print("-" * 30)
    for line in transcript_lines[:15]:
        print(line)
    if len(transcript_lines) > 15:
        print("...")


if __name__ == "__main__":
    main()
