#!/usr/bin/env python3
"""Phase 3: download every pick, pull keyframes, transcribe. All local, all free.

For each jobs/NN-*/ folder:
  reel      media.mp4 -> frame_1..4.jpg (hook, 30%, 55%, 85%) -> audio.wav ->
            local Whisper -> transcript.txt + transcript.json
  carousel  slide_01..10.jpg
  image     slide_01.jpg
Writes prep.json per job ({ok, error, language, ...}). Safe to re-run: finished
steps are skipped.

Transcription uses whichever local Whisper is installed, in this order:
mlx_whisper (fast on Apple Silicon), faster_whisper, openai-whisper. With none
of them the reels are still analysed from their frames and caption, just
without a transcript.

  prep_media.py RUN_DIR [--workers 6] [--cookies-browser chrome]
"""
import argparse, glob, json, os, shutil, subprocess, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")
YTDLP = shutil.which("yt-dlp")          # optional: only the fallback download needs it
COOKIES_BROWSER = ""                    # set from --cookies-browser
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


def fetch(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return True
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": "https://www.instagram.com/"})
        with urllib.request.urlopen(req, timeout=90) as r, open(dest + ".part", "wb") as f:
            shutil.copyfileobj(r, f)
        os.replace(dest + ".part", dest)
        return os.path.getsize(dest) > 1000
    except Exception:
        return False


def ytdlp(post_url, dest):
    """CDN links from Apify expire after a few days; fall back to yt-dlp.

    Instagram usually wants a logged-in session, which yt-dlp borrows from a
    browser with --cookies-from-browser. That is opt-in (--cookies-browser),
    because reading browser cookies is the user's call, not ours.
    """
    if not YTDLP:
        return False
    cmd = [YTDLP, "-f", "mp4/best", "-o", dest, "--no-part", "-q", post_url]
    if COOKIES_BROWSER:
        cmd[1:1] = ["--cookies-from-browser", COOKIES_BROWSER]
    try:
        return subprocess.run(cmd, capture_output=True, timeout=300).returncode == 0 and os.path.exists(dest)
    except Exception:
        return False


def ff(*args):
    return subprocess.run([FFMPEG, "-loglevel", "error", "-y", *args], capture_output=True).returncode == 0


def duration(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


def has_audio(path):
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return bool(out)


def download(job):
    d = job["dir"]; p = job["post"]; st = job["state"]
    if p["kind"] == "reel":
        mp4 = os.path.join(d, "media.mp4")
        ok = (p.get("video_url") and fetch(p["video_url"], mp4)) or ytdlp(p["url"], mp4)
        if not ok:
            st["error"] = "video download failed (CDN expired and yt-dlp fallback failed)"
            return
        if not has_audio(mp4):
            # some Apify videoUrls are the video-only DASH track; yt-dlp returns the muxed file
            alt = os.path.join(d, "media_yt.mp4")
            if ytdlp(p["url"], alt) and has_audio(alt):
                os.replace(alt, mp4)
            elif os.path.exists(alt):
                os.remove(alt)
        dur = duration(mp4) or float(p.get("duration") or 0)
        st["duration"] = round(dur, 1)
        for n, frac in enumerate((0.0, 0.30, 0.55, 0.85), 1):
            t = 0.4 if frac == 0 else dur * frac
            out = os.path.join(d, f"frame_{n}.jpg")
            if not os.path.exists(out):
                ff("-ss", f"{t:.2f}", "-i", mp4, "-frames:v", "1", "-vf", "scale=540:-2", "-q:v", "4", out)
        if has_audio(mp4):
            wav = os.path.join(d, "audio.wav")
            if not os.path.exists(wav):
                ff("-i", mp4, "-vn", "-ac", "1", "-ar", "16000", wav)
        else:
            st["no_audio"] = True
    else:
        urls = p.get("slide_urls") or [p.get("display_url")]
        got = 0
        for n, u in enumerate([u for u in urls if u], 1):
            raw = os.path.join(d, f"slide_{n:02d}.src")
            out = os.path.join(d, f"slide_{n:02d}.jpg")
            if os.path.exists(out) or (fetch(u, raw) and ff("-i", raw, "-vf", "scale=720:-2", "-q:v", "4", out)):
                got += 1
            if os.path.exists(raw):
                os.remove(raw)
        st["slides"] = got
        if not got:
            st["error"] = "no slide images downloaded"


def whisper_engine():
    """Returns (name, fn) where fn(wav) -> {"language", "segments": [{start, end, text, no_speech_prob}]}."""
    try:
        import mlx_whisper
        return "mlx_whisper", lambda wav: mlx_whisper.transcribe(
            wav, path_or_hf_repo="mlx-community/whisper-large-v3-turbo", condition_on_previous_text=False)
    except ImportError:
        pass
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("large-v3-turbo", compute_type="int8")

        def run(wav):
            segs, info = model.transcribe(wav, condition_on_previous_text=False)
            return {"language": info.language,
                    "segments": [{"start": x.start, "end": x.end, "text": x.text,
                                  "no_speech_prob": x.no_speech_prob} for x in segs]}
        return "faster_whisper", run
    except ImportError:
        pass
    try:
        import whisper
        model = whisper.load_model("turbo")
        return "openai-whisper", lambda wav: model.transcribe(wav, condition_on_previous_text=False)
    except ImportError:
        return None, None


def transcribe(jobs):
    todo = [j for j in jobs if os.path.exists(os.path.join(j["dir"], "audio.wav"))
            and not os.path.exists(os.path.join(j["dir"], "transcript.json"))]
    if not todo:
        return
    name, engine = whisper_engine()
    if not engine:
        print("  no local Whisper installed: reels are analysed without transcripts", flush=True)
        for j in todo:
            j["state"]["no_transcript"] = "no local Whisper installed"
        return
    print(f"  transcribing {len(todo)} reels with {name} ...", flush=True)
    for j in todo:
        wav = os.path.join(j["dir"], "audio.wav")
        try:
            r = engine(wav)
        except Exception as e:
            j["state"]["error"] = f"whisper failed: {e}"
            continue
        segs = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip(),
                 "no_speech": round(s.get("no_speech_prob", 0), 2)} for s in r.get("segments", [])]
        speech = [s for s in segs if s["no_speech"] < 0.6]
        text = " ".join(s["text"] for s in speech).strip()
        json.dump({"language": r.get("language"), "segments": segs}, open(
            os.path.join(j["dir"], "transcript.json"), "w"), ensure_ascii=False, indent=1)
        open(os.path.join(j["dir"], "transcript.txt"), "w").write(text)
        j["state"]["language"] = r.get("language")
        if len(text.split()) < 4:
            j["state"]["music_only"] = True
        print(f"  transcribed {os.path.basename(j['dir'])} [{r.get('language')}] {len(text.split())} words", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--cookies-browser", default="",
                    help="let yt-dlp borrow this browser's Instagram login for the fallback download (chrome, safari, firefox...)")
    a = ap.parse_args()
    global COOKIES_BROWSER
    COOKIES_BROWSER = a.cookies_browser
    if not FFMPEG or not FFPROBE:
        sys.exit("NO_FFMPEG: install ffmpeg first (Mac: brew install ffmpeg)")

    jobs = []
    for d in sorted(glob.glob(os.path.join(a.run_dir, "jobs", "*"))):
        post = json.load(open(os.path.join(d, "post.json")))
        jobs.append({"dir": d, "post": post, "state": {"job": os.path.basename(d), "kind": post["kind"]}})
    print(f"downloading {len(jobs)} posts ...", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(download, jobs))
    transcribe(jobs)

    bad = 0
    for j in jobs:
        j["state"]["ok"] = "error" not in j["state"]
        bad += not j["state"]["ok"]
        json.dump(j["state"], open(os.path.join(j["dir"], "prep.json"), "w"), indent=1)
        wav = os.path.join(j["dir"], "audio.wav")
        if os.path.exists(wav) and os.path.exists(os.path.join(j["dir"], "transcript.json")):
            os.remove(wav)
    print(f"prep done: {len(jobs) - bad} ok, {bad} failed")
    for j in jobs:
        if not j["state"]["ok"]:
            print(f"  ! {j['state']['job']}: {j['state']['error']}")


if __name__ == "__main__":
    main()
