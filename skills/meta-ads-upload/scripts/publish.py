#!/usr/bin/env python3
"""Flip built entities live (or back to paused, or delete them).

  publish.py built.json --activate [--campaign]
  publish.py built.json --pause
  publish.py built.json --delete            # removes ad sets created by this run
  publish.py --activate --ids 120...,120...

Ads are flipped before ad sets so nothing serves from an ad set with no live ad.
--campaign also activates the parent campaign (needed if it is still paused).
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import api, err  # noqa: E402


def set_status(entity_id, status):
    return api(entity_id, {"status": status}, method="POST")


def explain(e):
    """Surface the failure modes worth acting on."""
    s = str(e)
    if "1885648" in s or "Minimum Spend" in s:
        return ("Combined ad-set minimum spend exceeds the campaign budget. "
                "Lower/remove daily_min_spend_target (paused ad sets still count) "
                "or raise the campaign budget.")
    if "1341012" in s or "permission to access this profile" in s:
        return "The token cannot post as that Page/IG. Pick a page from `discover.py pages`."
    return None


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)

    action = ("ACTIVE" if "--activate" in args else
              "PAUSED" if "--pause" in args else
              "DELETE" if "--delete" in args else None)
    if not action:
        print(__doc__); sys.exit(1)
    do_campaign = "--campaign" in args

    ad_ids, adset_ids, campaign_id = [], [], None
    if "--ids" in args:
        adset_ids = [x for x in args[args.index("--ids") + 1].split(",") if x]
    else:
        built = json.load(open(args[0]))
        campaign_id = built.get("campaign_id")
        for s in built.get("adsets", []):
            if s.get("id") and s["id"] != "DRYRUN":
                adset_ids.append(s["id"])
            for a in s.get("ads", []):
                if a.get("id") and a["id"] != "DRYRUN":
                    ad_ids.append(a["id"])

    if action == "DELETE":
        for i in adset_ids:  # deleting an ad set removes its ads
            r = api(i, {}, method="DELETE")
            print(f"  {'x' if '__error__' in r else '-'} delete adset {i}"
                  f"{': ' + err(r) if '__error__' in r else ''}")
        return

    failed = []
    for i in ad_ids:
        r = set_status(i, action)
        ok = "__error__" not in r
        print(f"  {'+' if ok else 'x'} ad {i}{'' if ok else ': ' + err(r)}")
        if not ok:
            failed.append(err(r))
    for i in adset_ids:
        r = set_status(i, action)
        ok = "__error__" not in r
        print(f"  {'+' if ok else 'x'} adset {i}{'' if ok else ': ' + err(r)}")
        if not ok:
            failed.append(err(r))
    if do_campaign and campaign_id:
        r = set_status(campaign_id, action)
        ok = "__error__" not in r
        print(f"  {'+' if ok else 'x'} campaign {campaign_id}{'' if ok else ': ' + err(r)}")
        if not ok:
            failed.append(err(r))

    for f in failed:
        hint = explain(f)
        if hint:
            print(f"\nHINT: {hint}")
            break
    if not failed:
        print(f"\nAll set to {action}.")
        if action == "ACTIVE":
            print("New ads sit in IN_PROCESS / PENDING_REVIEW until Meta approves them.")


if __name__ == "__main__":
    main()
