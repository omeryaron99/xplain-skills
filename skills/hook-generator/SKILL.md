---
name: hook-generator
description: Generate 6 proven video hooks from your performance data and Kallaway's database, adapted to any topic. Use when brainstorming hooks, picking angles, or starting a video idea. For full scripts, use /content-scripter instead.
---

# Hook Generator

Pull 6 data-backed hooks for any video topic — 3 from your top-performing content, 3 from Kallaway's proven frameworks — adapted and ready to film.

---

## Before Generating — Mandatory Reads

Read ALL of these before writing anything:

1. **`references/framework.md`** — Kallaway hook formula, 3-beat rule, validation checklist
2. **`references/01-hooks-key-points.md`** — 3-step hook formula, visual hooks, speed to value
3. **`references/02-hook-mistakes-key-points.md`** — Delay, confusion, irrelevance, disinterest
4. **Project voice guide** — Speech patterns, language rules (path from project CLAUDE.md)

---

## Step 1: Extract Topic Keywords

From the user's topic description, extract 3-6 search keywords to query both databases. Think broadly:
- The tool/product name (e.g., "claude code", "meta ads")
- The outcome (e.g., "leads", "optimize", "automate")
- The domain (e.g., "ad", "campaign", "crm", "client")
- Adjacent concepts (e.g., "marketing", "business", "money")

---

## Step 2: Pull Hooks from Databases

**Supabase project:** `YOUR_SUPABASE_PROJECT_ID`

### Query 1 — Your top hooks relevant to this topic

```sql
SELECT spoken_hook, spoken_hook_framework, spoken_hook_structure, views, url
FROM content
WHERE handle = 'YOUR_HANDLE'
  AND platform = 'instagram'
  AND spoken_hook IS NOT NULL
  AND views > 20000
  AND (LOWER(caption) LIKE '%[keyword1]%' OR LOWER(spoken_hook) LIKE '%[keyword1]%'
       OR LOWER(caption) LIKE '%[keyword2]%' OR LOWER(spoken_hook) LIKE '%[keyword2]%'
       OR LOWER(caption) LIKE '%[keyword3]%' OR LOWER(spoken_hook) LIKE '%[keyword3]%')
ORDER BY views DESC
LIMIT 10
```

**If < 5 results**, run a fallback for overall top performers:

```sql
SELECT spoken_hook, spoken_hook_framework, spoken_hook_structure, views, url
FROM content
WHERE handle = 'YOUR_HANDLE'
  AND platform = 'instagram'
  AND spoken_hook IS NOT NULL
  AND views > 50000
ORDER BY views DESC
LIMIT 15
```

### Query 2 — Kallaway hooks relevant to this topic

```sql
SELECT spoken_hook, spoken_hook_framework, spoken_hook_structure, views, niche
FROM kallaway_hooks
WHERE spoken_hook IS NOT NULL
  AND (LOWER(spoken_hook) LIKE '%[keyword1]%' OR LOWER(spoken_hook) LIKE '%[keyword2]%'
       OR LOWER(spoken_hook) LIKE '%[keyword3]%' OR niche IN ('Tech', 'Content Marketing'))
ORDER BY views DESC
LIMIT 15
```

Run both queries in parallel.

---

## Step 3: Select & Adapt

From the query results, pick **3 from your data** and **3 from Kallaway** that:

1. **Actually fit this topic** — the framework must naturally work for the content angle. Don't force it.
2. **Cover different structures** — mix Educational, Shock, FOMO, Contrarian, Fortuneteller, Comparison, etc. Never present 6 hooks that sound the same.
3. **Adapt the framework** — swap the [X] [Y] [Z] variables for the current topic. Keep the rhythm and structure identical to the proven original.

---

## Step 4: Present

Use this exact format:

```
## 6 Hook Options for: [Topic]

### From Your Data (proven on your account)

**A)** [views] views — [structure type]
   Framework: "[original framework with [X] [Y] placeholders]"
   Adapted: "[hook adapted for this topic]"
   Text Hook: "[3-7 word on-screen text — adds context spoken hook doesn't]"
   Source: [url]

**B)** ...
**C)** ...

### From Kallaway Database (proven frameworks across niches)

**D)** [views] views — [structure type]
   Framework: "[original framework]"
   Adapted: "[hook adapted for this topic]"
   Text Hook: "[3-7 word on-screen text]"

**E)** ...
**F)** ...

Pick one or more, edit them, or mash them up. Want a full filming card? Run /content-scripter.
```

---

## Hook Rules (Non-Negotiable)

- **Under 15 words** — shorter = more views
- **Topic clarity in first 2 seconds** — viewer must know what the video is about immediately
- **SPECIFIC tool/product + SPECIFIC outcome in first 3 seconds** — no vague hooks
- **Text hook adds context the spoken hook doesn't** — never repeat the spoken hook as text
- **Text hook: 3-7 words** — hyperbolic words that win: "Unlimited", "Dead", "Replacing", "Infinite", "Insane", "Cooked"
- **NO question hooks** (0% outlier rate from data)
- **NO raw shock without payoff** (0% outlier rate)
- **NO secret reveal structure** (0% outlier rate)
- **Use your actual speech patterns** from your voice guide

---

## Iteration

- **"More options"** — Pull 6 more from both databases, different structures
- **"More aggressive"** — Lean into Shock, FOMO, Contrarian structures
- **"Softer"** — Lean into Educational, Fortuneteller structures
- **"For YouTube"** — Longer hooks OK (up to 20 words), add curiosity loop
- **"Script it"** — Hand off to `/content-scripter` with the chosen hook

---

## Part of the Content Team

```
/daily-content-researcher → /content-ideator → /hook-generator (this skill) → /content-scripter
```
