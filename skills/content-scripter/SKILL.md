---
name: content-scripter
description: Write video scripts using proven hook patterns and structures. Handles short-form (TikTok, Reels, Shorts) and long-form (YouTube, VSLs). Reads scripting frameworks from references/ before writing. Use when scripting content for any brand or format.
---

# Content Scripter — Interactive Filming Card Generator

Take a topic → present hook options → generate a filming card the creator riffs from on camera.

**Your scope:** Topic + hook selection → filming card → save to pipeline
**NOT your scope:** Finding topics (/daily-content-researcher), generating ideas (/content-ideator)

---

## Setup

Add this to your project's CLAUDE.md:

| Key | Value |
|-----|-------|
| Airtable Base ID | YOUR_AIRTABLE_BASE_ID |
| Content Pipeline Table ID | YOUR_CONTENT_PIPELINE_TABLE_ID |
| Supabase Project | YOUR_SUPABASE_PROJECT_ID |
| Handle | YOUR_HANDLE |
| Platform | instagram |

Also requires:
- Airtable MCP connected
- Supabase MCP connected
- Reference files in `references/` folder (included with this skill)

---

## Before EVERY Session — Mandatory Reads

Read ALL of these before writing anything:

1. **`references/framework.md`** — Kallaway hook formula, 3-beat rule, validation checklist
2. **`references/01-hooks-key-points.md`** — 3-step hook formula, visual hooks, speed to value
3. **`references/02-hook-mistakes-key-points.md`** — Delay, confusion, irrelevance, disinterest
4. **`references/03-script-writing-key-points.md`** — Story flow, comprehension, speed to value
5. **`references/04-psychology-key-points.md`** — 6 checkpoints: pain, trust, plan, likability, attention, action
6. **Project voice guide** — Speech patterns, language rules, winner/loser examples (path from project CLAUDE.md)
7. **Latest Scripter Brief** — Find the most recent shortform analysis file, scroll to the `## Scripter Brief` section. Apply these data-driven rules when selecting hooks and writing filming cards.

If the project CLAUDE.md doesn't specify voice or hook files, use the defaults in `references/framework.md`.

---

## Step 0: Read Research from Pipeline

Before anything else, check if this topic has research in the Content Pipeline.

**Airtable Details:**
- MCP: `airtable` → `search_records`
- Base: `YOUR_AIRTABLE_BASE_ID`
- Table: `YOUR_CONTENT_PIPELINE_TABLE_ID` (Content Pipeline)
- Filter: Match by topic title, status "📝 Researched"

**Read these fields:**
- `Content Angle` — the chosen angle from ideation
- `Materials & Research` — full research brief (key facts, sources, demo details, what everyone else is saying, the gap)
- `Type` — content type determined during ideation (Demo, Tutorial, Everything Else)

**If research exists:** Use it to inform hook selection AND filming card details. The research brief contains specific facts, numbers, and names — use these instead of generic placeholders.

**If no research exists:** Proceed normally (the topic may have been given directly without going through the pipeline).

---

## Step 0b: Confirm Content Type

The content type should already be set during ideation. Confirm it with the user. Default types:

| Type | When | Examples |
|------|------|---------|
| **Demo** | Showcasing a tool, workflow, automation, build, or someone else's project | n8n workflows, Claude builds, app demos, split-screen showcases |
| **Tutorial** | Step-by-step teaching how to do something | Product walkthroughs, feature explanations, how-tos |
| **Everything Else** | Hot takes, reacts, news, comparisons, lists, humor | Opinions, reactions, breaking news, comparisons |

**For demos with workflows:** If n8n MCP tools are available and the topic involves a workflow, fetch the actual workflow JSON first. Extract: What triggers it? What's the input? What AI processes it? What's the output? Use these real details in the filming card.

---

## Step 1: Present 6 Hook Options (WAIT for response)

**DO NOT skip this step. Present hooks and WAIT for the user to pick one.**

### How to build hooks:

1. Query the Supabase `content` table for analyzed top performer hooks that are relevant to this topic and content type
2. Pull 6 hooks — show the **spoken hook** AND the **spoken hook framework** for each
3. Apply the creator's voice patterns from the voice guide
4. Mix: **2 contrarian hooks** + **4 best fit** (educational, raw shock, secret reveal, comparison — whatever matches)

### Supabase Query:

```sql
SELECT spoken_hook, spoken_hook_framework, spoken_hook_structure,
       handle, views, url
FROM content
WHERE spoken_hook IS NOT NULL
  AND spoken_hook != ''
  AND spoken_hook_structure IN ('[relevant structures]')
ORDER BY views DESC
LIMIT 20
```

Pick the 6 most relevant from the results. For the 2 contrarian hooks, filter for `spoken_hook_structure = 'Contrarian/Negative'`.

If not enough results from `content`, supplement from `kallaway_hooks` table.

### Performance insights to apply (from latest analysis):

- **Shorter hooks win.** Fewer words = more views. Under 15 words ideal.
- **Withhold the payoff.** "Look at this" (curiosity) beats "I just built X" (reveal). Don't front-load what the viewer will see.
- **Educational/Tutorial hooks outperform Raw Shock.** "I'm going to teach you" (61k avg) beats "This is insane" (32k avg).
- **"Teach" > "Show"** in hook language — it implies the viewer learns something.
- **Time constraints create urgency.** "in the next 30 seconds" outperformed "in the next 60 seconds" by 7.5x on the same video.

### Rules for hooks:

- Under 15 words (shorter = more views)
- Use the creator's actual speech patterns (from voice guide)
- Topic clarity in first 2 seconds — viewer must know what the video is about immediately
- SPECIFIC tool/product + SPECIFIC outcome in first 3 seconds — no vague hooks
- Withhold the payoff — create a curiosity gap, don't reveal what they'll see
- Text hook MUST add context the spoken hook doesn't — never repeat the spoken hook as text
- Text hook: 3-7 words, hyperbolic words that win: "Unlimited", "Dead", "Replacing", "Infinite", "Insane", "Cooked"
- **NO question hooks** (0% outlier rate from data)
- **NO raw shock without payoff** (0% outlier rate)
- **NO secret reveal structure** (0% outlier rate)
- Each hook uses a DIFFERENT framework/structure

### Present format:

```
## 6 Hook Options for: [Topic]
**Content Type:** [Demo / Tutorial / Everything Else]

**A)** "[Adapted hook text]"
   Framework: [spoken_hook_framework with [X] [Y] placeholders]
   Source: @[handle] — [X] views | Structure: [type]

**B)** "[Adapted hook text]"
   Framework: [spoken_hook_framework]
   Source: @[handle] — [X] views | Structure: [type]

**C)** "[Adapted hook text]"
   Framework: [spoken_hook_framework]
   Source: @[handle] — [X] views | Structure: [type]

**D)** "[Adapted hook text]"
   Framework: [spoken_hook_framework]
   Source: @[handle] — [X] views | Structure: [type]

**E) (Contrarian)** "[Adapted hook text]"
   Framework: [spoken_hook_framework]
   Source: @[handle] — [X] views | Structure: Contrarian/Negative

**F) (Contrarian)** "[Adapted hook text]"
   Framework: [spoken_hook_framework]
   Source: @[handle] — [X] views | Structure: Contrarian/Negative

**Pick one or more (e.g., A, C, E) — each becomes its own video. Or edit / write your own.**
```

**STOP HERE. Wait for user to choose before generating the filming card.**

**If the user picks multiple hooks:** Each hook becomes a separate video. Generate a filming card for EACH picked hook, then save each as its own Airtable record (duplicate the current record with the different hook/script/CTA). Same topic, same research, different videos.

---

## Step 2: Generate Filming Card

Based on the chosen hook + content type, generate a filming card in **sequential format**.

The filming card is a series of beats — each beat has a **framework** (what this beat accomplishes) and an **example sentence** (what you might say, in your voice). You riff from the example — it's a talking point, not a teleprompter.

### Card Format (All Content Types)

```
HOOK: [chosen line]

[SCREEN/ACTION direction if needed]

[Framework for this beat]
"[Example sentence in your voice]"

[SCREEN/ACTION direction if needed]

[Framework for next beat]
"[Example sentence in your voice]"

[SCREEN/ACTION direction if needed]

[Framework for next beat]
"[Example sentence in your voice]"

CLOSE: "[CTA or emotional payoff — 1 line]"
```

### Beat Frameworks by Content Type

**Demo (showcasing something):**
1. **Context** — what is this / who made it / why it matters
2. **The impressive thing** — the wow moment, the feature that makes jaws drop
3. **Proof / scale** — numbers, specifics, "and it gets crazier"
4. **Payoff** — emotional close or CTA

**Tutorial (step-by-step):**
1. **Promise** — what they'll be able to do after watching
2. **The key step** — the non-obvious thing that makes it work
3. **Result** — proof it works, what the viewer sees
4. **CTA** — where to learn more / what to do next

**Everything Else (takes, reacts, news):**
1. **Setup** — the thing that happened / the claim
2. **The twist** — the detail nobody noticed, the contrarian take
3. **Evidence** — why this matters, proof, comparison
4. **Close** — prediction, CTA, or punchline

### Filming Card Rules

- **3-4 beats max.** Under 45 seconds when spoken. If it's longer, cut a beat.
- **Framework + example sentence for each beat.** The framework tells you WHAT this beat accomplishes. The example sentence shows HOW to say it in his voice.
- **[SCREEN] directions between beats** when the visual changes (screen recording, B-roll, split-screen footage).
- **Specific details from research.** Use real names, numbers, dates, and features from `Materials & Research`. NEVER use generic placeholders.
- **Creator's voice.** Use patterns from the voice guide (e.g., "I'm gonna", "All I had to do", "actually insane", "bro", "Watch this").
- **Screen Recording > Text Overlay.** Showing the tool/product in action always outperforms text lists.
- **Withhold, don't front-load.** Build curiosity through the beats — don't give away the punchline early.

---

## Step 3: Save to Pipeline

After the user approves the filming card(s), save to Airtable.

**Airtable Details:**
- MCP: `airtable` → `update_records` (single hook) or `create_record` (multiple hooks)
- Base: `YOUR_AIRTABLE_BASE_ID`
- Table: `YOUR_CONTENT_PIPELINE_TABLE_ID` (Content Pipeline)

**Fields to save per video:**

| Airtable Field | What Goes Here |
|---------------|----------------|
| `Hook 1` | The chosen hook line (spoken) |
| `On-Screen Text Hook` | Text overlay version of the hook (if different from spoken) |
| `Script` | The full filming card body (beats with example sentences + screen directions) |
| `Post Caption` | CTA or caption for the post |
| `Recording Instructions` | Any special recording notes (split-screen, screen recording setup, B-roll needed) |

**DO NOT overwrite `Materials & Research`** — that field holds the research brief from ideation. The script goes in `Script`.

**After saving script fields, update `Status` to "🎬 Filming"** to move the record into the filming pipeline. The video is scripted — it's ready to film.

### Pipeline Statuses (for reference):
```
💡 Idea → ✍️ Scripting → 📝 Prep Materials → 🎬 Filming → ✂️ Editing → 🚀 Prep For Post → 📅 Scheduled → ✅ Posted
```

### Visual Format Options:
- `Selfie` — talking head
- `Selfie + Image Background` — talking head with image behind
- `Split Screen` — split-screen with B-roll/demo footage
- `B Roll + Words` — footage with text overlay

### Single hook picked:
Update the existing pipeline record with the hook/script/CTA fields above, then set Status → "🎬 Filming".

### Multiple hooks picked (e.g., A, C, E):
- **First hook** → update the existing record
- **Each additional hook** → create a NEW record with the same Title (appended with the hook structure, e.g., "How to Set Up Claude Code (Contrarian)"), same Materials & Research, same Topic, same Type, same Date Created, but different Hook 1, Script, Post Caption, and Recording Instructions
- **Set Status → "🎬 Filming"** on ALL records (existing + new)
- **Set Visual Format** on ALL records based on the content type and recording instructions

Each video = its own record. Never combine multiple hooks into one record.

---

## Long-Form Scripts

For YouTube videos, VSLs, or content over 60 seconds, use a fuller script format:

```
HOOK (0-3 sec): [Topic clarity + shock value]

BODY (3-20 sec): [3 beats max, clear story flow]

REHOOK (if 30+ sec): [Re-agitate — "But here's where it gets crazy..."]

BODY 2 (20-40 sec): [More value]

CTA: [Single clear action]
```

Apply the same framework.md psychology checkpoints. For rehook phrases, see `references/framework.md`.

---

## Iteration

Common revision requests:
- **"Shorter"** → Cut to 2 beats, keep hook and close
- **"Different hook"** → Go back to Step 1, present 6 new options from different frameworks
- **"More controversial"** → Add contrarian angle, bolder claims
- **"Different CTA"** → Try engagement question vs simple follow
- **"Full script instead"** → Expand beats into full sentences (but warn: memorized scripts sound stiff)
- **"Just showcase"** → Cut any "creator doing their own thing" beats, keep it focused on showing the subject

---

## Voice & Tone

The skill does NOT define a specific voice. Each project's CLAUDE.md specifies:
- Speech patterns and catchphrases
- Energy level and personality
- Language simplification rules
- Winner/loser examples with analysis

If no voice guide exists in the project, default to:
- Casual, conversational tone
- 6th grade vocabulary
- Active voice
- High energy, genuine excitement

---

## References

| File | Read When |
|------|-----------|
| `references/framework.md` | **EVERY scripting session** — hook formula, psychology, validation |

---

## Part of the Content Team

```
/daily-content-researcher → Pipeline (Airtable) → /content-ideator (research + angles) → /content-scripter (this skill)
```

The ideator saves research + angle to the Content Pipeline. This skill reads that research in Step 0 to inform hook selection and filming card details. After generating the card, it saves hook/script/CTA to the pipeline fields.

**Skills:**
- `/daily-content-researcher` — Agentic morning research, pipeline save
- `/content-ideator` — Pull pipeline ideas, deep research, unique angles
- `/content-scripter` (this skill) — Read research, hooks, filming card, pipeline save
