#!/usr/bin/env python3
"""Phase 1: scrape competitors' recent Instagram posts through Apify.

Runs apify/instagram-scraper once for every handle (one billed run), waits for
it, and writes the raw items to <run_dir>/dataset.json. The token comes from
$APIFY_TOKEN or from APIFY_TOKEN= in the skill's own .env; it is sent as a
header, never in a URL, and never printed.

  scrape.py --check                                  (read-only: is the token good?)
  scrape.py --run-dir DIR                            (handles from competitors.md)
  scrape.py --run-dir DIR --handles creator1,creator2 [--per-handle 20]
  scrape.py --run-dir DIR --dataset-id ABC123        (re-use a finished run, free)
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ENV_FILE = SKILL / ".env"
LIST_FILE = SKILL / "competitors.md"
ACTOR = "apify~instagram-scraper"
API = "https://api.apify.com/v2"


def token():
    t = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if t:
        return t.strip()
    try:
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\s*APIFY_(?:API_)?TOKEN\s*=\s*['\"]?([^'\"\s]+)", line)
            if m:
                return m.group(1)
    except OSError:
        pass
    sys.exit(f"NO_TOKEN: put APIFY_TOKEN=... in {ENV_FILE} "
             "(apify.com > Settings > API & Integrations > Personal API token).")


def call(method, path, body=None, tok=None, timeout=60):
    req = urllib.request.Request(API + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"APIFY_HTTP_{e.code}: {e.read()[:400].decode(errors='replace')}")


def handles_from_list(path, section):
    """Pull @handles out of the `## <section>` block of a markdown list."""
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.split(r"^##\s+", text, flags=re.M)
    for b in blocks[1:]:
        title, _, body = b.partition("\n")
        if title.strip().lower().startswith(section.lower()):
            return [h.lower() for h in re.findall(r"^\s*[-*]\s*@([A-Za-z0-9_.]+)", body, flags=re.M)]
    sys.exit(f"NO_SECTION: '## {section}' not found in {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir")
    ap.add_argument("--check", action="store_true", help="read-only token check, costs nothing")
    ap.add_argument("--handles", help="comma separated, @ optional")
    ap.add_argument("--list", default=str(LIST_FILE), help="markdown competitor list")
    ap.add_argument("--section", default="Instagram")
    ap.add_argument("--per-handle", type=int, default=20,
                    help="posts per profile; the extra history is the breakout baseline")
    ap.add_argument("--dataset-id", help="skip scraping, download this dataset")
    a = ap.parse_args()

    tok = token()
    if a.check:
        me = call("GET", "/users/me", tok=tok)["data"]
        print(f"token OK: Apify user {me.get('username')} (plan: {(me.get('plan') or {}).get('id', '?')})")
        return
    if not a.run_dir:
        sys.exit("give --run-dir (or --check)")

    os.makedirs(a.run_dir, exist_ok=True)
    meta = {"started": datetime.now().isoformat(timespec="seconds")}

    if a.dataset_id:
        ds = a.dataset_id
    else:
        if a.handles:
            handles = [h.strip().lstrip("@").lower() for h in a.handles.split(",") if h.strip()]
        else:
            if not Path(a.list).exists():
                sys.exit(f"NO_LIST: {a.list} does not exist. Copy competitors.example.md to it and fill it in.")
            handles = handles_from_list(a.list, a.section)
        if not handles:
            sys.exit("NO_HANDLES")
        body = {"directUrls": [f"https://www.instagram.com/{h}/" for h in handles],
                "resultsType": "posts", "resultsLimit": a.per_handle,
                "addParentData": False}
        run = call("POST", f"/acts/{ACTOR}/runs", body, tok)["data"]
        print(f"run {run['id']} started for {len(handles)} handles: {', '.join(handles)}", flush=True)
        while True:
            time.sleep(10)
            run = call("GET", f"/actor-runs/{run['id']}", tok=tok)["data"]
            if run["status"] in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break
            print(f"  {run['status']} ... {run.get('stats', {}).get('durationMillis', 0)//1000}s", flush=True)
        if run["status"] != "SUCCEEDED":
            sys.exit(f"RUN_{run['status']}: https://console.apify.com/actors/runs/{run['id']}")
        ds = run["defaultDatasetId"]
        meta.update(run_id=run["id"], cost_usd=run.get("usageTotalUsd"), handles=handles)

    items = call("GET", f"/datasets/{ds}/items?clean=true&format=json", tok=tok, timeout=180)
    items = [i for i in items if i.get("shortCode") and not i.get("error")]
    json.dump(items, open(os.path.join(a.run_dir, "dataset.json"), "w"), ensure_ascii=False, indent=1)
    meta.update(dataset_id=ds, items=len(items))
    json.dump(meta, open(os.path.join(a.run_dir, "scrape.json"), "w"), indent=1)
    per = {}
    for i in items:
        per[i.get("ownerUsername", "?")] = per.get(i.get("ownerUsername", "?"), 0) + 1
    print(f"dataset {ds}: {len(items)} posts | " + ", ".join(f"@{k} {v}" for k, v in per.items()))
    if meta.get("cost_usd") is not None:
        print(f"apify cost ${meta['cost_usd']:.3f}")
    missing = set(meta.get("handles", [])) - {k.lower() for k in per}
    if missing:
        print("NO POSTS (private, renamed or wrong handle): " + ", ".join("@" + m for m in sorted(missing)))


if __name__ == "__main__":
    main()
