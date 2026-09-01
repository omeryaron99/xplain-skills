---
name: youtube-competitor-analysis
description: Scrape YouTube competitor channels, detect outlier videos, grab first-30s transcripts, and sync to Supabase + Airtable. Use when analyzing competitor YouTube packaging, titles, or thumbnails.
---

# YouTube Competitor Analysis

Scrape YouTube competitors from Airtable, pull all their videos via YouTube Data API v3, detect outlier videos (2x+ channel average views), grab the first 30 seconds of transcripts, and sync everything to Supabase + Airtable.

---

## When to Use

- Scouting YouTube competitor packaging (thumbnails, titles, hooks)
- Running a daily or weekly competitor video sync
- Looking for outlier videos to study what's working
- Backfilling a new competitor's full video history

## Data Flow

```
Airtable YouTube Competitors → YouTube Data API v3 → YouTube Captions (free) / Apify (fallback) →
Supabase competitor_videos + Airtable Competitor Videos
```

## Storage IDs

Read these from your project's `CLAUDE.md`:

| Store | Table | ID |
|-------|-------|----|
| Airtable | YouTube Competitors | `tblXXXXXXXXXXXXX` |
| Airtable | Competitor Videos | `tblXXXXXXXXXXXXX` |
| Supabase | competitor_videos | (your Supabase project) |
| Airtable Base | Content System | `appXXXXXXXXXXXXX` |

## Process

### Default: Daily Scrape (all competitors, last 50 videos each)

```bash
python3 scripts/pull_yt_competitors.py
```

### Single Channel

```bash
python3 scripts/pull_yt_competitors.py --channel "Channel Name"
```

### Full Backfill (all videos, all competitors)

```bash
python3 scripts/pull_yt_competitors.py --backfill
```

### Fast Run (skip transcripts)

```bash
python3 scripts/pull_yt_competitors.py --no-captions
```

### Flags can combine

```bash
python3 scripts/pull_yt_competitors.py --channel "Channel Name" --backfill
```

## What It Outputs

For each competitor:
1. Resolves channel URL to channel ID + uploads playlist
2. Pulls video details (title, description, thumbnail, views, likes, comments, duration)
3. Calculates outlier score (views / channel average)
4. Flags outliers (2x+ average)
5. Grabs first 30s transcript for outliers (free library first, Apify fallback at $0.005/video)
6. Upserts to Supabase `competitor_videos` table
7. Upserts to Airtable `Competitor Videos` table

## After Running

Present a summary table of outliers found, sorted by outlier score. Example:

| Channel | Title | Views | Outlier Score | Hook (first 30s) |
|---------|-------|-------|---------------|-------------------|

Then ask if the user wants to:
- Analyze the outlier titles/hooks for patterns
- Compare against their own content
- Add more competitors to the YouTube Competitors table

## Querying Outliers (Supabase)

```sql
SELECT channel, title, views, outlier_score, hook_first_30s
FROM competitor_videos
WHERE is_outlier = true
ORDER BY outlier_score DESC;
```

## Requirements

In `.env`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_ACCESS_TOKEN`, `GOOGLE_REFRESH_TOKEN`, `AIRTABLE_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `APIFY_API_TOKEN`

Python: `requests`, `youtube-transcript-api`
