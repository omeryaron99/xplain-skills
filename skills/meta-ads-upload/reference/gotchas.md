# Meta Ads API — failure modes and field notes

Every entry here cost a real debugging cycle. Check this before improvising.

## Errors you will actually hit

### `(#200) ... NOT grant ads_management or ads_read permission`
Almost never a token scope problem. It usually means **the request targeted an ad
account the token can't see** — e.g. an MCP server configured with the wrong
`META_AD_ACCOUNT_ID`. Verify with `discover.py accounts` and compare against the
account id in `~/.claude.json` / `~/.mcp.json`. Fix the config, then reconnect the
MCP server (env vars are read at process spawn — editing the file does nothing
until it restarts).

### `(#10) ... No permission to access this profile` (subcode 1341012)
The token cannot post as the Page/IG in `object_story_spec`. Common when cloning a
reference ad set whose ads run on a **different Page** than the one you have access
to. Run `discover.py pages`, pick a page that resolves, and swap `page_id` +
`instagram_user_id` together (they are a pair — a mismatched IG id fails too).
Tell the user you switched pages; do not silently publish under a different brand.

### `Minimum Spend Limit Is Higher Than Campaign Budget` (subcode 1885648)
Raised when activating an ad set in a CBO campaign. Meta compares the campaign
budget against the **sum of `daily_min_spend_target` across ad sets — including
PAUSED ones that still carry a value.** A campaign can therefore look like it has
headroom and still reject the activation. Options, in order of preference:
1. Drop the new ad set's minimum entirely (let CBO allocate freely).
2. Clear stale minimums off paused ad sets that aren't running.
3. Raise the campaign daily budget.

Setting the value to `1` (i.e. 0.01 in account currency) will activate, but that is
**not** a meaningful floor — never present it as one; say the minimum was effectively
removed.

### `You Must Also Select Instagram Explore` (subcode 2490392)
`instagram_positions` containing `explore_home` requires `explore` as well.
`build.py` patches this automatically in `fix_targeting()`.

### `(#3) AdAccount must pass GK: contextual_bundle_test_api_accounts`
`contextual_bundling_spec` — the **Multi-advertiser ads** toggle — is gated to Meta
test accounts. It cannot be read or written via the API on a normal account. It is
**UI-only**: Ad set → Advantage+ placements → Multi-advertiser ads. Do not claim to
have changed it; tell the user to flip it manually.

### `UnsupportedDofAssetFeedSpecFieldInCarouselAd` (subcode 2446264)
A **carousel** ad's `asset_feed_spec` may contain **only `bodies`** — `titles` and
`descriptions` are rejected. Multiple headlines on a carousel must go on the cards
(`child_attachments[].name`), one per card. `build.py` strips them automatically.

### Read-only echo fields rejected on POST
Meta returns fields it will not accept back:
- `targeting.age_range` (derived from `age_min`/`age_max`)
- `promoted_object.smart_pse_enabled`
- custom audience entries come back as `{id, name}` but must be POSTed as `{id}`

`discover.py clone` and `build.py` strip these.

## Structure rules

- **CBO campaigns** (campaign has `daily_budget`/`lifetime_budget`): ad sets must
  **not** carry a budget. Sending one errors. `build.py` strips it after reading the
  campaign. ABO is the reverse — each ad set needs its own budget.
- **Always create PAUSED**, verify, then activate. Never build straight to ACTIVE
  in a live account.
- **Activation order**: ads first, then ad sets, then campaign. Reverse for pausing.
- **Scheduling a future launch**: set the ad set's `start_time` (ISO 8601 with
  offset, e.g. `2026-07-13T09:00:00+0300`) and set everything ACTIVE. Meta holds
  delivery until then — that is what "schedule live now" means. Nothing spends early.
- `effective_status` is the truth, `status` is only what you requested. New ads show
  `IN_PROCESS` / `PENDING_REVIEW` during Meta review — normal, usually clears within
  hours. `ACTIVE` at ad level + `PAUSED` parent still means nothing serves.

## Creative shapes (`object_story_spec`)

| Shape | Key | Notes |
|---|---|---|
| Video | `video_data` | `video_id`, `image_url` (thumbnail), `message` (primary text), `title` (headline) |
| Single image | `link_data` | `image_hash`, `link`, `message`, `name` (headline) |
| Carousel | `link_data.child_attachments` | 2–10 cards, each `{link, image_hash, name, call_to_action}`. Card order = array order. `multi_share_optimized:false` keeps your order; `true` lets Meta reorder. `multi_share_end_card:false` drops the trailing page card. |

CTA lives at `call_to_action: {type, value:{link}}` on video/image; carousel cards
take `{type}` only (the link is per-card).

## Multi-text (rotating headlines / bodies)

More than one headline or primary text ⇒ add `asset_feed_spec` **alongside**
`object_story_spec`:

```json
{"bodies":[{"text":"..."}],"titles":[{"text":"..."}],"optimization_type":"DEGREES_OF_FREEDOM"}
```

This is *not* Dynamic Creative (`is_dynamic_creative` on the ad set) — it is
per-ad text optimization, which is what the UI produces when you add several
headline/primary-text variants to one ad. Keep `object_story_spec` populated with
the first variant so the ad still renders if the feed is ignored.

## Turning off Advantage+ creative enhancements

Pass `degrees_of_freedom_spec` with every feature set to `OPT_OUT`
(`meta.opt_out_spec()`). Cloned reference ads that had enhancements disabled will
show `creative_enhancements_disabled: true` in the clone blob.

## Media upload

- **Images** → `POST {act}/adimages`, multipart, field name = filename. Response is
  `{"images": {"<filename>": {"hash": ...}}}`.
- **Videos** → `POST {act}/advideos` resumable: `start` (file_size) → repeated
  `transfer` (chunk at `start_offset`) → `finish`. Required above ~50MB, safe always.
- After upload a video is `processing`. **Poll `GET {video_id}?fields=status` until
  `ready`** before creating ads, then pull `GET {video_id}/thumbnails` and use the
  `is_preferred` one as `image_url`. Ads made against an unprocessed video get no
  thumbnail.
- Carousel card order follows filename order — sort naturally (`1, 2, 10`, not
  `1, 10, 2`). `upload_media.py` does this.

## Budgets and currency

All money is in **minor units** of the account currency: 100 ILS → `10000`.
Check `GET {act}?fields=currency` (zero-decimal currencies like JPY are 1:1).
`meta.to_minor()` / `from_minor()` handle it.

## Useful fields

- Campaign: `objective` (`OUTCOME_SALES`, `OUTCOME_LEADS`, `OUTCOME_TRAFFIC`, ...),
  `bid_strategy` (`LOWEST_COST_WITHOUT_CAP` = Highest Volume), `special_ad_categories`.
- Ad set: `optimization_goal` (`OFFSITE_CONVERSIONS`, `LINK_CLICKS`, `LEAD_GENERATION`),
  `billing_event` (usually `IMPRESSIONS`), `promoted_object`
  (`{pixel_id, custom_event_type}` — e.g. `PURCHASE`), `attribution_spec`,
  `destination_type` (`WEBSITE`), `targeting`.
