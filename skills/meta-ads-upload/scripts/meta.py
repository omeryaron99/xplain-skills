"""Shared Meta Marketing API helper.

Resolves credentials, wraps Graph API calls, handles multipart + resumable uploads.
Import from the other scripts in this folder:  from meta import api, TOKEN, ...
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

API_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{API_VERSION}"

# Token locations, in priority order. Each is (file, [json paths to try]).
_TOKEN_KEYS = ["META_ADS_ACCESS_TOKEN", "META_ACCESS_TOKEN"]
_CONFIGS = [
    os.path.expanduser("~/.claude.json"),
    os.path.expanduser("~/.mcp.json"),
]


def _dig(obj, *path):
    for k in path:
        if not isinstance(obj, dict) or k not in obj:
            return None
        obj = obj[k]
    return obj


def resolve_token():
    """Find a Meta access token: env var first, then MCP server configs."""
    for k in _TOKEN_KEYS:
        if os.environ.get(k):
            return os.environ[k]
    for cfg in _CONFIGS:
        if not os.path.exists(cfg):
            continue
        try:
            data = json.load(open(cfg))
        except Exception:
            continue
        servers = data.get("mcpServers", {}) or {}
        # Any server whose env carries a Meta token (name varies: meta-ads, meta, etc.)
        for _name, spec in servers.items():
            env = (spec or {}).get("env", {}) or {}
            for k in _TOKEN_KEYS:
                if env.get(k):
                    return env[k]
    raise SystemExit(
        "No Meta access token found. Set META_ADS_ACCESS_TOKEN or configure the "
        "meta-ads MCP server (see the meta-ads-setup skill)."
    )


def resolve_account(explicit=None):
    """Return an ad account id as 'act_<digits>'. Falls back to MCP config."""
    if explicit:
        return explicit if str(explicit).startswith("act_") else f"act_{explicit}"
    for k in ("META_AD_ACCOUNT_ID", "META_ADS_ACCOUNT_ID"):
        if os.environ.get(k):
            v = os.environ[k]
            return v if v.startswith("act_") else f"act_{v}"
    for cfg in _CONFIGS:
        if not os.path.exists(cfg):
            continue
        try:
            data = json.load(open(cfg))
        except Exception:
            continue
        for _name, spec in (data.get("mcpServers", {}) or {}).items():
            env = (spec or {}).get("env", {}) or {}
            for k in ("META_AD_ACCOUNT_ID", "META_ADS_ACCOUNT_ID"):
                if env.get(k):
                    v = env[k]
                    return v if v.startswith("act_") else f"act_{v}"
    return None


TOKEN = None  # lazily set on first api() call


def _tok():
    global TOKEN
    if TOKEN is None:
        TOKEN = resolve_token()
    return TOKEN


def api(path, params=None, method="GET", raise_on_error=False):
    """Call the Graph API. Returns parsed JSON, or {'__error__': ...} on HTTP error.

    NOTE: errors are returned, not raised, so callers can inspect Meta's
    error_user_msg / error_subcode and react. Pass raise_on_error=True to hard-fail.
    """
    p = dict(params or {})
    p["access_token"] = _tok()
    url = f"{BASE}/{path}"
    if method == "POST":
        req = urllib.request.Request(url, data=urllib.parse.urlencode(p).encode())
    elif method == "DELETE":
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(p), method="DELETE")
    else:
        req = urllib.request.Request(url + "?" + urllib.parse.urlencode(p))
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        if raise_on_error:
            raise SystemExit(f"API error on {method} {path}:\n{raw}")
        try:
            return {"__error__": json.loads(raw).get("error", raw)}
        except Exception:
            return {"__error__": raw}


def api_all(path, params=None, limit_pages=50):
    """GET with pagination, returns the concatenated 'data' list."""
    p = dict(params or {})
    p.setdefault("limit", 200)
    out, page = [], 0
    r = api(path, p)
    while True:
        if "__error__" in r:
            return out if out else r
        out.extend(r.get("data", []))
        page += 1
        nxt = _dig(r, "paging", "cursors", "after")
        if not nxt or page >= limit_pages or not r.get("data"):
            return out
        p["after"] = nxt
        r = api(path, p)


def err(resp):
    """Human-readable error string, or None if the response is fine."""
    if not isinstance(resp, dict) or "__error__" not in resp:
        return None
    e = resp["__error__"]
    if isinstance(e, dict):
        return (
            f"{e.get('error_user_title') or e.get('type')}: "
            f"{e.get('error_user_msg') or e.get('message')} "
            f"(code {e.get('code')}/{e.get('error_subcode')})"
        )
    return str(e)


# ---------------------------------------------------------------- money

def to_minor(amount, currency="ILS"):
    """Meta budgets are in minor units. 100 ILS -> 10000. Zero-decimal currencies differ."""
    zero_decimal = {"JPY", "KRW", "CLP", "ISK", "VND", "HUF", "TWD"}
    if str(currency).upper() in zero_decimal:
        return int(round(float(amount)))
    return int(round(float(amount) * 100))


def from_minor(amount, currency="ILS"):
    zero_decimal = {"JPY", "KRW", "CLP", "ISK", "VND", "HUF", "TWD"}
    if amount in (None, ""):
        return None
    if str(currency).upper() in zero_decimal:
        return float(amount)
    return float(amount) / 100.0


# ---------------------------------------------------------------- uploads

def _multipart(url, fields, file_field=None, file_bytes=None, filename="chunk", timeout=900):
    boundary = uuid.uuid4().hex
    body = b""
    for k, v in fields.items():
        body += (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n"
        ).encode()
    if file_field:
        body += (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; "
            f"filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
        ).encode()
        body += file_bytes + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return {"__error__": json.loads(raw).get("error", raw)}
        except Exception:
            return {"__error__": raw}


def upload_image(account_id, path):
    """Upload one image to /adimages. Returns its hash."""
    fn = os.path.basename(path)
    with open(path, "rb") as f:
        data = f.read()
    r = _multipart(
        f"{BASE}/{account_id}/adimages",
        {"access_token": _tok()},
        file_field=fn, file_bytes=data, filename=fn,
    )
    if "__error__" in r:
        return r
    imgs = r.get("images", {})
    if not imgs:
        return {"__error__": f"no image hash returned: {r}"}
    first = list(imgs.values())[0]
    return {"hash": first["hash"], "url": first.get("url")}


def upload_video(account_id, path, verbose=True):
    """Resumable chunked upload to /advideos. Returns {'video_id': ...}.

    Required for anything over ~50MB; safe for small files too.
    """
    url = f"{BASE}/{account_id}/advideos"
    size = os.path.getsize(path)
    start = _multipart(url, {
        "access_token": _tok(), "upload_phase": "start", "file_size": str(size),
    })
    if "__error__" in start:
        return start
    sess, vid = start["upload_session_id"], start["video_id"]
    so, eo = int(start["start_offset"]), int(start["end_offset"])
    with open(path, "rb") as f:
        while so < eo:
            f.seek(so)
            chunk = f.read(eo - so)
            r = _multipart(url, {
                "access_token": _tok(), "upload_phase": "transfer",
                "upload_session_id": sess, "start_offset": str(so),
            }, file_field="video_file_chunk", file_bytes=chunk)
            if "__error__" in r:
                return r
            so, eo = int(r["start_offset"]), int(r["end_offset"])
            if verbose:
                pct = 100.0 * so / max(size, 1)
                print(f"    {os.path.basename(path)}: {pct:5.1f}%", end="\r", flush=True)
    fin = _multipart(url, {
        "access_token": _tok(), "upload_phase": "finish", "upload_session_id": sess,
    })
    if verbose:
        print(" " * 40, end="\r")
    if "__error__" in fin:
        return fin
    return {"video_id": vid}


def wait_for_video(video_id, timeout_s=900, poll_s=10, verbose=True):
    """Block until a video finishes processing; return {'status','thumb'}.

    A video must be 'ready' before an ad using it will render a thumbnail.
    """
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = api(video_id, {"fields": "status"})
        if "__error__" in r:
            return r
        st = _dig(r, "status", "video_status")
        if st == "ready":
            th = api(f"{video_id}/thumbnails", {})
            thumb = None
            for t in th.get("data", []) or []:
                if t.get("is_preferred"):
                    thumb = t["uri"]
                    break
            if not thumb and th.get("data"):
                thumb = th["data"][0]["uri"]
            return {"status": "ready", "thumb": thumb}
        if st == "error":
            return {"__error__": f"video {video_id} failed processing: {r}"}
        if verbose:
            print(f"    {video_id}: {st}...", end="\r", flush=True)
        time.sleep(poll_s)
    return {"__error__": f"timeout waiting for video {video_id}"}


# ------------------------------------------------- creative feature opt-out

# Every Advantage+ / automatic creative enhancement Meta may apply. Passing this
# as degrees_of_freedom_spec turns them all OFF, matching an ad set built with
# creative enhancements disabled in the UI.
CREATIVE_FEATURES = [
    "adapt_to_placement", "add_text_overlay", "ads_with_benefits",
    "advantage_plus_creative", "app_highlights", "audio", "biz_ai",
    "carousel_to_video", "catalog_feed_tag", "creative_stickers",
    "cv_transformation", "description_automation", "dha_optimization",
    "enable_ncs_testimonials", "enhance_cta", "feed_caption_optimization",
    "generate_cta", "hide_price", "ig_glados_feed", "ig_video_native_subtitle",
    "image_animation", "image_auto_crop", "image_background_gen",
    "image_brightness_and_contrast", "image_enhancement", "image_templates",
    "image_text_translation", "image_touchups", "image_uncrop", "inline_comment",
    "local_store_extension", "media_liquidity_animated_image", "media_order",
    "media_type_automation", "multi_photo_to_video", "pac_recomposition",
    "pac_relaxation", "product_browsing", "product_extensions",
    "product_metadata_automation", "profile_card", "replace_media_text",
    "reveal_details_over_time", "show_destination_blurbs", "show_summary",
    "site_extensions", "standard_enhancements_catalog", "text_optimizations",
    "text_translation", "translate_voiceover", "video_auto_crop",
    "video_filtering", "video_highlight", "video_highlights", "video_to_image",
    "video_uncrop", "wa_mm_image_filtering",
]


def opt_out_spec():
    return {"creative_features_spec": {k: {"enroll_status": "OPT_OUT"} for k in CREATIVE_FEATURES}}


def jdump(obj):
    return json.dumps(obj, ensure_ascii=False)
