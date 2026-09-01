#!/usr/bin/env python3
"""Create ad sets + ads from a plan file. Everything lands PAUSED by default.

  build.py plan.json [-o built.json] [--dry-run]

Plan schema (only 'campaign_id', 'page_id', 'link' and 'adsets' are required;
everything else has sane defaults or comes from a cloned reference):

{
  "account_id": "act_123",
  "campaign_id": "120...",
  "page_id": "...", "instagram_user_id": "...",
  "link": "https://example.com/", "cta": "LEARN_MORE",
  "adset_settings": { ...verbatim from discover.py clone... },
  "copy": {
    "primary_texts": ["body A", "body B"],     // >1 = multi-text optimization
    "headlines":     ["headline A"],
    "descriptions":  [],
    "disable_creative_enhancements": true
  },
  "adsets": [
    { "name": "Ad set 1",
      "settings": { "daily_min_spend_target": 15000 },   // optional overrides
      "ads": [
        {"name": "Vid 1", "video": "clip.mp4"},
        {"name": "Img 1", "image": "pic.jpg"},
        {"name": "Carousel", "carousel": ["1.jpg","2.png","3.jpg"]},
        {"name": "Custom copy", "video": "x.mp4",
         "primary_text": "override", "headline": "override"}
      ]}
  ]
}

Media names are looked up in assets.json (written by upload_media.py); a raw
image hash / video id also works.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import api, err, opt_out_spec, jdump, resolve_account  # noqa: E402


def load_assets(plan_dir, plan):
    path = plan.get("assets_file", "assets.json")
    if not os.path.isabs(path):
        path = os.path.join(plan_dir, path)
    if os.path.exists(path):
        return json.load(open(path))
    return {"images": {}, "videos": {}}


def fix_targeting(t):
    """Apply the fixups Meta rejects ad sets over."""
    if not isinstance(t, dict):
        return t
    t = json.loads(json.dumps(t))  # deep copy
    ig = t.get("instagram_positions")
    # 'explore_home' is invalid without 'explore' (error_subcode 2490392)
    if ig and "explore_home" in ig and "explore" not in ig:
        ig.insert(ig.index("explore_home"), "explore")
    # read-only echo fields that cannot be POSTed back
    t.pop("age_range", None)
    for aud_key in ("custom_audiences", "excluded_custom_audiences"):
        if isinstance(t.get(aud_key), list):
            t[aud_key] = [{"id": a["id"]} if isinstance(a, dict) else {"id": a} for a in t[aud_key]]
    return t


def resolve_image(assets, ref):
    if ref in assets.get("images", {}):
        return assets["images"][ref]["hash"]
    return ref  # assume a raw hash


def resolve_video(assets, ref):
    v = assets.get("videos", {}).get(ref)
    if v:
        return v["video_id"], v.get("thumb")
    return ref, None  # assume a raw video id


def build_creative(ad, plan, assets):
    """Assemble object_story_spec (+ asset_feed_spec for multi-text)."""
    page = plan["page_id"]
    ig = plan.get("instagram_user_id")
    link = ad.get("link", plan["link"])
    cta = ad.get("cta", plan.get("cta", "LEARN_MORE"))
    copy = plan.get("copy", {}) or {}

    bodies = ad.get("primary_texts") or ([ad["primary_text"]] if ad.get("primary_text")
                                         else copy.get("primary_texts") or [])
    titles = ad.get("headlines") or ([ad["headline"]] if ad.get("headline")
                                     else copy.get("headlines") or [])
    descs = ad.get("descriptions") or copy.get("descriptions") or []
    body0 = bodies[0] if bodies else None
    title0 = titles[0] if titles else None

    oss = {"page_id": page}
    if ig:
        oss["instagram_user_id"] = ig

    if ad.get("carousel"):
        cards = []
        for card in ad["carousel"]:
            if isinstance(card, dict):
                h = card.get("image") or card.get("image_hash")
                cards.append({
                    "link": card.get("link", link),
                    "image_hash": resolve_image(assets, h),
                    "name": card.get("headline", title0),
                    "description": card.get("description"),
                    "call_to_action": {"type": card.get("cta", cta)},
                })
            else:
                cards.append({
                    "link": link,
                    "image_hash": resolve_image(assets, card),
                    "name": title0,
                    "call_to_action": {"type": cta},
                })
        cards = [{k: v for k, v in c.items() if v is not None} for c in cards]
        ld = {
            "link": link,
            "child_attachments": cards,
            "multi_share_end_card": ad.get("end_card", False),
            "multi_share_optimized": ad.get("auto_optimize_order", False),
            "call_to_action": {"type": cta, "value": {"link": link}},
        }
        if body0:
            ld["message"] = body0
        oss["link_data"] = ld

    elif ad.get("video"):
        vid, thumb = resolve_video(assets, ad["video"])
        vd = {"video_id": vid, "call_to_action": {"type": cta, "value": {"link": link}}}
        if ad.get("thumbnail") or thumb:
            vd["image_url"] = ad.get("thumbnail") or thumb
        if body0:
            vd["message"] = body0
        if title0:
            vd["title"] = title0
        if descs:
            vd["link_description"] = descs[0]
        oss["video_data"] = vd

    elif ad.get("image"):
        ld = {
            "image_hash": resolve_image(assets, ad["image"]),
            "link": link,
            "call_to_action": {"type": cta, "value": {"link": link}},
        }
        if body0:
            ld["message"] = body0
        if title0:
            ld["name"] = title0
        if descs:
            ld["description"] = descs[0]
        oss["link_data"] = ld
    else:
        raise SystemExit(f"ad '{ad.get('name')}' has no video/image/carousel")

    creative = {"object_story_spec": oss}

    # >1 headline or body => let Meta rotate them (same shape the UI produces).
    # Carousels are the exception: Meta only accepts 'bodies' there (error 2446264),
    # so extra headlines must live on the cards themselves.
    is_carousel = bool(ad.get("carousel"))
    if len(bodies) > 1 or (not is_carousel and (len(titles) > 1 or len(descs) > 1)):
        afs = {"optimization_type": "DEGREES_OF_FREEDOM"}
        if bodies:
            afs["bodies"] = [{"text": b} for b in bodies]
        if not is_carousel:
            if titles:
                afs["titles"] = [{"text": t} for t in titles]
            if descs:
                afs["descriptions"] = [{"text": d} for d in descs]
        creative["asset_feed_spec"] = afs

    if copy.get("disable_creative_enhancements", True):
        creative["degrees_of_freedom_spec"] = opt_out_spec()

    return creative


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    out_path = "built.json"
    if "-o" in args:
        i = args.index("-o"); out_path = args[i + 1]; del args[i:i + 2]

    plan_path = args[0]
    plan = json.load(open(plan_path))
    plan_dir = os.path.dirname(os.path.abspath(plan_path))
    assets = load_assets(plan_dir, plan)

    act = resolve_account(plan.get("account_id"))
    camp_id = plan["campaign_id"]
    status = plan.get("status", "PAUSED")

    camp = api(camp_id, {"fields": "name,objective,daily_budget,lifetime_budget,status"})
    if "__error__" in camp:
        print("ERROR reading campaign:", err(camp)); sys.exit(1)
    is_cbo = bool(camp.get("daily_budget") or camp.get("lifetime_budget"))
    print(f"Campaign: {camp.get('name')}  [{'CBO' if is_cbo else 'ABO'}]  status={camp.get('status')}")
    print(f"Creating {len(plan['adsets'])} ad set(s), status={status}\n")

    base = dict(plan.get("adset_settings", {}) or {})
    base.pop("is_dynamic_creative", None)
    if is_cbo:
        # budgets live on the campaign; sending them on the ad set errors out
        base.pop("daily_budget", None)
        base.pop("lifetime_budget", None)

    built = {"campaign_id": camp_id, "adsets": []}
    for spec in plan["adsets"]:
        settings = dict(base)
        settings.update(spec.get("settings", {}) or {})
        if is_cbo:
            settings.pop("daily_budget", None)
            settings.pop("lifetime_budget", None)

        params = {"name": spec["name"], "campaign_id": camp_id, "status": status}
        for k, v in settings.items():
            if v is None:
                continue
            params[k] = jdump(fix_targeting(v)) if k == "targeting" else (
                jdump(v) if isinstance(v, (dict, list)) else v)

        if dry:
            print(f"[dry-run] ad set {spec['name']}: {json.dumps(params, ensure_ascii=False)[:300]}")
            aset_id = "DRYRUN"
        else:
            r = api(f"{act}/adsets", params, method="POST")
            if "__error__" in r:
                print(f"  x AD SET '{spec['name']}': {err(r)}")
                built["adsets"].append({"name": spec["name"], "error": err(r)})
                continue
            aset_id = r["id"]
            print(f"  + AD SET {aset_id}  {spec['name']}")

        entry = {"id": aset_id, "name": spec["name"], "ads": []}
        for ad in spec.get("ads", []):
            creative = build_creative(ad, plan, assets)
            if dry:
                shape = "carousel" if ad.get("carousel") else ("video" if ad.get("video") else "image")
                print(f"      [dry-run] ad '{ad['name']}' ({shape})")
                entry["ads"].append({"name": ad["name"], "id": "DRYRUN"})
                continue
            r = api(f"{act}/ads", {
                "name": ad["name"], "adset_id": aset_id,
                "creative": jdump(creative), "status": status,
            }, method="POST")
            if "__error__" in r:
                print(f"      x ad '{ad['name']}': {err(r)}")
                entry["ads"].append({"name": ad["name"], "error": err(r)})
            else:
                print(f"      + ad {r['id']}  {ad['name']}")
                entry["ads"].append({"name": ad["name"], "id": r["id"]})
        built["adsets"].append(entry)

    if not dry:
        json.dump(built, open(out_path, "w"), ensure_ascii=False, indent=1)
        print(f"\nwrote {out_path}")
        fails = [a for s in built["adsets"] for a in s.get("ads", []) if "error" in a]
        fails += [s for s in built["adsets"] if "error" in s]
        if fails:
            print(f"!! {len(fails)} failure(s) — see above. Nothing is live (status={status}).")
        else:
            print(f"All created with status={status}. Review, then: publish.py {out_path} --activate")


if __name__ == "__main__":
    main()
