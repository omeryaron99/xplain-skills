#!/usr/bin/env python3
"""Phase 2: rank the scraped posts, score breakouts, pick the winners.

breakout = post likes / that creator's median likes over every scraped,
non-pinned post (the --per-handle history from scrape.py). Only posts from the
last --days are eligible. Top --per-creator per handle, then re-ranked overall
and capped at --top. Writes selection.json and one jobs/NN-handle-code/ folder
per pick holding post.json.

  rank_and_select.py RUN_DIR [--days 7] [--per-creator 3] [--top 15] [--rank-by likes|breakout|views|comments]
"""
import argparse, json, os, shutil, statistics, sys
from datetime import datetime, timedelta, timezone


def kind(p):
    t = (p.get("type") or "").lower()
    if t == "sidecar" or p.get("childPosts"):
        return "carousel"
    if t == "video" or p.get("videoUrl"):
        return "reel"
    return "image"


def when(p):
    try:
        return datetime.fromisoformat(p["timestamp"].replace("Z", "+00:00"))
    except Exception:
        return None


def owner(p):
    """The scraped profile (inputUrl), not a collab co-author in ownerUsername."""
    u = (p.get("inputUrl") or "").rstrip("/").split("/")
    if len(u) >= 4 and "instagram.com" in u[2] and u[3] not in ("p", "reel", "reels"):
        return u[3].lower()
    return (p.get("ownerUsername") or "").lower()


def norm(p, median, n_base):
    likes = max(int(p.get("likesCount") or 0), 0)   # hidden likes come back as -1
    views = int(p.get("videoPlayCount") or p.get("videoViewCount") or 0)
    k = kind(p)
    slides = []
    if k == "carousel":
        slides = [c.get("displayUrl") for c in p.get("childPosts") or [] if c.get("displayUrl")]
        slides = slides or list(p.get("images") or [])
        videos = [c.get("videoUrl") for c in p.get("childPosts") or [] if c.get("videoUrl")]
    else:
        videos = []
    return {
        "handle": owner(p),
        "collab_with": (p.get("ownerUsername") or "").lower() if (p.get("ownerUsername") or "").lower() != owner(p) else "",
        "full_name": p.get("ownerFullName") or "",
        "shortcode": p["shortCode"],
        "url": p.get("url") or f"https://www.instagram.com/p/{p['shortCode']}/",
        "kind": k,
        "timestamp": p.get("timestamp"),
        "date": (when(p) or datetime.now(timezone.utc)).strftime("%b %-d, %Y"),
        "likes": likes,
        "comments": int(p.get("commentsCount") or 0),
        "views": views,
        "duration": p.get("videoDuration"),
        "creator_median_likes": median,
        "baseline_posts": n_base,
        "breakout": round(likes / median, 1) if median else None,
        "caption": p.get("caption") or "",
        "video_url": p.get("videoUrl") if k == "reel" else None,
        "display_url": p.get("displayUrl"),
        "slide_urls": slides[:10],
        "slide_video_urls": videos[:10],
        "music": (p.get("musicInfo") or {}).get("song_name"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--per-creator", type=int, default=3)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--rank-by", default="likes", choices=["likes", "breakout", "views", "comments"])
    a = ap.parse_args()

    items = json.load(open(os.path.join(a.run_dir, "dataset.json")))
    by_handle = {}
    for p in items:
        if p.get("shortCode"):
            by_handle.setdefault(owner(p), []).append(p)

    cutoff = datetime.now(timezone.utc) - timedelta(days=a.days)
    pool, flags = [], []
    for h, posts in by_handle.items():
        seen, uniq = set(), []
        for p in posts:
            if p["shortCode"] not in seen:
                seen.add(p["shortCode"]); uniq.append(p)
        base = [max(int(p.get("likesCount") or 0), 0) for p in uniq if not p.get("isPinned")]
        base = [b for b in base if b > 0]
        median = statistics.median(base) if base else 0
        recent = [p for p in uniq if (when(p) or cutoff) > cutoff and not p.get("isPinned")]
        if not recent:
            flags.append(f"@{h}: nothing posted in the last {a.days} days")
            continue
        if len(base) < 5:
            flags.append(f"@{h}: breakout baseline is only {len(base)} posts")
        rows = [norm(p, median, len(base)) for p in recent]
        key = lambda r: (r[a.rank_by] if a.rank_by != "breakout" else (r["breakout"] or 0))
        pool += sorted(rows, key=key, reverse=True)[: a.per_creator]

    key = lambda r: (r[a.rank_by] if a.rank_by != "breakout" else (r["breakout"] or 0))
    picks = sorted(pool, key=key, reverse=True)[: a.top]
    if not picks:
        sys.exit("NO_PICKS: no eligible posts. Widen --days or check the handles.")

    jobs = os.path.join(a.run_dir, "jobs")
    shutil.rmtree(jobs, ignore_errors=True)
    for i, r in enumerate(picks, 1):
        r["rank"] = i
        r["job"] = f"{i:02d}-{r['handle']}-{r['shortcode']}"
        os.makedirs(os.path.join(jobs, r["job"]))
        json.dump(r, open(os.path.join(jobs, r["job"], "post.json"), "w"), ensure_ascii=False, indent=1)

    sel = {"days": a.days, "rank_by": a.rank_by, "accounts": len(by_handle),
           "scraped": len(items), "picks": picks, "flags": flags,
           "built": datetime.now().isoformat(timespec="seconds")}
    json.dump(sel, open(os.path.join(a.run_dir, "selection.json"), "w"), ensure_ascii=False, indent=1)

    print(f"{len(picks)} picks from {len(by_handle)} accounts ({len(items)} posts), ranked by {a.rank_by}:")
    for r in picks:
        b = f"{r['breakout']}x" if r["breakout"] else "n/a"
        print(f"  #{r['rank']:>2} @{r['handle']:<22} {r['kind']:<8} likes {r['likes']:>7,}  breakout {b:>7}  {r['job']}")
    for f in flags:
        print("  ! " + f)


if __name__ == "__main__":
    main()
