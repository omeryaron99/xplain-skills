---
name: meta-ads-upload
description: Upload creatives and build Meta (Facebook/Instagram) ads, ad sets and campaigns in any ad account — cloning settings and copy from an existing ad set so new creatives ship in minutes. Use when the user wants to upload videos/images to Meta Ads, add ads to a campaign, duplicate an ad set with new creative, or edit/publish/pause existing ads.
---

# Meta Ads — Creative Upload & Ad Builder

Turn a folder of creatives into live-ready Meta ads. The core move: **clone an
existing ad set** (its targeting, optimization, copy, headlines, CTA) and hang new
creatives off it, instead of re-specifying everything by hand.

Works with any ad account, campaign, product, or language.

## Operating principles

1. **Discover before asking.** Never ask the user for an ID you can look up. Run the
   discovery scripts first, then ask them to pick from real options.
2. **Batch the questions.** Use `AskUserQuestion` with multiple questions at once.
   Aim for **two rounds, maximum**. Speed is the point of this skill.
3. **Clone, don't invent.** If the user points at an existing ad set, copy its copy
   and settings *verbatim*. Only write new copy when explicitly asked. Ad text that
   was edited in Ads Manager lives on the ad, not in your memory — always re-read it.
4. **Build PAUSED, then publish.** Everything lands paused. Show the user what was
   built, get approval, then activate. Real money is at stake.
5. **Report honestly.** If Meta rejects something or you had to deviate (different
   page, dropped minimum spend), say so plainly. Never present a workaround as if it
   were what was asked for.

## Scripts

All under `scripts/`, run with `python3`. No dependencies. They find the access
token automatically (env `META_ADS_ACCESS_TOKEN`, else the meta-ads MCP config in
`~/.claude.json` / `~/.mcp.json`).

| Script | Purpose |
|---|---|
| `discover.py accounts \| campaigns \| adsets \| ads \| pages` | List what exists |
| `discover.py clone <adset_id> -o ref.json` | Dump a reference ad set's settings + ad copy |
| `upload_media.py <act_id> <paths...> -o assets.json` | Upload images/videos (resumable, polls video processing) |
| `build.py plan.json -o built.json` | Create ad sets + ads (PAUSED) |
| `verify.py built.json` | Print the resulting tree with real statuses |
| `publish.py built.json --activate` | Flip live (ads → ad sets → campaign) |

Read `reference/gotchas.md` before debugging any API error — the failure modes are
catalogued there with fixes.

## Workflow

### Step 0 — Orient (no questions yet)

Run in parallel, and also `ls` any creative folder the user mentioned:

```bash
python3 scripts/discover.py accounts
python3 scripts/discover.py campaigns act_XXX
```

If the user named a campaign, grep for it. If several match (common — accounts have
`Launch`, `Scale`, `Relaunch` variants of the same name), **ask which one**; don't
guess. Note which are ACTIVE and their budgets.

### Step 1 — Ask (round 1)

Batch these. Pre-fill options from Step 0:

- **Destination** — which campaign? (show status + budget so they can tell them apart)
- **Reference ad set** — "copy settings and copy from which existing ad set?"
  List recent ad sets. This one question replaces ~10 others.
- **Creative split** — how should these files map to ad sets? Offer the shapes you
  can see in the folder, e.g. "all in one ad set", "one ad set per creative",
  "images as a carousel + videos separate".
- **Anything to change** vs. the reference — copy, headline, landing page, budget,
  schedule. Default is "identical to reference".

Then clone the reference:

```bash
python3 scripts/discover.py clone <adset_id> -o ref.json
```

Read `ref.json`. It reports the page/IG, link, CTA, creative shapes, and whether the
ads rotate multiple headlines/bodies. **Show the user the actual copy you're about
to reuse** (first ~5 lines is enough) so they can catch stale text.

### Step 2 — Ask (round 2, only what's still open)

Typically just: budget/min-spend, schedule (launch now or a future `start_time`),
and activate-now vs. leave-paused. Skip anything already settled.

### Step 3 — Upload media

```bash
python3 scripts/upload_media.py act_XXX "/path/to/folder" -o assets.json
```

Directories expand and sort naturally so carousel order matches `1.jpg, 2.png, 10.jpg`.
Videos are polled until `ready` and their preferred thumbnail is saved. Large videos
take a few minutes — that's normal, let it run.

### Step 4 — Write the plan

Compose `plan.json` from `ref.json` + the answers. Structure and every field are
documented in `build.py`'s docstring — read it. Minimum shape:

```json
{
  "account_id": "act_XXX",
  "campaign_id": "120...",
  "page_id": "<from ref.json>",
  "instagram_user_id": "<from ref.json>",
  "link": "<from ref.json>",
  "cta": "LEARN_MORE",
  "adset_settings": { "<paste adset_settings from ref.json>": "" },
  "copy": {
    "primary_texts": ["<from ref.json>"],
    "headlines": ["<from ref.json>"]
  },
  "adsets": [
    {"name": "...", "ads": [
      {"name": "...", "video": "clip.mp4"},
      {"name": "...", "carousel": ["1.jpg", "2.png"]}
    ]}
  ]
}
```

Several entries in `primary_texts` / `headlines` ⇒ Meta rotates them
(`DEGREES_OF_FREEDOM`), matching the UI's multi-text setup. Copy the reference's
count exactly unless told otherwise. (Carousels accept rotating body text only —
their headlines live per card.)

Name ad sets and ads consistently with what's already in the account — check the
reference's naming pattern (often `Concept | Type | DD/M/YY`).

### Step 5 — Build, verify, show

```bash
python3 scripts/build.py plan.json -o built.json
python3 scripts/verify.py built.json
```

Use `--dry-run` first if the plan is large or unusual. Then summarize for the user
as a small table: ad set → ads → creative type → headline. Flag anything that
deviated from the reference.

### Step 6 — Publish on approval

```bash
python3 scripts/publish.py built.json --activate
python3 scripts/verify.py built.json
```

Add `--campaign` if the parent campaign is paused. Confirm the final
`effective_status` and tell the user `IN_PROCESS`/`PENDING_REVIEW` is normal review.

## Editing existing ads

To change copy, budget, status, or targeting on things that already exist:

- Read current state first (`discover.py clone` on the ad set, or `verify.py --adsets`).
- Ad **copy cannot be edited in place** — Meta creatives are immutable. Create a
  replacement ad in the same ad set and delete/pause the old one. Say this rather
  than silently making a duplicate.
- Budget/status/targeting update fine via `POST {id}` with the changed field.
- Deleting an ad set removes its ads: `publish.py built.json --delete`.

## Things that will bite you

Full catalogue in `reference/gotchas.md`. The short list:

- **CBO campaigns**: ad sets must not carry a budget. ABO: they must.
- **`daily_min_spend_target`** is summed across *all* ad sets including paused ones;
  exceeding the campaign budget blocks activation (subcode 1885648). Removing the
  minimum is usually right — and say that you removed it.
- **Multi-advertiser ads** (`contextual_bundling_spec`) is API-gated on normal
  accounts. UI-only. Don't claim to have changed it.
- **Page permissions**: cloning an ad set from a different Page fails with subcode
  1341012. Switch to an accessible page via `discover.py pages` and tell the user.
- **Wrong ad account** in the MCP config surfaces as a bogus "no ads_management
  permission" error. Check the account id before believing the permission message.
- Videos must finish processing before ads are created, or they render without a
  thumbnail.
