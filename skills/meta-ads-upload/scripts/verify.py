#!/usr/bin/env python3
"""Print the campaign -> ad set -> ad tree with real statuses and settings.

  verify.py built.json
  verify.py --campaign <campaign_id>
  verify.py --adsets 120...,120...

Use after build.py (confirm what was created) and after publish.py (confirm it
actually went live). effective_status is the truth; status is only what you asked for.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import api, api_all, err, from_minor  # noqa: E402

ADSET_FIELDS = ("name,status,effective_status,daily_budget,daily_min_spend_target,"
                "optimization_goal,billing_event,destination_type,promoted_object,"
                "targeting,start_time,campaign_id")


def show_adset(asid, indent="  "):
    a = api(asid, {"fields": ADSET_FIELDS})
    if "__error__" in a:
        print(f"{indent}x {asid}: {err(a)}"); return
    t = a.get("targeting", {}) or {}
    geo = (t.get("geo_locations", {}) or {}).get("countries")
    ta = t.get("targeting_automation", {}) or {}
    print(f"{indent}AD SET {a['id']}  {a.get('name')}")
    print(f"{indent}  status={a.get('status')}/{a.get('effective_status')}  "
          f"opt={a.get('optimization_goal')}  budget={from_minor(a.get('daily_budget')) or '-'}  "
          f"min_spend={from_minor(a.get('daily_min_spend_target')) or '-'}")
    po = a.get("promoted_object") or {}
    print(f"{indent}  geo={geo} age={t.get('age_min')}-{t.get('age_max')} "
          f"advantage_audience={ta.get('advantage_audience')} "
          f"pixel={po.get('pixel_id')} event={po.get('custom_event_type')}")
    if t.get("custom_audiences"):
        print(f"{indent}  include: {[c.get('name', c.get('id')) for c in t['custom_audiences']]}")
    if t.get("excluded_custom_audiences"):
        print(f"{indent}  exclude: {[c.get('name', c.get('id')) for c in t['excluded_custom_audiences']]}")
    if a.get("start_time"):
        print(f"{indent}  start_time={a['start_time']}")

    ads = api_all(f"{asid}/ads", {
        "fields": "name,status,effective_status,creative{title,body,object_story_spec,asset_feed_spec}"})
    if isinstance(ads, dict):
        print(f"{indent}  x ads: {err(ads)}"); return
    for ad in ads:
        cr = ad.get("creative", {}) or {}
        oss = cr.get("object_story_spec", {}) or {}
        ld = oss.get("link_data", {}) or {}
        shape = ("carousel" if ld.get("child_attachments") else
                 "video" if oss.get("video_data") else "image" if ld else "?")
        extra = ""
        if shape == "carousel":
            extra = f" ({len(ld['child_attachments'])} cards)"
        afs = cr.get("asset_feed_spec", {}) or {}
        if afs.get("titles") or afs.get("bodies"):
            extra += f" [rotating {len(afs.get('titles', []))}h/{len(afs.get('bodies', []))}b]"
        print(f"{indent}    AD {ad['id']}  {ad.get('name')}")
        print(f"{indent}      {ad.get('status')}/{ad.get('effective_status')}  {shape}{extra}")
        if shape == "carousel":
            # carousel headlines live per card; link_data.name echoes the page name
            title = (ld["child_attachments"][0] or {}).get("name")
        else:
            title = cr.get("title") or (oss.get("video_data", {}) or {}).get("title") or ld.get("name")
        if title:
            print(f"{indent}      headline: {title}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)

    if args[0] == "--campaign":
        cid = args[1]
        c = api(cid, {"fields": "name,status,effective_status,objective,daily_budget,bid_strategy"})
        print(f"CAMPAIGN {cid}  {c.get('name')}  {c.get('status')}/{c.get('effective_status')}  "
              f"budget={from_minor(c.get('daily_budget')) or '-'}  {c.get('objective')}")
        for a in api_all(f"{cid}/adsets", {"fields": "id"}):
            show_adset(a["id"])
    elif args[0] == "--adsets":
        for asid in args[1].split(","):
            show_adset(asid.strip())
    else:
        built = json.load(open(args[0]))
        cid = built.get("campaign_id")
        if cid:
            c = api(cid, {"fields": "name,status,effective_status,daily_budget,objective"})
            print(f"CAMPAIGN {cid}  {c.get('name')}  {c.get('status')}/{c.get('effective_status')}  "
                  f"budget={from_minor(c.get('daily_budget')) or '-'}")
        for s in built.get("adsets", []):
            if s.get("id") and s["id"] != "DRYRUN":
                show_adset(s["id"])


if __name__ == "__main__":
    main()
