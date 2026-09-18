#!/usr/bin/env python3
"""
Keyword in a comment -> the link in a DM (the ManyChat pattern), via Zernio.

Instagram: Zernio has a native comment-to-DM engine. We just register the rule
once (`ig-create`) and Meta's webhooks do the rest — real DM, real buttons.

YouTube: no DM system exists on YouTube at all, so the only delivery channel is
a public reply under the commenter's comment. That needs polling (`yt-run`),
because Zernio emits no comment webhook for YouTube.

TikTok: not possible. Zernio has no TikTok comment or DM support, and TikTok's
public API exposes neither. See SKILL.md.

Subcommands:
  accounts                 Show connected accounts + the profile id
  posts [--platform p]     Recent posts with comment counts + platform post ids
  ig-create <rule>         Register the Instagram comment-to-DM automation
  ig-list                  List Instagram automations + their stats
  ig-logs <automationId>   Who triggered it, and whether the DM landed
  ig-delete <automationId> Remove an automation
  yt-run [--dry-run]       Scan YouTube comments, reply to keyword matches
  yt-status                What the poller has replied to so far

Rules live in config.json next to this script. Hebrew is sent with urllib, never
curl — the shell mangles it.
"""
import argparse, json, os, random, re, sys, time, unicodedata
import urllib.request, urllib.error, urllib.parse
from datetime import datetime, timedelta, timezone

BASE = "https://zernio.com/api/v1"
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
CONFIG_PATH = os.path.join(SKILL, "config.json")
STATE_PATH = os.path.join(SKILL, "state", "yt_replied.json")

ENV_PATHS = [
    # A .env next to this skill is the one a launchd agent can actually read:
    # macOS TCC blocks background agents from external and removable volumes,
    # so a key that lives on one works by hand and fails every scheduled run.
    os.path.join(SKILL, ".env"),
    os.path.expanduser("~/.env"),
    ".env",
]


# ---------------------------------------------------------------- api plumbing

def api_key():
    if os.environ.get("LATE_API_KEY"):
        return os.environ["LATE_API_KEY"]
    for p in ENV_PATHS:
        try:
            with open(p) as f:
                for line in f:
                    if line.startswith("LATE_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except OSError:
            # Missing *or* unreadable (TCC on removable volumes) — try the next
            # one. os.path.exists() is true for a blocked path, so testing it
            # first would stop here instead of falling through.
            continue
    sys.exit(f"No LATE_API_KEY found. Looked in: {', '.join(ENV_PATHS)}")


def call(method, path, body=None, timeout=60):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        headers={
            "Authorization": f"Bearer {api_key()}",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"error": raw.decode("utf-8", "replace")[:500]}


def ok(status, data, what):
    if status >= 300:
        sys.exit(f"{what} failed [{status}]: {json.dumps(data, ensure_ascii=False)[:600]}")
    return data


# -------------------------------------------------------------- config / state

def load_config():
    if not os.path.exists(CONFIG_PATH):
        sys.exit(f"No config at {CONFIG_PATH} — copy config.example.json and fill it in.")
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


def assert_filled(body, what):
    """Refuse to make a live call while config.example.json placeholders remain.

    Without this, a fresh install posts "PUT-YOUR-PROFILE-ID-HERE" to the API and
    gets back a validation error that reads like a bug in this script rather than
    an unfinished config.
    """
    blob = json.dumps(body, ensure_ascii=False)
    for marker in ("PUT-YOUR-", "FILL-IN-LINK", "YOUR-HANDLE"):
        if marker in blob:
            sys.exit(f"Refusing to {what}: config.json still has a {marker} placeholder in it. "
                     f"Fill it in first. `accounts` prints your real ids.")


def get_rule(cfg, name):
    for r in cfg["rules"]:
        if r["name"] == name:
            return r
    sys.exit(f"No rule named {name!r}. Have: {', '.join(r['name'] for r in cfg['rules'])}")


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {"replied": {}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, STATE_PATH)


# ------------------------------------------------------------ keyword matching

_PUNCT = re.compile(r"[^\w֐-׿]+", re.UNICODE)
_NIQQUD = re.compile(r"[֑-ׇ]")


def normalize(text):
    """Fold case, strip niqqud, emoji and punctuation so 'מדריך!!' == 'מדריך'."""
    t = unicodedata.normalize("NFKC", text or "").lower()
    t = _NIQQUD.sub("", t)
    t = _PUNCT.sub(" ", t)
    return f" {' '.join(t.split())} "


def matches(text, keywords, mode):
    """mode: contains (substring, same as Zernio's Instagram engine — so
    'המדריך' still matches the keyword 'מדריך', which Hebrew prefixes demand),
    word (whole word only), exact (the whole comment is the keyword)."""
    body = normalize(text)
    for kw in keywords:
        k = normalize(kw).strip()
        if not k:
            continue
        if mode == "exact":
            if body.strip() == k:
                return kw
        elif mode == "word":
            if f" {k} " in body:
                return kw
        else:
            if k in body:
                return kw
    return None


# --------------------------------------------------------------- subcommands

def cmd_accounts(args):
    data = ok(*call("GET", "/accounts"), "accounts")
    profiles = ok(*call("GET", "/profiles"), "profiles")
    for p in profiles.get("profiles", []):
        print(f"profile  {p['name']:<10} {p['_id']}")
    accounts = data.get("accounts", data if isinstance(data, list) else [])
    for a in accounts:
        print(f"account  {a.get('platform',''):<10} {a.get('username',''):<16} {a.get('_id') or a.get('id')}")


def cmd_posts(args):
    q = {"limit": str(args.limit)}
    if args.platform:
        q["platform"] = args.platform
    data = ok(*call("GET", f"/inbox/comments?{urllib.parse.urlencode(q)}"), "list posts")
    for p in data.get("data", []):
        head = (p.get("content") or "").replace("\n", " ")[:58]
        print(f"{p['platform']:<10} {p['id']:<22} {p.get('commentCount',0):>3}c  {p.get('createdTime','')[:10]}  {head}")


# ------------------------------------------------- multi-step Instagram flow

def _send_node(node_id, cfg, message, buttons=None, card=None, x=0, y=0):
    """A webhook node that calls Zernio's own send-message endpoint.

    Workflow `send_message` nodes can only push text/media on Instagram —
    `interactive` is WhatsApp-only — so anything with buttons has to go out
    through POST /v1/inbox/conversations/{id}/messages instead.
    """
    payload = {"accountId": cfg["accounts"]["instagram"], "message": message}
    if card:
        payload["template"] = {
            "type": "generic",
            "elements": [{
                "title": card["title"],
                **({"subtitle": card["subtitle"]} if card.get("subtitle") else {}),
                **({"imageUrl": card["imageUrl"]} if card.get("imageUrl") else {}),
                "buttons": [{"type": "url", "title": card["buttonTitle"], "url": card["url"]}],
            }],
        }
    elif buttons:
        payload["buttons"] = buttons
    return {
        "id": node_id,
        "type": "webhook",
        "config": {
            "url": f"{BASE}/inbox/conversations/{{{{conversationId}}}}/messages",
            "method": "POST",
            "headers": {"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
            # bodyTemplate is a raw string, not an object — the executor
            # interpolates {{vars}} into it and posts it verbatim.
            "bodyTemplate": json.dumps(payload, ensure_ascii=False),
            "saveAs": f"sent_{node_id}",
        },
        "position": {"x": x, "y": y},
    }


def build_flow_graph(cfg, flow):
    """Step 2+ of the funnel. Step 1 (comment -> first DM) is the native
    comment automation; this picks up when its button is tapped.

    tap "I'm human" -> follow gate (2 buttons) -> tap "I followed" -> link

    There is deliberately no isFollower check in front of the gate. Zernio does
    not put that variable in the run's bag, so the condition never matched and
    every single person fell through to the gate anyway — including people who
    already followed, who then got told they weren't following. One less node,
    same behaviour.
    """
    gate, link = flow["gate"], flow["link"]
    nodes = [
        {"id": "t1", "type": "trigger",
         "config": {"triggerType": "inbound_message",
                    "keywords": flow["tap_keywords"],
                    "matchType": "contains"},
         "position": {"x": 0, "y": 0}},
        _send_node("w_gate", cfg, gate["message"], buttons=[
            {"type": "url", "title": gate["follow_button"], "url": cfg["instagram_profile_url"]},
            {"type": "postback", "title": gate["confirm_button"], "payload": "followed_ok"},
        ], x=220, y=0),
        {"id": "wait1", "type": "wait_for_reply",
         "config": {"timeoutMinutes": 1440, "saveAs": "gate_reply"},
         "position": {"x": 440, "y": 0}},
        {"id": "c2", "type": "condition",
         "config": {"rules": [{"id": "confirmed", "variable": "gate_reply",
                               "operator": "contains", "value": flow["confirm_match"]}]},
         "position": {"x": 660, "y": 0}},
        _send_node("w_link", cfg, link["message"], card=link.get("card"), x=880, y=0),
        {"id": "end_ok", "type": "end", "config": {}, "position": {"x": 1100, "y": 0}},
        {"id": "end_out", "type": "end", "config": {}, "position": {"x": 1100, "y": 160}},
    ]
    edges = [
        {"id": "e1", "source": "t1", "target": "w_gate"},
        {"id": "e2", "source": "w_gate", "target": "wait1", "sourceHandle": "success"},
        {"id": "e3", "source": "w_gate", "target": "end_out", "sourceHandle": "error"},
        {"id": "e4", "source": "wait1", "target": "c2", "sourceHandle": "reply"},
        {"id": "e5", "source": "wait1", "target": "end_out", "sourceHandle": "timeout"},
        {"id": "e6", "source": "c2", "target": "w_link", "sourceHandle": "confirmed"},
        {"id": "e7", "source": "c2", "target": "end_out", "sourceHandle": "default"},
        {"id": "e8", "source": "w_link", "target": "end_ok", "sourceHandle": "success"},
        {"id": "e9", "source": "w_link", "target": "end_out", "sourceHandle": "error"},
    ]
    return nodes, edges


def cmd_flow_create(args):
    cfg = load_config()
    flow = cfg["flows"][args.flow]
    # Same guard as yt-run: a workflow is the step that actually hands over the
    # link, so shipping one with the placeholder still in it means every person
    # who taps through the funnel gets a dead button.
    if "FILL-IN-LINK" in json.dumps(flow, ensure_ascii=False) and not args.dry_run:
        sys.exit(f"Refusing to create {args.flow!r}: it still has a FILL-IN-LINK "
                 f"placeholder. Put the real URL in config.json first.")
    nodes, edges = build_flow_graph(cfg, flow)
    body = {
        "profileId": flow.get("profileId") or cfg["profileId"],
        "accountId": flow.get("accountId") or cfg["accounts"]["instagram"],
        "platform": "instagram",
        "name": flow["name"],
        "description": flow.get("description", ""),
        "nodes": nodes,
        "edges": edges,
        "entryNodeId": "t1",
    }
    if args.dry_run:
        redacted = json.loads(json.dumps(body).replace(api_key(), "<KEY>"))
        print(json.dumps(redacted, ensure_ascii=False, indent=2))
        return
    assert_filled({k: v for k, v in body.items() if k != "nodes"}, "create this workflow")
    data = ok(*call("POST", "/workflows", body), "create workflow")
    wf = data["workflow"]
    print(f"created workflow {wf['id']}  status={wf['status']}  nodes={wf['nodeCount']}")
    if args.activate:
        ok(*call("POST", f"/workflows/{wf['id']}/activate"), "activate")
        print("activated — live")
    else:
        print("still a draft. activate with:  flow-activate " + wf["id"])


def cmd_flow_activate(args):
    ok(*call("POST", f"/workflows/{args.workflow_id}/activate"), "activate")
    print("activated")


def cmd_flow_pause(args):
    ok(*call("POST", f"/workflows/{args.workflow_id}/pause"), "pause")
    print("paused")


def cmd_flow_list(args):
    data = ok(*call("GET", "/workflows"), "list workflows")
    for w in data.get("workflows", []):
        print(f"{w['id']}  {w['status']:<7} {w['name']}  started={w.get('totalStarted',0)} "
              f"completed={w.get('totalCompleted',0)} exited={w.get('totalExited',0)}")
    if not data.get("workflows"):
        print("(none)")


def cmd_flow_runs(args):
    data = ok(*call("GET", f"/workflows/{args.workflow_id}/executions?limit={args.limit}"), "runs")
    execs = data.get("executions", [])
    if not execs:
        print("(no runs yet)")
    for e in execs:
        print(f"{e.get('createdAt','')[:19]}  {e.get('status',''):<9} node={e.get('currentNodeId','')} "
              f"conv={e.get('conversationId','')} err={e.get('lastError') or '-'}")
        if args.vars:
            print("    vars: " + json.dumps(e.get("variables", {}), ensure_ascii=False)[:400])


def cmd_flow_delete(args):
    ok(*call("DELETE", f"/workflows/{args.workflow_id}"), "delete")
    print(f"deleted {args.workflow_id}")


def cmd_ig_create(args):
    cfg = load_config()
    rule = get_rule(cfg, args.rule)
    body = {
        "profileId": rule.get("profileId") or cfg["profileId"],
        "accountId": rule.get("accountId") or cfg["accounts"]["instagram"],
        "name": rule["name"],
        # "comment" or "story_reply" — a story reply has no public surface, so
        # commentReply/variations are silently ignored by Zernio for that one.
        "trigger": rule.get("trigger", "comment"),
        "keywords": rule["keywords"],
        "matchMode": rule.get("match", "contains"),
        "dmMessage": rule["dm_message"],
        # Off by default: link tracking wraps the destination in a redirect, and
        # redirect wrappers in DMs are a spam heuristic. Opt back in per-rule with
        # "link_tracking": true if the click numbers are worth it.
        "linkTracking": rule.get("link_tracking", False),
    }
    if rule.get("buttons"):
        body["buttons"] = rule["buttons"]
    if rule.get("comment_reply"):
        body["commentReply"] = rule["comment_reply"]
    if rule.get("comment_reply_variations"):
        body["commentReplyVariations"] = rule["comment_reply_variations"]
    if rule.get("dm_message_variations"):
        body["dmMessageVariations"] = rule["dm_message_variations"]
    if args.post_id:                      # scope to one reel instead of account-wide
        body["platformPostId"] = args.post_id
    if args.dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return
    assert_filled(body, "create this automation")
    data = ok(*call("POST", "/comment-automations", body), "create automation")
    auto = data.get("automation", data)
    print(f"created  {auto.get('_id') or auto.get('id')}  scope={'post ' + args.post_id if args.post_id else 'account-wide'}")
    print(json.dumps(auto, ensure_ascii=False, indent=2)[:1200])


def cmd_ig_list(args):
    # Rules live under whichever PROFILE their accountId belongs to, and the account was
    # reconnected into a second profile. Listing only cfg['profileId'] hid every rule made
    # since 13/8 -- on 24/8 two freshly created rules looked like they had not been created
    # at all. Walk every profile the config knows about, and label the rows.
    cfg = load_config()
    profs, seen = [], set()
    for pid in [cfg.get("profileId")] + [r.get("profileId") for r in cfg.get("rules", [])]:
        if pid and pid not in seen:
            seen.add(pid); profs.append(pid)
    autos = []
    for pid in profs:
        data = ok(*call("GET", f"/comment-automations?profileId={pid}"), f"list automations ({pid})")
        for a in data.get("automations", []):
            a["_profileId"] = pid
            autos.append(a)
    if not autos:
        print("(none)")
    if len(profs) > 1:
        print(f"  note: {len(profs)} profiles scanned {profs}")
    for a in autos:
        scope = a.get("platformPostId") or "account-wide"
        s = a.get("stats", {})
        print(f"{a.get('id') or a.get('_id')}  active={a.get('isActive')}  {a.get('name')}  kw={a.get('keywords')}  "
              f"scope={scope}  triggered={s.get('triggered', 0)} sent={s.get('dmsSent', 0)} "
              f"failed={s.get('dmsFailed', 0)} clicks={s.get('linkClicks', 0)}")


def cmd_ig_logs(args):
    data = ok(*call("GET", f"/comment-automations/{args.automation_id}/logs?limit={args.limit}"), "logs")
    for log in data.get("logs", data.get("data", [])):
        who = log.get("commenterUsername") or log.get("commenterName") or "?"
        print(f"{log.get('createdAt','')[:19]}  {who:<20} {log.get('status','')}  {(log.get('commentText') or '')[:50]}")


def cmd_audit(args):
    """Safety audit. config.json drives the YouTube poller and the live Zernio
    automations drive Instagram, so the two drift silently — a rule tightened on
    one side can stay dangerous on the other. Exits non-zero if anything fails.
    """
    cfg = load_config()
    live = {a["name"]: a for a in ok(*call("GET", "/comment-automations"), "list").get("automations", [])}
    fails, warns = [], []

    for a in live.values():
        if a.get("linkTracking"):
            fails.append(f"{a['name']}: linkTracking is ON (redirect wrappers read as spam in DMs)")
        if not a.get("platformPostId") and a.get("trigger", "comment") != "story_reply":
            fails.append(f"{a['name']}: ACCOUNT-WIDE — fires on every post you've ever published")

    for r in cfg["rules"]:
        a = live.get(r["name"])
        if not a:
            warns.append(f"{r['name']}: in config.json but not live on Instagram")
            continue
        if r.get("match", "contains") != a.get("matchMode"):
            fails.append(f"{r['name']}: match drift — config/YouTube={r.get('match','contains')!r} "
                         f"vs live/Instagram={a.get('matchMode')!r}")
        if set(r["keywords"]) != set(a.get("keywords", [])):
            warns.append(f"{r['name']}: keyword drift — config={r['keywords']} live={a.get('keywords')}")
        # A short keyword matched as a substring will collide with real words.
        if r.get("match", "contains") == "contains":
            for kw in r["keywords"]:
                if len(kw.strip()) <= 4:
                    fails.append(f"{r['name']}: {kw!r} is contains-matched and only "
                                 f"{len(kw.strip())} chars — will fire inside unrelated words")

    for name in ("yt_replied.json",):
        pass
    state = load_state()
    today = datetime.now(timezone.utc).date().isoformat()
    used = sum(1 for v in state["replied"].values() if (v.get("at") or "").startswith(today))
    print(f"YouTube budget today: {used}/{args.daily_max}")

    for f in fails:
        print(f"  FAIL  {f}")
    for w in warns:
        print(f"  warn  {w}")
    if not fails:
        print(f"  PASS  {len(live)} automations, {len(cfg['rules'])} config rules — no safety issues")
    sys.exit(1 if fails else 0)


def cmd_ig_delete(args):
    ok(*call("DELETE", f"/comment-automations/{args.automation_id}"), "delete")
    print(f"deleted {args.automation_id}")


# ------------------------------------------------------------- youtube poller

def yt_comments(post_id, account_id, max_pages=5):
    out, cursor = [], None
    for _ in range(max_pages):
        q = {"accountId": account_id, "limit": "100"}
        if cursor:
            q["cursor"] = cursor
        status, data = call("GET", f"/inbox/comments/{post_id}?{urllib.parse.urlencode(q)}")
        if status >= 300:
            print(f"  ! cannot read comments on {post_id} [{status}]: "
                  f"{json.dumps(data, ensure_ascii=False)[:200]}")
            return out
        out.extend(data.get("comments", data.get("data", [])))
        page = data.get("pagination", {})
        if not page.get("hasMore"):
            break
        cursor = page.get("cursor") or page.get("nextCursor")
        if not cursor:
            break
    return out


def already_answered(comment):
    """True if we (the channel owner) already replied under this comment."""
    for r in comment.get("replies") or []:
        if (r.get("from") or {}).get("isOwner"):
            return True
    return False


def cmd_yt_run(args):
    cfg = load_config()
    account_id = cfg["accounts"]["youtube"]
    rules = [r for r in cfg["rules"] if "youtube" in r.get("platforms", ["youtube"])]
    if not rules:
        sys.exit("No rule targets youtube.")
    unfilled = [r["name"] for r in rules if "FILL-IN-LINK" in r.get("youtube_reply", "")]
    if unfilled and not args.dry_run:
        sys.exit(f"Refusing to post: {', '.join(unfilled)} still has a FILL-IN-LINK placeholder. "
                 f"YouTube replies are public — put the real URL in config.json first.")
    state = load_state()
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)

    # Daily ceiling. The per-run cap alone bounds nothing over a day: at one run
    # every 15 min, --max 5 still permits ~480 public link-bearing replies in 24h,
    # which is exactly the burst shape YouTube's spam systems act on. Counted from
    # the state file so it survives restarts and holds across every run of the day.
    today = datetime.now(timezone.utc).date().isoformat()
    today_count = sum(1 for v in state["replied"].values()
                      if (v.get("at") or "").startswith(today))
    if today_count >= args.daily_max:
        print(f"daily cap reached ({today_count}/{args.daily_max}) — nothing sent")
        return
    print(f"budget: {today_count}/{args.daily_max} replies used today")

    posts = ok(*call("GET", f"/inbox/comments?platform=youtube&limit={args.posts}"), "list posts").get("data", [])
    sent = 0
    for p in posts:
        try:
            created = datetime.fromisoformat(p["createdTime"].replace("Z", "+00:00"))
        except Exception:
            created = datetime.now(timezone.utc)
        if created < cutoff or not p.get("commentCount"):
            continue
        for c in yt_comments(p["id"], account_id):
            cid = c.get("id")
            if not cid or cid in state["replied"]:
                continue
            if (c.get("from") or {}).get("isOwner"):
                continue
            if already_answered(c) and not args.redo:
                # Don't persist the skip during a dry run — doing so silently
                # consumes comments the caller was only previewing.
                if not args.dry_run:
                    state["replied"][cid] = {"status": "pre-existing-reply"}
                continue
            rule = next((r for r in rules if matches(c.get("message"), r["keywords"], r.get("match", "contains"))), None)
            if not rule:
                continue
            # Only answer comments that are actually *asking* for the link. On
            # YouTube we scan every comment on the video, so a bare keyword match
            # also catches people merely discussing the topic — including jokes
            # ("זה רק אני או שאתה AI"), complaints and critiques. Auto-replying to
            # those with a promo link is what earns spam reports, which is the
            # real route to a channel strike. Measured 2026-08-11: a 2-word gate
            # keeps all 170 genuine requests and drops all 21 conversational ones.
            if len(normalize(c.get("message")).strip().split()) > args.max_words:
                continue
            hit = matches(c.get("message"), rule["keywords"], rule.get("match", "contains"))
            who = (c.get("from") or {}).get("name", "?")
            # rotate wording — YouTube flags a run of identical replies as spam
            variants = [rule["youtube_reply"]] + rule.get("youtube_reply_variations", [])
            reply = variants[abs(hash(cid)) % len(variants)]
            print(f"  match [{rule['name']}/{hit}] {who}: {(c.get('message') or '')[:50]}")
            if args.dry_run:
                print(f"    would reply: {reply[:80]}")
                continue
            if sent >= args.max:
                print("  ! per-run cap reached, stopping")
                save_state(state)
                return
            if today_count + sent >= args.daily_max:
                print(f"  ! daily cap reached ({args.daily_max}), stopping")
                save_state(state)
                return
            status, data = call("POST", f"/inbox/comments/{p['id']}",
                                {"accountId": account_id, "message": reply, "commentId": cid})
            if status < 300:
                state["replied"][cid] = {
                    "rule": rule["name"], "at": datetime.now(timezone.utc).isoformat(),
                    "post": p["id"], "who": who,
                }
                sent += 1
                print("    replied ✓")
                save_state(state)
                # Jittered, not fixed: a metronomic 2s gap is itself a bot
                # signature, and the old setting let a run land 20 near-identical
                # link replies inside a minute.
                time.sleep(random.uniform(8, 20))
            else:
                print(f"    ! reply failed [{status}]: {json.dumps(data, ensure_ascii=False)[:200]}")
    save_state(state)
    print(f"done — {sent} repl{'y' if sent == 1 else 'ies'} sent"
          f"{' (dry run)' if args.dry_run else ''}")


def cmd_yt_status(args):
    state = load_state()
    rows = sorted(state["replied"].items(), key=lambda kv: kv[1].get("at", ""), reverse=True)
    print(f"{len(rows)} comments handled")
    for cid, meta in rows[:args.limit]:
        print(f"  {meta.get('at','')[:19]}  {meta.get('rule','-'):<14} {meta.get('who','-')}")


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("accounts").set_defaults(fn=cmd_accounts)

    p = sub.add_parser("posts")
    p.add_argument("--platform", choices=["instagram", "youtube", "facebook", "threads"])
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(fn=cmd_posts)

    p = sub.add_parser("ig-create")
    p.add_argument("rule")
    p.add_argument("--post-id", help="platform post id — scope to one reel (default: account-wide)")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_ig_create)

    sub.add_parser("ig-list").set_defaults(fn=cmd_ig_list)

    p = sub.add_parser("audit", help="safety audit: config vs live, scoping, link tracking")
    p.add_argument("--daily-max", type=int, default=60)
    p.set_defaults(fn=cmd_audit)

    p = sub.add_parser("ig-logs")
    p.add_argument("automation_id")
    p.add_argument("--limit", type=int, default=25)
    p.set_defaults(fn=cmd_ig_logs)

    p = sub.add_parser("ig-delete")
    p.add_argument("automation_id")
    p.set_defaults(fn=cmd_ig_delete)

    p = sub.add_parser("flow-create")
    p.add_argument("flow")
    p.add_argument("--activate", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_flow_create)

    p = sub.add_parser("flow-activate"); p.add_argument("workflow_id"); p.set_defaults(fn=cmd_flow_activate)
    p = sub.add_parser("flow-pause"); p.add_argument("workflow_id"); p.set_defaults(fn=cmd_flow_pause)
    p = sub.add_parser("flow-delete"); p.add_argument("workflow_id"); p.set_defaults(fn=cmd_flow_delete)
    sub.add_parser("flow-list").set_defaults(fn=cmd_flow_list)

    p = sub.add_parser("flow-runs")
    p.add_argument("workflow_id")
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--vars", action="store_true", help="dump each run's variable bag")
    p.set_defaults(fn=cmd_flow_runs)

    p = sub.add_parser("yt-run")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--days", type=int, default=30, help="only scan videos posted in the last N days")
    p.add_argument("--posts", type=int, default=25, help="how many recent videos to scan")
    p.add_argument("--max", type=int, default=5, help="max replies per run")
    p.add_argument("--daily-max", type=int, default=60,
                   help="hard ceiling on replies per UTC day, counted from state")
    p.add_argument("--max-words", type=int, default=2,
                   help="only reply to comments this short — a bare keyword is a "
                        "request, a sentence is conversation (default 2)")
    p.add_argument("--redo", action="store_true",
                   help="reply even to comments that already carry an owner reply. "
                        "Use to re-answer people who got an earlier, wrong reply — "
                        "it posts a SECOND reply under each, so clear their state first.")
    p.set_defaults(fn=cmd_yt_run)

    p = sub.add_parser("yt-status")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(fn=cmd_yt_status)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
