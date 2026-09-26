#!/usr/bin/env python3
"""Phase 5: assemble the self-contained HTML report (every image embedded).

Reads selection.json, jobs/*/{post,prep,analysis}.json, frames/slides,
transcript.txt, plus pattern.txt (and optional ideas.json) written by the
orchestrator. Writes <run_dir>/report.html and prints a markdown leaderboard.

  build_report.py RUN_DIR
"""
import base64, glob, html, json, os, sys
from datetime import datetime

ACCENT = "#22A5C4"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def img64(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


def k(n):
    n = int(n or 0)
    return f"{n/1_000_000:.1f}M" if n >= 1_000_000 else f"{n:,}"


def load(path, default=None):
    try:
        return json.load(open(path, encoding="utf-8"))
    except Exception:
        return default


CSS = """
:root{--bg:#0b0d10;--card:#12161b;--line:#1f262e;--ink:#e8edf2;--mute:#8a96a3;--acc:%s;--acc2:rgba(34,165,196,.12);--hot:#ff7a45}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 Inter,Heebo,system-ui,sans-serif}
.wrap{max-width:1040px;margin:0 auto;padding:48px 20px 80px}
.eyebrow{color:var(--acc);font-size:12px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}
h1{font-size:34px;margin:6px 0 14px;letter-spacing:-.02em}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:28px}
.chip{border:1px solid var(--line);border-radius:999px;padding:4px 12px;font-size:12.5px;color:var(--mute)}
.chip b{color:var(--ink)}
.pattern{border:1px solid var(--line);border-left:3px solid var(--acc);background:var(--acc2);border-radius:12px;padding:18px 22px;margin-bottom:22px}
.label{font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);margin:14px 0 4px}
.pattern .label{color:var(--acc);margin-top:0}
.pattern p{margin:6px 0}
.lbwrap{overflow-x:auto;margin:0 0 30px}table.lb{width:100%%;border-collapse:collapse;font-size:13.5px}
.lb th,.lb td{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left}
.lb th{color:var(--mute);font-weight:600;font-size:12px}
.lb a{color:var(--ink);text-decoration:none}.lb a:hover{color:var(--acc)}
.card{display:grid;grid-template-columns:44px 300px 1fr;gap:22px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px;margin-bottom:18px}
.rank{width:40px;height:40px;border-radius:10px;background:var(--acc);color:#001018;font-weight:800;display:grid;place-items:center}
.media{position:relative}
.slider{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;border-radius:12px;background:#000;aspect-ratio:9/16;scrollbar-width:none}
.slider.sq{aspect-ratio:4/5}.slider::-webkit-scrollbar{display:none}
.slider img{flex:0 0 100%%;width:100%%;height:100%%;object-fit:cover;scroll-snap-align:start}
.count{position:absolute;top:10px;right:10px;background:rgba(0,0,0,.65);border-radius:999px;padding:2px 9px;font-size:12px}
.nav{position:absolute;top:45%%;border:0;background:rgba(0,0,0,.55);color:#fff;width:30px;height:30px;border-radius:50%%;cursor:pointer}
.nav.l{left:8px}.nav.r{right:8px}
.ig{display:block;text-align:center;margin-top:10px;padding:9px;border:1px solid var(--line);border-radius:10px;color:var(--ink);text-decoration:none;font-size:13.5px}
.ig:hover{border-color:var(--acc);color:var(--acc)}
.who{display:flex;align-items:center;gap:10px;font-weight:700;font-size:17px}
.pill{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;border:1px solid var(--line);border-radius:6px;padding:2px 7px;color:var(--mute)}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 4px}
.stat{background:#0e1216;border:1px solid var(--line);border-radius:8px;padding:3px 10px;font-size:13px}
.stat.hot{color:var(--hot);border-color:rgba(255,122,69,.35)}
.hook{font-size:19px;font-weight:700;line-height:1.35;margin:2px 0}
.ontext{color:var(--mute);font-size:13.5px}
.fmt{display:inline-block;background:var(--acc2);color:var(--acc);border:1px solid rgba(34,165,196,.35);border-radius:8px;padding:3px 10px;font-weight:600;font-size:13.5px}
.box{background:#0e1216;border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-top:12px}
.box .top{display:flex;justify-content:space-between;align-items:center}
.copy{background:none;border:0;color:var(--acc);font-weight:700;font-size:11px;letter-spacing:.1em;cursor:pointer}
.tx{max-height:150px;overflow:auto;color:#c4ccd5;font-size:13.5px;white-space:pre-wrap}
.why{border-color:rgba(34,165,196,.35);background:var(--acc2)}
.he{font-family:Heebo,Inter,sans-serif}
.flags{color:var(--hot);font-size:13px;margin-top:26px}
@media(max-width:820px){.card{grid-template-columns:1fr}.rank{position:static}.media{max-width:320px}.wrap{padding:32px 16px 60px}h1{font-size:28px}.card{padding:16px}}
""" % ACCENT

JS = """
document.querySelectorAll('.media').forEach(m=>{const s=m.querySelector('.slider'),c=m.querySelector('.count'),n=s.children.length;
const upd=()=>{c.textContent=(Math.round(s.scrollLeft/s.clientWidth)+1)+' / '+n};s.addEventListener('scroll',upd);upd();
m.querySelectorAll('.nav').forEach(b=>b.onclick=()=>s.scrollBy({left:(b.classList.contains('l')?-1:1)*s.clientWidth,behavior:'smooth'}))});
document.querySelectorAll('.copy').forEach(b=>b.onclick=()=>{navigator.clipboard.writeText(b.closest('.box').querySelector('.tx').innerText);b.textContent='COPIED';setTimeout(()=>b.textContent='COPY',1200)});
"""


def card(p, d):
    a = load(os.path.join(d, "analysis.json"), {}) or {}
    prep = load(os.path.join(d, "prep.json"), {}) or {}
    pics = sorted(glob.glob(os.path.join(d, "frame_*.jpg"))) or sorted(glob.glob(os.path.join(d, "slide_*.jpg")))
    imgs = "".join(f'<img loading="lazy" src="{img64(x)}" alt="">' for x in pics) or '<img alt="">'
    nav = '<button class="nav l">&#8249;</button><button class="nav r">&#8250;</button>' if len(pics) > 1 else ""
    tx = ""
    if os.path.exists(os.path.join(d, "transcript.txt")):
        tx = open(os.path.join(d, "transcript.txt"), encoding="utf-8").read().strip()
    if not tx and p["kind"] != "reel":
        st = a.get("slide_text")
        st = "\n".join(f"{i}. {x}" for i, x in enumerate(st, 1)) if isinstance(st, list) else st
        tx = st or p.get("caption", "")
    tx_label = "Transcript" if p["kind"] == "reel" else "Slide text / caption"
    if prep.get("music_only"):
        tx_label += " (music only, no speech)"
    stats = [f'<span class="stat">&#9829; {k(p["likes"])}</span>']
    if p.get("breakout"):
        stats.append(f'<span class="stat hot">&#128293; {p["breakout"]}&times; breakout</span>')
    stats.append(f'<span class="stat">&#128172; {k(p["comments"])}</span>')
    if p.get("views"):
        stats.append(f'<span class="stat">&#9654; {k(p["views"])}</span>')
    stats.append(f'<span class="stat">{esc(p["date"])}</span>')
    hook = a.get("hook_spoken") or a.get("hook_text") or "(analysis missing)"
    ontext = a.get("hook_text") if a.get("hook_spoken") and a.get("hook_text") else ""
    mine = a.get("your_version") or a.get("your_version_he")
    err = f'<div class="flags">prep: {esc(prep.get("error"))}</div>' if prep.get("error") else ""
    return f"""
<section class="card" id="p{p['rank']}">
  <div class="rank">#{p['rank']}</div>
  <div class="media"><div class="slider{' sq' if p['kind'] != 'reel' else ''}">{imgs}</div><span class="count"></span>{nav}
    <a class="ig" href="{esc(p['url'])}" target="_blank" rel="noopener">&#9654; View on Instagram</a></div>
  <div>
    <div class="who">@{esc(p['handle'])} <span class="pill">{esc(p['kind'])}</span></div>
    <div class="stats">{''.join(stats)}</div>
    <div class="label">Hook &middot; {esc(a.get('hook_type', 'spoken + text'))}</div>
    <div class="hook" dir="auto">{esc(hook)}</div>
    {f'<div class="ontext" dir="auto">On screen: {esc(ontext)}</div>' if ontext else ''}
    <div class="label">Format</div><span class="fmt">{esc(a.get('format', '?'))}</span>
    <div class="label">Breakdown</div><div dir="auto">{esc(a.get('breakdown', ''))}</div>
    {f'<div class="label">CTA</div><div dir="auto">{esc(a["cta"])}</div>' if a.get('cta') else ''}
    <div class="box"><div class="top"><span class="label" style="margin:0">{tx_label}</span><button class="copy">COPY</button></div>
      <div class="tx" dir="auto">{esc(tx) or '(none)'}</div></div>
    <div class="box why"><div class="label" style="margin-top:0;color:var(--acc)">Why it worked</div><div dir="auto">{esc(a.get('why_it_worked', ''))}</div></div>
    {f'<div class="box he" dir="auto"><div class="label" style="margin-top:0">Your version</div><div dir="auto">{esc(mine)}</div></div>' if mine else ''}
    {err}
  </div>
</section>"""


def main():
    run = sys.argv[1]
    sel = load(os.path.join(run, "selection.json"))
    if not sel:
        sys.exit("no selection.json; run rank_and_select.py first")
    picks = sel["picks"]
    jobs = os.path.join(run, "jobs")
    missing = [p["job"] for p in picks if not os.path.exists(os.path.join(jobs, p["job"], "analysis.json"))]

    pattern = ""
    if os.path.exists(os.path.join(run, "pattern.txt")):
        paras = [x.strip() for x in open(os.path.join(run, "pattern.txt"), encoding="utf-8").read().split("\n\n") if x.strip()]
        pattern = "".join(f'<p dir="auto">{esc(x)}</p>' for x in paras)
    ideas = load(os.path.join(run, "ideas.json"), []) or []
    ideas_html = ""
    if ideas:
        rows = "".join(f'<li dir="auto"><b>{esc(i.get("hook") or i.get("hook_he"))}</b> <span class="ontext">({esc(i.get("format"))}, from #{esc(i.get("based_on"))})</span></li>' for i in ideas)
        ideas_html = f'<div class="pattern he"><div class="label">Video ideas for you</div><ul>{rows}</ul></div>'

    lb = "".join(
        f'<tr><td>{p["rank"]}</td><td><a href="#p{p["rank"]}">@{esc(p["handle"])}</a></td><td>{esc(p["kind"])}</td>'
        f'<td>{k(p["likes"])}</td><td>{(str(p["breakout"]) + "&times;") if p.get("breakout") else "n/a"}</td>'
        f'<td dir="auto">{esc((load(os.path.join(jobs, p["job"], "analysis.json"), {}) or {}).get("hook_spoken") or (load(os.path.join(jobs, p["job"], "analysis.json"), {}) or {}).get("hook_text") or "")[:90]}</td></tr>'
        for p in picks)
    handles = len({p["handle"] for p in picks})
    date = sel.get("built", datetime.now().isoformat())[:10]
    cards = "".join(card(p, os.path.join(jobs, p["job"])) for p in picks)
    flags = "".join(f"<div>&#9888; {esc(f)}</div>" for f in sel.get("flags", []))

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>IG Competitor Research {date}</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Heebo:wght@400;600;700&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="wrap">
<div class="eyebrow">Instagram competitor research</div>
<h1>What's working in the niche</h1>
<div class="chips"><span class="chip"><b>{sel['accounts']}</b> accounts</span><span class="chip"><b>{len(picks)}</b> posts</span>
<span class="chip">last {sel['days']} days</span><span class="chip">ranked by <b>{esc(sel['rank_by'])}</b></span>
<span class="chip">&#128293; <b>breakout</b> = likes &divide; creator median</span><span class="chip">{date}</span><span class="chip">{handles} creators in picks</span></div>
{f'<div class="pattern"><div class="label">Pattern</div>{pattern}</div>' if pattern else ''}
{ideas_html}
<div class="lbwrap"><table class="lb"><tr><th>#</th><th>Handle</th><th>Format</th><th>Likes</th><th>Breakout</th><th>Hook</th></tr>{lb}</table></div>
{cards}
<div class="flags">{flags}</div>
</div><script>{JS}</script></body></html>"""
    out = os.path.join(run, "report.html")
    open(out, "w", encoding="utf-8").write(doc)
    print(f"report: {out} ({os.path.getsize(out)/1e6:.1f} MB)")
    if missing:
        print("! no analysis.json for: " + ", ".join(missing))
    print("\n| # | Handle | Format | Likes | Breakout | Hook |\n|---|---|---|---|---|---|")
    for p in picks:
        a = load(os.path.join(jobs, p["job"], "analysis.json"), {}) or {}
        b = f"{p['breakout']}x" if p.get("breakout") else "n/a"
        print(f"| {p['rank']} | @{p['handle']} | {p['kind']} | {k(p['likes'])} | {b} | {(a.get('hook_spoken') or a.get('hook_text') or '')[:70]} |")


if __name__ == "__main__":
    main()
