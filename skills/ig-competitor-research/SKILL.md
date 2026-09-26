---
name: ig-competitor-research
description: Instagram competitor research that tells you what to post. Scrapes the last week of posts from your competitor list through Apify, ranks them by likes and breakout score (likes divided by that creator's median), fans out one sub-agent per winning reel or carousel to pull the hook, format, transcript, visual breakdown and why it worked, then builds one HTML report with a version adapted to you for every pick. Use when the user says "competitor research", "IG competitor research", "מחקר מתחרים", "מה עובד בנישה", "what's working in my niche", "what should I post this week", "viral research", or passes a list of Instagram handles to research.
---

# IG Competitor Research

One command, one report: the posts that won in your niche this week, each with its
hook, breakout score, likes, comments and views, format, a breakdown, the full
transcript, why it worked, and a version of the hook written for you.

The only paid step is the Apify scrape. Frames come from ffmpeg and transcripts
from a local Whisper, so everything after the scrape is free.

```
SK=~/.claude/skills/ig-competitor-research
S=$SK/scripts
```

## First run: interview them, do not hand them a manual

**If `$SK/config.json` or `$SK/.env` does not exist yet, this is a setup, not a
research run.** Read `setup/INTERVIEW.md` and run it: one question at a time, in
the user's language. It gets the Apify token in safely, writes their creator
profile and their competitor list, and runs the first report with them. Do not
paraphrase the setup from this file instead.

## Every run after that

Read `$SK/config.json` first. It holds `creator` (who the report adapts hooks
for), `language` (the language of those hooks), `output_dir`, and the ranking
defaults.

`RUN="<output_dir>/YYYY-MM-DD ig-research"` (expand `~`). If that folder exists
already, append ` HHMM`.

### Phase 1: scrape (the one paid step)

1. Handles: if the user passed handles in the message, use those
   (`--handles a,b,c`). Otherwise the script reads `$SK/competitors.md`, section
   `## Instagram` (another section with `--section "<name>"`, e.g. for a client).
   If the list is empty, ask the user for 5 to 8 handles and add them to the file.
   **Never invent handles.**
2. `python3 $S/scrape.py --run-dir "$RUN"` (or `--handles ...`). It fires
   `apify/instagram-scraper` once for all handles (20 posts each: the extra
   history is the breakout baseline), polls, and writes `dataset.json` +
   `scrape.json` with the run cost.
   - `NO_TOKEN`: `$SK/.env` has no `APIFY_TOKEN=`. Run the interview's token step.
   - A handle under "NO POSTS" is private, renamed or mistyped: report it, carry on.
   - Re-running on the same data costs nothing: `--dataset-id <id>` from `scrape.json`.

### Phase 2: rank and select (free)

`python3 $S/rank_and_select.py "$RUN" --days <days> --per-creator <per_creator> --top <top> --rank-by <rank_by>`
with the values from `config.json` (defaults 7, 3, 15, likes).

Only posts from the window are eligible; each creator contributes at most
`per_creator`; the pool is re-ranked and capped at `top`. `--rank-by breakout`
surfaces small accounts that popped, which is usually the better topic signal;
use it when the user asks for "outliers" or when one huge account takes every
slot. Print the ranked table to the chat.

### Phase 3: media prep (free, local)

`python3 $S/prep_media.py "$RUN"` (add `--cookies-browser <browser>` only if
`config.json` sets `cookies_browser`). It downloads every pick in parallel, grabs
4 keyframes per reel (hook at 0.4 s, then 30%, 55%, 85%) or every carousel slide,
and transcribes reels with whichever local Whisper is installed. Run it in the
background and wait for it. A job with `"ok": false` in `prep.json` still gets
analysed from its caption and whatever frames exist.

### Phase 4: one sub-agent per pick (parallel)

Spawn every pick in ONE message, all in parallel, `subagent_type: general-purpose`,
`model: sonnet`, description `Break down #N @handle`. Prompt, filled per job:

> You are breaking down one Instagram {kind} by @{handle} for a competitor-research report. Job folder: `{RUN}/jobs/{job}/`.
> Read `post.json` (stats + caption), `prep.json`, `transcript.txt` and `transcript.json` if present (segment timestamps show what is said in the first 3 seconds), and LOOK at every `frame_*.jpg` / `slide_*.jpg` with the Read tool. Do not download anything.
> Write `analysis.json` in that folder, UTF-8, exactly these keys:
> - `hook_spoken`: the first spoken sentence, verbatim in its original language ("" if none)
> - `hook_text`: on-screen text in the first frame / cover slide, verbatim ("" if none)
> - `hook_type`: "spoken + text", "spoken", "text only" or "visual"
> - `format`: 2 to 4 word label, reuse these when they fit: Talking Head Listicle, Talking Head Story, Green Screen Explainer, Screen Recording Tutorial, Split Screen Demo, Skit, Text-on-Video Meme, Carousel Listicle, Carousel Tweet Screenshot, Carousel Infographic, Before/After
> - `topic`: one short phrase
> - `breakdown`: 1 to 2 sentences on the structure and visuals (what happens, how it is shot and edited)
> - `cta`: the call to action, e.g. `comment "TOOLS" for the list` ("" if none)
> - `why_it_worked`: 1 to 2 sentences naming the mechanism (curiosity gap, specific-number proof, job-replacement shock, comment-to-DM lead magnet, authority drop, etc.)
> - `your_version`: a hook in {language} for this creator: "{creator}". Reuse the same mechanism on their own angle. Natural spoken language, 15 words at most, no invented numbers or results.
> - `slide_text` (carousels only): the text of every slide, in order, one line each
> Reply with one line: `OK #{rank}` or `FAIL #{rank}: reason`.

When all return, check every job has `analysis.json`; re-run a failed one once,
then move on.

### Phase 5: pattern and report

1. Read all `analysis.json` files (not the frames) and write `$RUN/pattern.txt`:
   one or two short paragraphs of cross-pick synthesis. Which engine keeps
   repeating (CTA type, hook archetypes, topics, formats), which picks broke out
   hardest and why, and what is missing that this creator could own. Concrete:
   cite handles and numbers.
2. Write `$RUN/ideas.json`: 5 video ideas,
   `[{"hook": "...", "format": "...", "based_on": 3}]`, hooks in `language`
   under the same rules as `your_version`.
3. `python3 $S/build_report.py "$RUN"` builds `report.html` (self-contained,
   images embedded) and prints a markdown leaderboard.
4. Open the report for them (`open "$RUN/report.html"` on a Mac).
5. In chat: the leaderboard, the pattern paragraph, the 5 ideas, the Apify cost
   from `scrape.json`, and any flags (dead handles, failed downloads, thin
   baselines).

## Follow-ups they may ask for

- "Write me scripts from this": the report's transcripts are the research
  context, so ideas start from what already won in the niche instead of a blank
  page.
- "Run it for a client": add a `## <Client>` section to `competitors.md`, then
  `--section "<Client>"`.
- Weekly on autopilot: schedule a Monday-morning run.

## Traps

- **Breakout** is likes divided by the creator's median over their last ~20
  non-pinned posts. Under 5 baseline posts the score is noisy;
  `rank_and_select.py` flags it.
- Likes can be hidden (Apify returns -1, treated as 0). Carousels have no views,
  which is why the default rank is likes, not views.
- Ranking by likes can crown a **sponsored post**. Say so in the pattern when the
  #1 is under 1x its creator's median.
- Collab posts come back with the co-author in `ownerUsername`;
  `rank_and_select.py` credits them to the scraped profile and records
  `collab_with`.
- Some Apify `videoUrl`s are the video-only track (no sound, so no transcript),
  and Apify's media links expire after a few days. `prep_media.py` falls back to
  `yt-dlp` for both, which for Instagram usually needs `--cookies-browser`.
- Music-only reels come back with `music_only: true` and an empty transcript; the
  hook then lives in `hook_text`.
- The report is research, not content to copy. Adapt the mechanism, never the
  words.

Built by Xplain ([explain.co.il](https://explain.co.il)), after an idea by Jason
Cooperson. MIT.
