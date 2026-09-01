---
name: video-analyzer
description: Analyze videos using Gemini — break down hooks, structure, pacing, CTAs, and content strategy. Accepts a URL or local file path. Use when asked to watch, analyze, or break down any video.
---

# Video Analyzer

Analyze any video using Gemini's video understanding. Break down content strategy, hooks, structure, pacing, and performance patterns.

---

## Input Handling

**URL provided:** Download first using /video-downloader, then analyze the local file.

**Local file provided:** Analyze directly.

## Analysis Workflow

### Step 1: Get the Video File

If input is a URL:
1. Invoke the video-downloader skill to download locally
2. Note the output file path

If input is a local path:
1. Verify file exists

### Step 2: Upload to Gemini

Upload the video file to Gemini's File API:

```bash
# Upload video file
curl -s -X POST "https://generativelanguage.googleapis.com/upload/v1beta/files?key=${GEMINI_API_KEY}" \
  -H "X-Goog-Upload-Command: start, upload, finalize" \
  -H "X-Goog-Upload-Header-Content-Type: video/mp4" \
  -H "Content-Type: video/mp4" \
  --data-binary "@${VIDEO_PATH}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['file']['uri'])"
```

Store the returned file URI for the analysis prompt.

**Wait for processing:** Gemini needs time to process video. Check status:

```bash
# Poll until state is ACTIVE (check every 5 seconds, max 60 seconds)
FILE_NAME=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['file']['name'])")
for i in $(seq 1 12); do
  STATUS=$(curl -s "https://generativelanguage.googleapis.com/v1beta/${FILE_NAME}?key=${GEMINI_API_KEY}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('state','ACTIVE'))")
  [ "$STATUS" = "ACTIVE" ] && break
  sleep 5
done
```

### Step 3: Analyze with Gemini

Send the video to Gemini with an analysis prompt. Adjust the prompt based on what the user wants:

```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "contents": [{
      "parts": [
        {"fileData": {"mimeType": "video/mp4", "fileUri": "'"${FILE_URI}"'"}},
        {"text": "'"${ANALYSIS_PROMPT}"'"}
      ]
    }]
  }'
```

### Step 4: Present Results

Format Gemini's response into a structured breakdown for the user.

---

## Analysis Prompts by Use Case

### Content Breakdown (default)
```
Watch this video and provide a detailed content breakdown:
1. HOOK (first 1-3 seconds): What's the opening hook? How does it grab attention?
2. STRUCTURE: What's the content structure? (problem-solution, listicle, story, tutorial, etc.)
3. PACING: How does the pacing flow? Where are the retention peaks/drops?
4. VISUAL FORMAT: What visual style is used? (talking head, b-roll, text overlay, split screen, etc.)
5. CTA: What's the call to action? Where is it placed?
6. AUDIO: Music, sound effects, voiceover style?
7. ESTIMATED DURATION: How long is the video?
8. KEY TAKEAWAY: What makes this video effective or ineffective?
```

### Competitor Research
```
Analyze this video as a competitor analysis:
1. HOOK TECHNIQUE: What hook pattern does the creator use?
2. CONTENT ANGLE: What unique angle or perspective do they bring?
3. AUDIENCE TARGETING: Who is this video for? What pain point does it address?
4. PRODUCTION QUALITY: Rate the production (lighting, audio, editing) 1-10
5. ENGAGEMENT DRIVERS: What would make someone comment, share, or save this?
6. REPLICABLE ELEMENTS: What patterns could be adapted for similar content?
7. WEAKNESSES: Where could this content be improved?
```

### Transcription + Strategy
```
Watch this video and provide:
1. FULL TRANSCRIPT: Word-for-word transcription with timestamps
2. STRATEGIC ANALYSIS: What content strategy is this video executing?
3. TOPIC CATEGORY: What niche/category does this fall into?
4. VIRAL POTENTIAL: What elements could make this spread? What's missing?
```

---

## API Key

The Gemini API key should be available as `GEMINI_API_KEY` environment variable. Check `~/.zshrc` or `~/.bashrc` for the key, or ask the user to provide it.

---

## Output Format

Always structure the output with clear headers matching the analysis type. Include timestamps where relevant. End with actionable takeaways — what can the user learn or apply from this video.
