#!/usr/bin/env python3
"""Bind an account-wide comment rule to a post the moment Zernio publishes it.

Why this exists: a comment rule has to exist BEFORE the comments do, because the
window to answer a comment privately is counted from the comment. But a rule can
only be scoped to a post once that post has a platform post id, which does not
exist until the platform accepts the upload. Those two facts pull in opposite
directions whenever the post is scheduled rather than already live.

This closes the gap. Create the rule account-wide, start this, and it polls the
scheduled post until the id appears, then PATCHes that id onto the live
automation, converting it to post-scoped in place. The DM, the buttons, the
funnel and the stats are untouched. Only the scope changes.

Scope matters: an account-wide comment rule answers comments on every post you
have ever published, so a stranger commenting under a two-year-old reel is pulled
into an unrelated funnel. `keyword_dm.py audit` reports that as a FAIL. Comment
rules belong scoped to their post; only story_reply rules belong account-wide,
since a story has no post surface to scope to.

PATCH, never delete-and-recreate: recreating a rule resets its stats to zero and
drops its DM logs.

  python3 rescope_on_publish.py --post-id <zernioPostId> --rule my-campaign
  python3 rescope_on_publish.py --post-id <zernioPostId> --rule my-campaign --dry-run
"""
import argparse, json, os, sys, time, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keyword_dm as K


def log(msg):
    print(f"[{datetime.datetime.now():%H:%M:%S}] {msg}", flush=True)


def platform_post_id(post, platform="instagram"):
    """Zernio nests the real IG media id under the per-platform record. It is absent
    until the platform actually accepts the upload, which is the signal we wait on."""
    for p in post.get("platforms", []):
        if p.get("platform") != platform:
            continue
        for k in ("platformPostId", "postId", "externalId", "platformId"):
            if p.get(k):
                return p[k]
        for k in ("platformResponse", "response", "result"):
            v = p.get(k) or {}
            if isinstance(v, dict) and v.get("id"):
                return v["id"]
    return None


def live_automation(profile_id, name):
    d = K.ok(*K.call("GET", f"/comment-automations?profileId={profile_id}"), "list automations")
    for a in d.get("automations", []):
        if a.get("name") == name:
            return a
    return None


def rescope(rule, auto, post_id, dry_run):
    """PATCH platformPostId onto the live rule.

    NOT delete-and-recreate: comment automations accept PATCH for keywords,
    matchMode, linkTracking and platformPostId, and the stats survive it. A
    delete+create resets triggered/dmsSent to zero, throws away the logs that are
    the only record of who was already DM'd, and opens a window with no rule at
    all on the reel's busiest minutes.
    """
    auto_id = auto.get("id") or auto.get("_id")
    body = {"platformPostId": post_id}
    if dry_run:
        log(f"DRY RUN — would PATCH {auto_id} with {json.dumps(body)}")
        return
    K.ok(*K.call("PATCH", f"/comment-automations/{auto_id}", body), "scope automation to post")
    check = live_automation(rule.get("profileId"), rule["name"])
    got = (check or {}).get("platformPostId")
    if got != post_id:
        sys.exit(f"PATCH reported success but scope is {got!r}, expected {post_id!r} — FIX BY HAND")
    log(f"scoped {auto_id} to post {post_id} (stats preserved: "
        f"{(check.get('stats') or {}).get('triggered', 0)} triggered)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post-id", required=True, help="Zernio scheduled post id")
    ap.add_argument("--rule", required=True, help="rule name in config.json")
    ap.add_argument("--platform", default="instagram")
    ap.add_argument("--timeout", type=int, default=5400, help="seconds to keep polling")
    ap.add_argument("--interval", type=int, default=20)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = K.load_config()
    rule = K.get_rule(cfg, args.rule)
    profile_id = rule.get("profileId") or cfg["profileId"]

    auto = live_automation(profile_id, args.rule)
    if not auto:
        sys.exit(f"no live automation named {args.rule!r} on profile {profile_id}")
    if auto.get("platformPostId"):
        log(f"already scoped to {auto['platformPostId']} — nothing to do")
        return

    log(f"watching post {args.post_id} for its {args.platform} media id…")
    end = time.time() + args.timeout
    while time.time() < end:
        d = K.ok(*K.call("GET", f"/posts/{args.post_id}"), "get post")
        post = d.get("post", d)
        pid = platform_post_id(post, args.platform)
        if pid:
            log(f"published — {args.platform} media id {pid}")
            rescope(rule, auto, pid, args.dry_run)
            return
        # poll lazily until the fire time is close, then tighten: every second between
        # publish and rescope is a comment the account-wide rule has to cover alone
        due = post.get("scheduledFor") or ""
        gap = None
        if due:
            try:
                t = datetime.datetime.fromisoformat(due.replace("Z", "+00:00"))
                gap = (t - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
            except ValueError:
                gap = None
        time.sleep(120 if (gap is not None and gap > 600) else args.interval)
    sys.exit("timed out before the post published — rule is STILL account-wide, scope it by hand")


if __name__ == "__main__":
    main()
