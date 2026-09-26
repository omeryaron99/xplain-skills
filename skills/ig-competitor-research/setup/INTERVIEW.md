# Guided setup: interview the user, then run their first report

You are setting up competitor research for someone who has not used this skill
before and does not want to read the manual. Run this as a conversation.

**Conduct the interview in whatever language the user writes to you in.**

```
SK=~/.claude/skills/ig-competitor-research
```

## The rules you do not get to break

1. **Ask one question at a time.** Wait for the answer.
2. **Nothing that costs money runs until they say yes.** The Apify scrape is the
   only paid step. Before it, say how many accounts and how many posts it will
   pull, and wait for an explicit go.
3. **Never print their Apify token back to them**, not in a message, not in a
   code block, not in a summary.
4. **The token goes into `$SK/.env` and nowhere else.** Not `config.json`, not a
   script, not a note.
5. **Never invent competitor handles.** Suggest the kind of account to look for,
   let them name the accounts.
6. **Do not report success on something you have not run.** "Works" means you ran
   it and read the output.

## 0. Check the ground before you ask anything

Run these yourself, quietly, and only raise what fails:

```bash
ls $SK/scripts/scrape.py          # skill is installed
python3 --version                 # 3.9+
ffmpeg -version | head -1         # frames and audio
yt-dlp --version                  # optional fallback downloader
python3 -c "import mlx_whisper" || python3 -c "import faster_whisper" || python3 -c "import whisper"
ls $SK/.env $SK/config.json $SK/competitors.md
```

- **No skill folder:** the zip was not unpacked into `~/.claude/skills/`. Fix it,
  then tell them to restart Claude Code, because skills load at startup.
- **No ffmpeg:** it is required. On a Mac with Homebrew: `brew install ffmpeg`.
  Ask before installing anything.
- **No Whisper at all:** the research still works, reels are then read from their
  frames and caption only. Offer to install one and say what it costs them in
  disk space first: on an Apple Silicon Mac `pip3 install mlx-whisper`,
  elsewhere `pip3 install faster-whisper`. The model downloads on first use.
- **No yt-dlp:** fine to skip. It only matters when Apify's media link has
  expired, which happens when an old run is re-processed days later.
- **`config.json` already exists:** stop and ask whether they want to change it
  or start over. Back it up first either way:
  `cp config.json config.json.bak.$(date +%s)`.

## 1. The Apify token

Explain in one sentence what Apify is: the service that reads the public posts
from Instagram for us, so nobody logs in with their own Instagram account.

Ask them to:

1. Open an account at apify.com (the free plan is enough to start).
2. Go to **Settings → API & Integrations** and copy the **Personal API token**.
3. Paste it here.

Write it without ever echoing it:

```bash
cd ~/.claude/skills/ig-competitor-research
printf 'APIFY_TOKEN=%s\n' 'THE-TOKEN' > .env
chmod 600 .env
```

Explain the chmod in one sentence: it makes the file readable only by them, and
the token can spend money on their Apify account.

Now prove the token works before building anything on top of it. This call is
read-only and free:

```bash
python3 scripts/scrape.py --check
```

If it fails, the token is wrong or was copied with a space. Fix it now, not after
the first paid run.

## 2. Who the report is for

Two questions, one at a time:

1. In one or two sentences: who are you, what do you teach or sell, and who
   watches you? (Every adapted hook in the report is written for this, so push
   gently for something specific.)
2. In which language should the adapted hooks be written?

Then:

```bash
cp config.example.json config.json
```

and fill `creator` and `language` from their answers. Leave the rest at the
defaults and tell them, in one line each, what `days`, `per_creator` and `top`
mean. Show them the finished file.

## 3. The competitor list

Ask for **5 to 8 public Instagram accounts** in their niche. Help them choose,
but do not name accounts for them:

- Accounts that post **every week**. An account that did not post in the last 7
  days contributes nothing.
- **A mix of big and small.** The big ones show what works at scale; the small
  ones that suddenly pop above their own average are often the best topic signal.
- Same audience, not necessarily the same topic. Who else does their viewer
  watch?

Write them into `competitors.md` (from `competitors.example.md`), one `- @handle`
per line under `## Instagram`, and show the file.

## 4. The first run

Say plainly before running anything paid: the scrape pulls 20 recent posts from
each of the N accounts (N × 20 results) in one Apify run, and the cost appears
in their Apify console and at the end of the run. Point them at the actor's page
on Apify for the current price. Wait for a yes.

Then run the whole thing as described in `SKILL.md`, phases 1 to 5, and narrate
it in one line per phase, not per command.

Afterwards show them:

- the leaderboard table
- the pattern paragraph
- the 5 ideas
- what the run cost (`scrape.json`)
- any handle that came back empty, and ask whether to replace it

## 5. Hand it over

Tell them, in three lines:

- To run it again, they just ask: "run the competitor research". Same list, same
  profile.
- To change the list, they edit `competitors.md` or ask you to.
- The report is research. They copy the **mechanism** of a winning post, never
  its words.

Then stop. Do not offer a schedule or more features unless they ask.
