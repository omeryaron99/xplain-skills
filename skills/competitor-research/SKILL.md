---
name: competitor-research
description: Build a complete competitor database from scratch. Researches competitors in any niche via web search, finds their Facebook Pages, scrapes Ad Library page IDs via Apify, and populates an Airtable table with logos, social handles, descriptions, and working Ad Library links. Works for any industry.
---

# Competitor Research — Full Pipeline

You are a competitive intelligence researcher. Given a niche/industry, you build a complete competitor database in Airtable with verified Facebook Ad Library links, logos, and social profiles.

**What you produce:** A ready-to-use Airtable table with 10+ competitors, each with working Meta Ad Library URLs, Facebook Page IDs, logos, social handles, and descriptions.

---

## Prerequisites

The user needs:
1. **Airtable PAT** — in `.mcp.json` under an `airtable-*` server, or in `.env` as `AIRTABLE_API_KEY`
2. **Apify token** — in `.mcp.json` under an `apify-*` server, or in `.env` as `APIFY_TOKEN`
3. **An Airtable base ID** — the base where the Competitors table will be created

If any are missing, tell the user what's needed and stop.

---

## Step 1: Gather Context

Ask the user (skip any they already provided):

1. **What's your niche/industry?** (e.g., "sports coaching SaaS", "DTC skincare", "restaurant tech")
2. **Who are your top 2-3 known competitors?** (seed list to start research)
3. **Airtable Base ID** — which base to create the table in
4. **How many competitors?** (default: 10 — suggest 5 micro-niche + 3 macro-niche + 2 ad leaders)

**Category definitions:**
- **Micro-Niche:** Direct competitors in the same narrow market
- **Macro-Niche:** Bigger players in the broader industry
- **Ad Leader:** Companies (any industry) known for excellent Meta ad creative worth studying

---

## Step 2: Create the Airtable Table

Create a new table called `Competitors` with these fields:

```
POST /meta/bases/{baseId}/tables
```

| Field | Type | Config |
|---|---|---|
| Name | singleLineText | Primary field — company/brand name |
| Logo | multipleAttachments | Company logo |
| Category | singleSelect | Choices: `Micro-Niche`, `Macro-Niche`, `Ad Leader` |
| Niche / Industry | singleLineText | What space they're in |
| Description | multilineText | 1-3 sentences: what they sell, who they sell to |
| Status | singleSelect | Choices: `Active`, `Inactive` |
| Facebook Page URL | url | **REQUIRED** — the key field for Ad Library lookups |
| Facebook Page ID | singleLineText | Ad Library page ID (NOT the profile ID) |
| Ad Library URL | url | Direct link using `view_all_page_id` |
| Website | url | Main site |
| Instagram URL | url | |
| YouTube URL | url | |
| TikTok URL | url | |
| LinkedIn URL | url | |
| Date Added | date | Format: M/D/YYYY |

Save the table ID and all field IDs from the response — you'll need them.

---

## Step 3: Research Competitors

Use the Agent tool with `subagent_type: general-purpose` to research competitors. Give the agent:
- The user's niche
- Their seed competitors
- The category breakdown (e.g., 5 micro + 3 macro + 2 ad leaders)

**For each competitor, the agent must find:**
- Company name
- What they sell and who they sell to (1-3 sentences)
- Facebook Page URL (facebook.com/pagename)
- Website URL
- Instagram URL
- YouTube, TikTok, LinkedIn URLs (if they exist)

**IMPORTANT:** Only return URLs the agent actually found. Never guess social handles.

---

## Step 4: Get Facebook Page IDs + Logos via Apify

This is the critical step. Facebook has TWO different IDs per page:
- **Profile ID** (starts with `100...`) — used internally, does NOT work in Ad Library URLs
- **Ad Library ID** (from `pageAdLibrary.id`) — this is what makes Ad Library URLs work

### Run the Apify Facebook Pages Scraper:

```
POST https://api.apify.com/v2/acts/apify~facebook-pages-scraper/run-sync-get-dataset-items
  ?token={APIFY_TOKEN}&timeout=180

Body:
{
  "startUrls": [
    {"url": "https://www.facebook.com/{slug1}/"},
    {"url": "https://www.facebook.com/{slug2}/"},
    ...
  ]
}
```

### From the response, extract THREE things per page:

```python
for item in response:
    slug = item["pageName"]
    ad_library_id = item["pageAdLibrary"]["id"]    # <-- THIS is the correct ID
    logo_url = item["profilePictureUrl"]            # <-- Logo image
    # item["pageId"] is the PROFILE ID — do NOT use for Ad Library URLs
```

### Build the Ad Library URL using the correct ID:

```
https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id={ad_library_id}
```

**Never use the profile `pageId` in Ad Library URLs — they will return empty results.**

---

## Step 5: Populate Airtable Records

Create records with all data. Airtable allows up to 10 records per POST request.

```
POST /v0/{baseId}/{tableId}
```

For each record:
- Set all text/url fields from research
- Set `Facebook Page ID` to the **Ad Library ID** (from `pageAdLibrary.id`)
- Set `Ad Library URL` using the format above
- Set `Logo` as an attachment: `[{"url": "{logo_url}", "filename": "{slug}-logo.jpg"}]`
- Set `Date Added` to today's date (YYYY-MM-DD)
- Set `Status` to `Active`

---

## Step 6: Verify

After populating, pull all records and verify:
- Total record count matches target
- Every record has a Facebook Page URL
- Every record has a Facebook Page ID (the Ad Library one)
- Every record has an Ad Library URL
- Every record has a Logo attachment
- Category breakdown matches the plan (e.g., 5/3/2)

Print a summary table showing the verification results.

---

## Key Lessons

1. **Facebook has two ID systems.** The Apify `pageId` field returns the profile/actor ID (100...). The `pageAdLibrary.id` field returns the real Ad Library ID. Only the Ad Library ID works in `view_all_page_id=` URLs.

2. **Airtable can't delete fields via API.** If you need to rebuild a table, create a new one rather than modifying the old one.

3. **Facebook CDN URLs for logos are temporary.** Airtable will download and cache the image when you create the attachment, so the CDN URL expiring later is fine.

4. **The Ad Library URL format that works:**
   ```
   https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=US&is_targeted_country=false&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id={AD_LIBRARY_ID}
   ```

5. **Graph API can't look up third-party pages** without `pages_read_engagement` or `Page Public Content Access` permissions. Use Apify instead.
