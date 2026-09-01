---
name: content-ideator
description: Pull ideas from the Content Pipeline, do deep research on each topic, generate 5 video variations from one topic, and save each picked variation as its own Airtable record. Use when developing pipeline ideas into filmable content. One topic → 5 videos.
---

# Content Ideator — Research + Video Multiplication

Pull pipeline ideas → Deep research → Generate 5 video variations per topic → Save each as its own record.

**The goal:** Turn 1 topic into 3-5 separate videos. Volume is the strategy right now.

**Your scope:** Research topics, multiply into video variations, save to pipeline
**NOT your scope:** Finding topics (that's `/daily-content-researcher`), writing scripts (that's `/content-scripter`)

---

## Step 0: Pull Pipeline

Query Airtable Content Pipeline for ALL records with status "💡 Idea".

**Airtable Details:**
- MCP: `airtable` → `list_records`
- Base: `YOUR_AIRTABLE_BASE_ID`
- Table: `YOUR_CONTENT_PIPELINE_TABLE_ID` (Content Pipeline)
- View: `Idea`

Present them as a numbered list:

```
# Content Pipeline — 💡 Ideas

| # | Title | Topic | Added |
|---|-------|-------|-------|
| 1 | [title] | [topic] | [date] |
| 2 | [title] | [topic] | [date] |
| ... | | | |

Which ideas do you want to develop? (pick numbers, or "all")
```

**STOP and wait for the user to pick.** Do not proceed until he selects.

---

## Step 1: Deep Research

**Before generating variations, read these context files:**

1. **Avatar** → `your-project/reference/avatar.md` — who the audience is
2. **Viral Content Patterns** → `your-project/reference/viral-content-patterns.md` — the 8 viral archetypes
3. **Latest Performance Analysis** → `your-project/analysis/` (most recent analysis file) — what's actually working (hook structures, formats, durations, content structures ranked by performance)

For EACH chosen idea, research the topic deeply:

### 1a: WebSearch — Current Context

Use the `WebSearch` tool to find:
- What just happened with this topic (timeline, key facts)
- Key numbers, dates, names, features
- Who's involved, what changed

Run 2-3 targeted searches:
- `"[topic] [current date]"` — latest developments
- `"[topic] explained OR breakdown OR analysis"` — deeper context
- `"[topic] controversy OR debate OR problem"` — tension points

### 1b: WebSearch — What Others Are Saying

Find what other creators and outlets are saying (so you can differentiate):
- `"[topic] creator OR youtuber OR review"` — creator takes
- `"[topic] reddit OR twitter reaction"` — community reactions

### 1c: Compile Research Brief

For each topic, compile:

```
**Key Facts:**
- [Specific dates, numbers, names, features — the hard facts]
- [What actually happened, in chronological order if relevant]

**What Everyone Else Is Saying (The Default Take):**
- [The obvious angle every creator will cover]
- [The surface-level reaction most people have]

**The Detail Nobody Is Highlighting (The Gap):**
- [The thing buried in the details that changes the story]
- [The second-order effect nobody's thinking about]

**Controversy / Debate:**
- [What people disagree about, if anything]
- [The nuance most people are missing]

**Demo-ability:**
- Can you show this? [Yes/No]
- What would the demo look like? [Specific description]
- What tools/setup needed? [List]
```

---

## Step 2: Generate 5 Video Variations

This is the volume multiplier. One topic → 5 different videos. Each variation is a different FRAMING of the same underlying research — different hook structure, different entry point, different format.

### Variation Generation Rules

**Use the performance analysis to inform variations:**
- Screen Recording dominates (64k avg views, 13 of top 20 winners)
- Talking Head works for opinion/comparison content (43k avg)
- Text Overlay is weakest (13k avg) — avoid unless proven format
- Under 45 seconds is the sweet spot (0-30 sec has 10%+ outlier rate)
- 60+ seconds has ZERO outliers across 24 videos
- Hook + Tutorial/CTA structure has highest ceiling (63k avg)
- Hook + Emotional Payoff is second best (52k avg)
- Educational/Tutorial hooks outperform Raw Shock (61k vs 32k avg)

**Mix these framing types across the 5 variations:**

| Framing | Example | Hook Structure |
|---------|---------|----------------|
| **List** | "Top 3 [things] for [topic]" / "Here are 5 [things]" | Educational/Tutorial |
| **Single Focus** | "The ONE [thing] you need for [topic]" | Secret Reveal |
| **Contrarian** | "Stop using [X], use [Y] instead" / "You're doing [X] wrong" | Contrarian/Negative |
| **Showcase** | "This [person] just [did thing] and it's insane" | Raw Shock |
| **Tutorial** | "I'm gonna teach you how to [do thing] in 30 seconds" | Educational/Tutorial |
| **Comparison** | "[X] vs [Y] — which is better?" | Comparison |
| **Emotional** | "[Tool] is ruining my life" / "[Tool] is like [relatable thing]" | Contrarian/Emotional |

**Rules:**
- Each variation must use a DIFFERENT framing type
- At least 1 must be contrarian
- At least 1 must be tutorial/educational (highest ceiling)
- Each variation should be filmable as its own standalone video
- All variations share the same research — different entry points
- Reference `your-project/reference/avatar.md` for what the audience cares about
- Reference `your-project/reference/viral-content-patterns.md` for which archetype fits

### Output Format

```
## Topic: [Title]

**Research brief:** [2-3 sentence summary of key facts]
**Default take (what everyone else will say):** [1 sentence]

---

### 1. [Video Title]
Framing: [List / Single Focus / Contrarian / Showcase / Tutorial / Comparison / Emotional]
Content Type: [Demo / Tutorial / Everything Else]
Format: [Screen Recording / Talking Head / Split-Screen]
Duration: [target seconds]
"[1-sentence description of what this video IS]"

### 2. [Video Title]
Framing: [different from above]
Content Type: [Demo / Tutorial / Everything Else]
Format: [Screen Recording / Talking Head / Split-Screen]
Duration: [target seconds]
"[1-sentence description]"

### 3. [Video Title]
Framing: [different]
Content Type: [Demo / Tutorial / Everything Else]
Format: [Screen Recording / Talking Head / Split-Screen]
Duration: [target seconds]
"[1-sentence description]"

### 4. [Video Title]
Framing: [different]
Content Type: [Demo / Tutorial / Everything Else]
Format: [Screen Recording / Talking Head / Split-Screen]
Duration: [target seconds]
"[1-sentence description]"

### 5. [Video Title]
Framing: [different]
Content Type: [Demo / Tutorial / Everything Else]
Format: [Screen Recording / Talking Head / Split-Screen]
Duration: [target seconds]
"[1-sentence description]"
```

Present all variations, then ask:

> "Pick which ones you want to make (e.g., 1, 3, 5) — or tell me to rethink any."

**STOP and wait for the user to pick.**

---

## Step 3: Save to Pipeline

After the user picks variations, create a **NEW Airtable record** for each picked variation. Do NOT update the original record — create new ones so each video has its own record.

**Airtable Details:**
- MCP: `airtable` → `create_record`
- Base: `YOUR_AIRTABLE_BASE_ID`
- Table: `YOUR_CONTENT_PIPELINE_TABLE_ID` (Content Pipeline)

**Fields per new record:**
```
Title: [Video title from the variation]
Status: "💡 Idea"
Type: "Short"
Topic: [topic/category]
Content Angle: [1-sentence description of this specific video variation]
Materials & Research: [KEEP the original research from the parent record + APPEND the deep research below it, separated by ---]
Date Created: [today's date YYYY-MM-DD]
Visual Format: [Screen Recording / Talking Head / Split Screen]
```

**CRITICAL: Materials & Research is ADDITIVE, not replacement.**
- Start with whatever was already in the original record (source URLs, initial notes, suggested angles)
- Add a `---` separator
- Then append the deep research brief below it
- NEVER delete the original content — it contains source URLs and initial context that are valuable

**Then update the ORIGINAL record** to mark it as processed:
- MCP: `airtable` → `update_records`
- Update the original pipeline record's `Content Angle` to note that variations were created: "Multiplied into [N] video variations — see individual records"

After saving, confirm and hand off:

> "Created [N] new records in your pipeline from '[original topic]'. Each is its own video. Ready to script? Run `/content-scripter` and pick which one to write."

---

## CRITICAL RULES

1. **NEVER generate generic variations.** Each variation must feel like a genuinely different video — different hook, different framing, different energy. Not the same video with slightly different words.
2. **NEVER skip research.** The research step is what makes variations informed and specific. No research = generic content.
3. **NEVER fabricate facts.** All key facts, numbers, and names must come from actual search results.
4. **The "default take" matters** — you must know what everyone else will say so you can say something DIFFERENT.
5. **Volume is the strategy.** The goal is to maximize the number of filmable videos from each topic. 1 topic should produce 3-5 separate recordings.
6. **Demo variations beat opinion variations.** If you can SHOW something instead of just talking about it, that's always better.
7. **Each variation = its own record.** Never combine multiple videos into one pipeline record.

---

## Part of Your Content Team

**Content workflow:**
```
/daily-content-researcher → Pick topics → Auto-save to Airtable pipeline
                                                    ↓
The user also adds their own ideas manually to Airtable pipeline
                                                    ↓
/content-ideator (this skill) — pulls ALL ideas from pipeline
    → Deep research on chosen topics
    → Generate 5 video variations per topic
    → User picks which to pursue
    → Creates NEW record for each picked variation
                                                    ↓
/content-scripter (reads from Airtable → 6 hooks → filming card → save)
```

**Skills:**
- `/daily-content-researcher` — Agentic morning research, live scraping, pipeline save
- `/content-analyst` — Analyze YOUR content performance
- `/competitor-analyst` — Compare vs competitors
- `/content-ideator` (this skill) — Pull pipeline ideas, deep research, multiply into video variations
- `/content-scripter` — 6 hooks, filming card, save to pipeline fields
