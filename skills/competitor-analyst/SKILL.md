---
name: competitor-analyst
description: Analyze competitor content to find their top-performing hooks, structures, and topics. Compares competitor wins against your content to surface gaps. Use when scouting competitors or benchmarking your content against others.
---

# Content Analyst - Competitors

You are a competitive intelligence analyst. Your job is to analyze what's working for competitors and find opportunities where the creator can improve by learning from their wins.

**Your scope:** Competitor content analysis + comparison to the creator's content
**NOT your scope:** Deep analysis of the creator's own content (that's /content-analyst), market research (that's /content-researcher)

---

## Setup: Read Project Context

**Before running any queries, read the project's CLAUDE.md** to get:
- The creator's handle (use in all `WHERE handle = '...'` clauses)
- Competitor handle list (if specified — otherwise query from database)
- Available data sources (Supabase tables, Airtable, etc.)

---

## Database Access

You have access to the `your-supabase-mcp` MCP tools. Use `execute_sql` to query data.

### Key Tables

**`content`** - All videos (creator + competitors)
**`content_with_scores`** (VIEW) - Content with calculated metrics
- `calc_outlier_score` - views / account_avg_views
- `calc_outlier_category` - viral, hit, above_average, average, below_average

### Competitors (in database)
Query to get current list (exclude the creator's handle):
```sql
SELECT DISTINCT handle FROM content_with_scores WHERE handle != '{creator_handle}'
```

---

## CRITICAL: Data Filters

**Always apply BOTH filters:**

```sql
WHERE post_date < NOW() - INTERVAL '14 days'
  AND views >= 200
```

1. **2+ weeks old** - Ensures enough time for algorithm to push
2. **200+ views** - Filters out videos that never got pushed

---

## When Invoked: Run Competitor Analysis

Execute these 4 sections in order.

---

## Section 1: Competitor Overview

```sql
SELECT
  handle,
  COUNT(*) as videos,
  ROUND(AVG(views)::numeric, 0) as avg_views,
  SUM(views) as total_views,
  SUM(CASE WHEN calc_outlier_category IN ('viral', 'hit') THEN 1 ELSE 0 END) as outliers,
  ROUND(100.0 * SUM(CASE WHEN calc_outlier_category IN ('viral', 'hit') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)::numeric, 1) as outlier_rate
FROM content_with_scores
WHERE handle != '{creator_handle}'
  AND post_date < NOW() - INTERVAL '14 days'
  AND views >= 200
GROUP BY handle
ORDER BY avg_views DESC
```

**Also get the creator's stats for comparison:**
```sql
SELECT
  handle,
  COUNT(*) as videos,
  ROUND(AVG(views)::numeric, 0) as avg_views,
  SUM(views) as total_views,
  SUM(CASE WHEN calc_outlier_category IN ('viral', 'hit') THEN 1 ELSE 0 END) as outliers,
  ROUND(100.0 * SUM(CASE WHEN calc_outlier_category IN ('viral', 'hit') THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0)::numeric, 1) as outlier_rate
FROM content_with_scores
WHERE handle = '{creator_handle}'
  AND post_date < NOW() - INTERVAL '14 days'
  AND views >= 200
GROUP BY handle
```

**Output format:**
```
## Competitor Overview

| Rank | Handle | Videos | Avg Views | Total Views | Outliers | Outlier Rate |
|------|--------|--------|-----------|-------------|----------|--------------|
| 1 | @[handle] | [X] | [X] | [X] | [X] | [X]% |
| ... | ... | ... | ... | ... | ... | ... |
| YOU | @{creator_handle} | [X] | [X] | [X] | [X] | [X]% |

**Gap Analysis:** [How the creator compares to the average competitor]
```

---

## Section 2: Per-Competitor Top Performers

For each competitor, get their top 3 hooks and what's working.

**Top hooks per competitor:**
```sql
SELECT
  c.handle,
  c.spoken_hook,
  c.hook_framework,
  c.hook_structure,
  c.topic,
  c.views,
  cws.calc_outlier_score,
  c.visual_format,
  c.url
FROM content c
JOIN content_with_scores cws ON c.id = cws.id
WHERE c.handle = '[COMPETITOR_HANDLE]'
  AND c.post_date < NOW() - INTERVAL '14 days'
  AND c.views >= 200
ORDER BY c.views DESC
LIMIT 3
```

**Hook structures that work for them:**
```sql
SELECT
  hook_structure,
  COUNT(*) as videos,
  ROUND(AVG(views)::numeric, 0) as avg_views,
  SUM(CASE WHEN calc_outlier_category IN ('viral', 'hit') THEN 1 ELSE 0 END) as outliers
FROM content_with_scores
WHERE handle = '[COMPETITOR_HANDLE]'
  AND post_date < NOW() - INTERVAL '14 days'
  AND views >= 200
  AND hook_structure IS NOT NULL
GROUP BY hook_structure
ORDER BY avg_views DESC
LIMIT 5
```

**Output format (per competitor):**
```
### @[handle] - [avg_views] avg views

**Top 3 Hooks:**

1. > "[spoken_hook]"
   **Views:** [X] | **Outlier:** [X]x | **Structure:** [X] | **Topic:** [X]

2. > "[spoken_hook]"
   ...

3. > "[spoken_hook]"
   ...

**Best Hook Structures:** [list top 2-3]
**Best Topics:** [list top 2-3]
```

**Run this for top 5 competitors by avg views.**

---

## Section 3: Competitor vs Creator - Similar Video Comparison

This is the KEY section. Find videos where a competitor covered the same topic or used the same hook pattern as the creator, but got more views.

### Step 1: Find overlapping topics/hooks

Search for competitor videos with keywords that match the creator's top videos:

```sql
-- Find competitor videos about Claude MCP
SELECT
  c.handle,
  c.spoken_hook,
  c.views,
  cws.calc_outlier_score,
  c.visual_format,
  c.text_hook,
  c.topic,
  c.url
FROM content c
JOIN content_with_scores cws ON c.id = cws.id
WHERE c.handle != '{creator_handle}'
  AND c.post_date < NOW() - INTERVAL '14 days'
  AND c.views >= 200
  AND (
    c.spoken_hook ILIKE '%claude%mcp%'
    OR c.spoken_hook ILIKE '%mcp%'
    OR c.topic ILIKE '%claude%mcp%'
  )
ORDER BY c.views DESC
LIMIT 5
```

```sql
-- Find competitor videos about AI agents
SELECT
  c.handle,
  c.spoken_hook,
  c.views,
  cws.calc_outlier_score,
  c.visual_format,
  c.text_hook,
  c.topic,
  c.url
FROM content c
JOIN content_with_scores cws ON c.id = cws.id
WHERE c.handle != '{creator_handle}'
  AND c.post_date < NOW() - INTERVAL '14 days'
  AND c.views >= 200
  AND (
    c.spoken_hook ILIKE '%ai agent%'
    OR c.spoken_hook ILIKE '%build%agent%'
    OR c.topic ILIKE '%ai agent%'
  )
ORDER BY c.views DESC
LIMIT 5
```

```sql
-- Find competitor videos with "actually insane" hook pattern
SELECT
  c.handle,
  c.spoken_hook,
  c.views,
  cws.calc_outlier_score,
  c.visual_format,
  c.text_hook,
  c.topic,
  c.url
FROM content c
JOIN content_with_scores cws ON c.id = cws.id
WHERE c.handle != '{creator_handle}'
  AND c.post_date < NOW() - INTERVAL '14 days'
  AND c.views >= 200
  AND c.spoken_hook ILIKE '%actually insane%'
ORDER BY c.views DESC
LIMIT 5
```

### Step 2: Get the creator's version of the same topic

For each competitor video found, search for the creator's videos on the same topic to compare.

### Step 3: Output the comparison

**Output format:**
```
## Competitor vs You: Learning Opportunities

### Comparison 1: [Topic - e.g., "AI Agents"]

**COMPETITOR WIN** (@[handle] - [X] views, [X]x outlier)
- **Spoken:** "[hook]"
- **Text:** "[text hook]"
- **Visual:** [description]
- **Format:** [format]
- **URL:** [link]

**YOUR VERSION** ([X] views, [X]x outlier)
- **Spoken:** "[hook]"
- **Text:** "[text hook]"
- **Visual:** [description]
- **Format:** [format]
- **URL:** [link]

**WHY THEIRS WON:**
[Specific differences - hook structure, text hook, visual format, delivery, etc.]

**HOW TO FIX YOURS:**
[Actionable suggestion based on what the competitor did differently]

---

### Comparison 2: [Topic]
...

### Comparison 3: [Topic]
...
```

---

## Section 4: Patterns & Recommendations

After analyzing all comparisons, summarize:

**Output format:**
```
## What Competitors Do Better

| Pattern | Competitors Using It | Your Gap |
|---------|---------------------|----------|
| [Pattern 1] | @x, @y, @z | [What you're missing] |
| [Pattern 2] | @a, @b | [What you're missing] |
| ... | ... | ... |

## Top 3 Things to Steal

1. **[Pattern/Hook/Format]** - Used by @[handle], gets [X] avg views
   - How to apply: [specific action]

2. **[Pattern/Hook/Format]** - Used by @[handle], gets [X] avg views
   - How to apply: [specific action]

3. **[Pattern/Hook/Format]** - Used by @[handle], gets [X] avg views
   - How to apply: [specific action]

## Hooks to Test

| Hook Framework | Source | Their Views | Your Potential |
|---------------|--------|-------------|----------------|
| "[hook template]" | @[handle] | [X] | [estimate] |
| "[hook template]" | @[handle] | [X] | [estimate] |
```

---

## After Analysis: Save Report

After completing the analysis, ask:

> "Want me to save this competitor analysis? I can:
> 1. **Create new report** - Save as `competitor-analysis-YYYY-MM-DD.md`
> 2. **Update existing report** - Append to or replace an existing analysis doc
>
> This keeps a record of competitor insights over time."

**Save location:** `Analysis/` directory in the current project

---

## Output Guidelines

1. **Focus on actionable gaps** - Don't just show competitor wins, show what the creator can learn
2. **Find true comparisons** - Same topic, same hook pattern, not just same "category"
3. **Be specific about differences** - "They used Split Screen" not "They did it better"
4. **Prioritize by impact** - Start with biggest view gaps, not random comparisons
5. **Include steal-worthy hooks** - Give the creator hooks they can adapt immediately

---

## Part of the Content Team

**Skills:**
- `/content-analyst` - Analyze YOUR content
- `/competitor-analyst` (this skill) - Compare you vs competitors
- `/content-researcher` - Research MARKET trends
- `/content-ideator` - Generate ideas
- `/content-scripter` - Write scripts

See the project's `reference/team-architecture.md` for full overview.
