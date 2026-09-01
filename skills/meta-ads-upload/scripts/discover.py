#!/usr/bin/env python3
"""Discovery + reference cloning.

  discover.py accounts
  discover.py campaigns  [act_id] [--all]
  discover.py adsets     <campaign_id>
  discover.py ads        <adset_id>
  discover.py pages      [act_id]
  discover.py clone      <adset_id> [-o out.json]   <-- the important one

`clone` dumps an existing ad set's full settings plus its ads' copy/headlines/
creative shape. Feed that into build.py so new ads inherit a proven setup
verbatim instead of being reinvented.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import api, api_all, err, resolve_account, from_minor  # noqa: E402

ADSET_FIELDS = (
    "name,status,effective_status,campaign_id,optimization_goal,billing_event,"
    "destination_type,bid_strategy,bid_amount,daily_budget,lifetime_budget,"
    "daily_min_spend_target,daily_spend_cap,promoted_object,targeting,"
    "attribution_spec,start_time,end_time,is_dynamic_creative,pacing_type"
)
AD_FIELDS = (
    "name,status,effective_status,creative{id,title,body,object_story_spec,"
    "asset_feed_spec,degrees_of_freedom_spec,call_to_action_type}"
)


def _p(x):
    print(json.dumps(x, ensure_ascii=False, indent=1))


def accounts():
    rows = api_all("me/adaccounts", {"fields": "name,account_id,currency,timezone_name,account_status"})
    if isinstance(rows, dict):
        print("ERROR:", err(rows)); return
    for a in rows:
        state = "ACTIVE" if a.get("account_status") == 1 else f"status={a.get('account_status')}"
        print(f"act_{a['account_id']:<20} {a.get('currency'):<5} {state:<12} {a.get('name')}")


def campaigns(act, show_all=False):
    rows = api_all(f"{act}/campaigns", {
        "fields": "name,status,effective_status,objective,daily_budget,lifetime_budget,bid_strategy"})
    if isinstance(rows, dict):
        print("ERROR:", err(rows)); return
    for c in rows:
        if not show_all and c.get("effective_status") not in ("ACTIVE", "PAUSED"):
            continue
        budget = c.get("daily_budget") or c.get("lifetime_budget")
        kind = "CBO" if budget else "ABO"
        b = from_minor(budget) if budget else None
        print(f"{c['id']:<22} {c.get('effective_status'):<10} {kind:<4} "
              f"{str(b or ''):<9} {c.get('objective','?'):<18} {c.get('name')}")


def adsets(campaign_id):
    rows = api_all(f"{campaign_id}/adsets", {
        "fields": "name,status,effective_status,daily_budget,daily_min_spend_target,optimization_goal"})
    if isinstance(rows, dict):
        print("ERROR:", err(rows)); return
    for a in rows:
        print(f"{a['id']:<22} {a.get('effective_status'):<10} "
              f"budget={str(from_minor(a.get('daily_budget')) or '-'):<8} "
              f"min={str(from_minor(a.get('daily_min_spend_target')) or '-'):<7} {a.get('name')}")


def ads(adset_id):
    rows = api_all(f"{adset_id}/ads", {"fields": "name,status,effective_status"})
    if isinstance(rows, dict):
        print("ERROR:", err(rows)); return
    for a in rows:
        print(f"{a['id']:<22} {a.get('effective_status'):<16} {a.get('name')}")


def pages(act):
    """Page/IG pairs usable for ads.

    Ads fail with (#10)/1341012 if the token cannot post as the page, so the
    authoritative list is (a) pages the token resolves by name, plus (b) the
    page/IG pairs already in use by ads in this account. The IG edges need a Page
    access token, so pairs are recovered from existing creatives instead.
    """
    accessible = {}
    r = api(f"{act}/promote_pages", {"fields": "id,name"})
    if "__error__" in r:
        r = api("me/accounts", {"fields": "id,name"})
    for p in (r.get("data") or []):
        accessible[p["id"]] = p.get("name")

    pairs = {}
    # Small pages only: object_story_spec is heavy and the account-level /ads edge
    # returns "reduce the amount of data" if asked for too many at once.
    ad_rows = []
    for lim in (25, 10):
        r = api(f"{act}/ads", {"fields": "creative{object_story_spec}", "limit": lim})
        if "__error__" not in r:
            ad_rows = r.get("data", [])
            break
    if not ad_rows:
        print("WARN: could not scan existing ads for page/IG pairs.")
    for ad in ad_rows:
        oss = ((ad.get("creative") or {}).get("object_story_spec") or {})
        pid = oss.get("page_id")
        if pid:
            pairs.setdefault(pid, set()).add(
                oss.get("instagram_user_id") or oss.get("instagram_actor_id"))

    print("page_id                ig_user_id             usable  name")
    seen = set()
    for pid, igs in pairs.items():
        for ig in igs:
            name = accessible.get(pid)
            if name is None:
                probe = api(pid, {"fields": "name"})
                name = probe.get("name") if "__error__" not in probe else None
            ok = "yes" if name else "NO"
            print(f"{pid:<22} {str(ig or '-'):<22} {ok:<7} {name or '(no access — ads will fail)'}")
            seen.add(pid)
    for pid, name in accessible.items():
        if pid not in seen:
            print(f"{pid:<22} {'-':<22} {'yes':<7} {name}  (no ads yet; IG id unknown)")
    print("\nPick a page marked usable=yes. page_id and ig_user_id must be used as a pair.")


def clone(adset_id, out=None):
    """Dump an ad set + its ads as a reusable reference blob."""
    aset = api(adset_id, {"fields": ADSET_FIELDS})
    if "__error__" in aset:
        print("ERROR:", err(aset)); sys.exit(1)
    ad_rows = api_all(f"{adset_id}/ads", {"fields": AD_FIELDS})
    if isinstance(ad_rows, dict):
        print("ERROR:", err(ad_rows)); sys.exit(1)

    copies, page_id, ig_id, link, cta = [], None, None, None, None
    creative_shapes = []
    for ad in ad_rows:
        cr = ad.get("creative", {}) or {}
        oss = cr.get("object_story_spec", {}) or {}
        page_id = page_id or oss.get("page_id")
        ig_id = ig_id or oss.get("instagram_user_id") or oss.get("instagram_actor_id")
        vd, ld = oss.get("video_data", {}) or {}, oss.get("link_data", {}) or {}
        shape = "video" if vd else ("carousel" if ld.get("child_attachments") else ("image" if ld else "?"))
        creative_shapes.append(shape)
        cta_obj = vd.get("call_to_action") or ld.get("call_to_action") or {}
        cta = cta or cta_obj.get("type")
        link = link or (cta_obj.get("value", {}) or {}).get("link") or ld.get("link")
        afs = cr.get("asset_feed_spec", {}) or {}
        entry = {
            "ad_name": ad.get("name"),
            "status": ad.get("status"),
            "shape": shape,
            "headline": cr.get("title") or vd.get("title") or ld.get("name"),
            "primary_text": cr.get("body") or vd.get("message") or ld.get("message"),
            "headlines_all": [t.get("text") for t in afs.get("titles", [])],
            "primary_texts_all": [b.get("text") for b in afs.get("bodies", [])],
            "descriptions_all": [d.get("text") for d in afs.get("descriptions", [])],
            "multi_text_optimization": afs.get("optimization_type"),
            "creative_enhancements_disabled": bool(cr.get("degrees_of_freedom_spec")),
        }
        if shape == "carousel":
            entry["carousel_cards"] = ld.get("child_attachments")
            entry["multi_share_end_card"] = ld.get("multi_share_end_card")
            entry["multi_share_optimized"] = ld.get("multi_share_optimized")
        copies.append(entry)

    camp = api(aset.get("campaign_id"), {
        "fields": "name,objective,daily_budget,lifetime_budget,bid_strategy,status"})

    blob = {
        "reference_adset_id": adset_id,
        "campaign": camp,
        "campaign_is_cbo": bool(camp.get("daily_budget") or camp.get("lifetime_budget")),
        "adset_settings": {
            k: aset.get(k) for k in (
                "optimization_goal", "billing_event", "destination_type", "bid_strategy",
                "promoted_object", "targeting", "attribution_spec",
                "daily_budget", "daily_min_spend_target", "is_dynamic_creative")
            if aset.get(k) is not None
        },
        "adset_name_example": aset.get("name"),
        "page_id": page_id,
        "instagram_user_id": ig_id,
        "link": link,
        "cta": cta,
        "creative_shapes_seen": sorted(set(creative_shapes)),
        "ads": copies,
    }
    # promoted_object carries a read-only echo field; drop so it can be re-POSTed
    po = blob["adset_settings"].get("promoted_object")
    if isinstance(po, dict):
        po.pop("smart_pse_enabled", None)

    txt = json.dumps(blob, ensure_ascii=False, indent=1)
    if out:
        open(out, "w").write(txt)
        print(f"wrote {out}")
        print(f"  campaign      : {camp.get('name')} ({'CBO' if blob['campaign_is_cbo'] else 'ABO'})")
        print(f"  page/ig       : {page_id} / {ig_id}")
        print(f"  link / cta    : {link} / {cta}")
        print(f"  shapes        : {blob['creative_shapes_seen']}")
        print(f"  ads captured  : {len(copies)}")
        uniq_h = {c["headline"] for c in copies if c.get("headline")}
        uniq_b = {c["primary_text"] for c in copies if c.get("primary_text")}
        print(f"  unique copy   : {len(uniq_h)} headline(s), {len(uniq_b)} primary text(s)")
        for c in copies:
            if c.get("headlines_all"):
                print(f"  NOTE: '{c['ad_name']}' rotates {len(c['headlines_all'])} headlines / "
                      f"{len(c['primary_texts_all'])} texts (multi-text optimization)")
                break
    else:
        print(txt)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "accounts":
        accounts()
    elif cmd == "campaigns":
        act = resolve_account(args[0] if args and args[0].startswith(("act_", "1", "2", "3", "4", "5", "6", "7", "8", "9")) else None)
        campaigns(act, show_all="--all" in args)
    elif cmd == "adsets":
        adsets(args[0])
    elif cmd == "ads":
        ads(args[0])
    elif cmd == "pages":
        pages(resolve_account(args[0] if args else None))
    elif cmd == "clone":
        out = None
        if "-o" in args:
            out = args[args.index("-o") + 1]
        clone(args[0], out)
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
