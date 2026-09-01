#!/usr/bin/env python3
"""Upload creatives to a Meta ad account's asset library.

  upload_media.py <act_id> <path ...> [-o assets.json]

Accepts files and/or directories (directories are expanded, sorted naturally so
carousel card order matches filenames like 1.jpg, 2.png, 10.jpg).
Images go to /adimages (hash), videos to /advideos (resumable, then polled until
'ready' so a thumbnail exists). Re-running merges into an existing assets.json,
skipping anything already uploaded.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from meta import upload_image, upload_video, wait_for_video, err, resolve_account  # noqa: E402

IMG_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VID_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}


def natural_key(p):
    """1.jpg < 2.png < 10.jpg (plain sort would put 10 before 2)."""
    name = os.path.basename(p)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def expand(paths):
    out = []
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            for fn in os.listdir(p):
                full = os.path.join(p, fn)
                if os.path.isfile(full) and os.path.splitext(fn)[1].lower() in IMG_EXT | VID_EXT:
                    out.append(full)
        elif os.path.isfile(p):
            out.append(p)
        else:
            print(f"  !! not found: {p}")
    return sorted(out, key=natural_key)


def main():
    args = [a for a in sys.argv[1:]]
    out_path = "assets.json"
    if "-o" in args:
        i = args.index("-o")
        out_path = args[i + 1]
        del args[i:i + 2]
    if not args:
        print(__doc__); sys.exit(1)

    act = resolve_account(args[0]) if args[0].startswith("act_") else resolve_account()
    paths = expand(args[1:] if args[0].startswith("act_") else args)
    if not act:
        print("No ad account id. Pass act_<id> as the first argument."); sys.exit(1)
    if not paths:
        print("No media files found."); sys.exit(1)

    assets = {"images": {}, "videos": {}}
    if os.path.exists(out_path):
        try:
            assets = json.load(open(out_path))
            assets.setdefault("images", {}); assets.setdefault("videos", {})
        except Exception:
            pass

    print(f"Uploading {len(paths)} file(s) to {act}\n")
    pending = []
    for p in paths:
        name = os.path.basename(p)
        ext = os.path.splitext(name)[1].lower()
        size_mb = os.path.getsize(p) / 1e6
        if ext in IMG_EXT:
            if name in assets["images"]:
                print(f"  = {name} (already uploaded)"); continue
            r = upload_image(act, p)
            if "__error__" in r:
                print(f"  x {name}: {err(r)}"); continue
            assets["images"][name] = {"hash": r["hash"], "path": p}
            print(f"  + {name} ({size_mb:.1f}MB) -> hash {r['hash']}")
        elif ext in VID_EXT:
            if name in assets["videos"] and assets["videos"][name].get("thumb"):
                print(f"  = {name} (already uploaded)"); continue
            print(f"  . {name} ({size_mb:.1f}MB) uploading...")
            r = upload_video(act, p)
            if "__error__" in r:
                print(f"  x {name}: {err(r)}"); continue
            assets["videos"][name] = {"video_id": r["video_id"], "path": p}
            pending.append(name)
            print(f"  + {name} -> video_id {r['video_id']}")
        else:
            print(f"  ? {name}: unsupported extension, skipped")
        json.dump(assets, open(out_path, "w"), ensure_ascii=False, indent=1)

    if pending:
        print("\nWaiting for video processing (thumbnails)...")
        for name in pending:
            vid = assets["videos"][name]["video_id"]
            r = wait_for_video(vid)
            if "__error__" in r:
                print(f"  x {name}: {err(r)}"); continue
            assets["videos"][name]["thumb"] = r["thumb"]
            print(f"  + {name} ready")
            json.dump(assets, open(out_path, "w"), ensure_ascii=False, indent=1)

    json.dump(assets, open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"\nwrote {out_path}: {len(assets['images'])} image(s), {len(assets['videos'])} video(s)")


if __name__ == "__main__":
    main()
