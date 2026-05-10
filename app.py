import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, Response

app = Flask(__name__)

USER_AGENT = "SeniorRadio/1.0 (+https://seniori.org; Niksa Barlovic)"
BASE_URL = "https://radio.hrt.hr/slusaonica"
CACHE_TTL = 15 * 60
STATS_FILE = os.path.join(os.path.dirname(__file__), "stats.json")

_cache = {}


def load_stats():
    try:
        with open(STATS_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f)


def record_play(slug):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    stats = load_stats()
    stats.setdefault(slug, {})
    stats[slug]["total"] = stats[slug].get("total", 0) + 1
    stats[slug].setdefault("days", {})
    stats[slug]["days"][today] = stats[slug]["days"].get(today, 0) + 1
    save_stats(stats)


def fetch_episode(slug):
    now = time.time()
    if slug in _cache and now - _cache[slug]["ts"] < CACHE_TTL:
        return _cache[slug]["data"]

    req = urllib.request.Request(
        f"{BASE_URL}/{slug}",
        headers={
            "User-Agent": USER_AGENT,
            "Referer": "https://seniori.org/",
            "Accept-Language": "hr-HR,hr;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        html = r.read().decode("utf-8")

    m = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>', html)
    if not m:
        raise ValueError("NEXT_DATA_NOT_FOUND")

    d = json.loads(m.group(1))
    ep = d["props"]["pageProps"]["cycle"]["data"]["radioCycle"][0]["lastAvailableEpisode"]
    url = ep["audio"]["metadata"][0]["path"]
    broadcast_start = ep.get("bag", {}).get("contentItems", [{}])[0].get("broadcastStart")
    caption = ep.get("caption")

    data = {"url": url, "broadcastStart": broadcast_start, "caption": caption}
    _cache[slug] = {"data": data, "ts": now}
    return data


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/<slug>")
def api(slug):
    if slug not in ("vijesti", "dnevnik"):
        return jsonify({"error": "not found"}), 404
    try:
        resp = jsonify(fetch_episode(slug))
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    except Exception as e:
        resp = jsonify({"error": str(e)})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp, 500


@app.route("/ping/<slug>")
def ping(slug):
    if slug in ("vijesti", "dnevnik"):
        record_play(slug)
    resp = Response("", status=204)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.route("/stats")
def stats():
    data = load_stats()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    rows = ""
    total_all = 0
    for slug in ("vijesti", "dnevnik"):
        s = data.get(slug, {})
        total = s.get("total", 0)
        today_count = s.get("days", {}).get(today, 0)
        total_all += total
        rows += f"<tr><td>{slug.capitalize()}</td><td>{today_count}</td><td>{total}</td></tr>"
    html = f"""<!DOCTYPE html><html lang="hr"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Senior Radio — Statistika</title>
<style>body{{background:#0B1F4D;color:#fff;font-family:-apple-system,sans-serif;padding:32px;max-width:500px;margin:0 auto}}
h1{{font-size:24px;margin-bottom:8px}}p{{color:#8FA0C8;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:12px 16px;text-align:left;border-bottom:1px solid #2A3F7A}}
th{{color:#8FA0C8;font-weight:600;font-size:13px;text-transform:uppercase}}
td:not(:first-child){{text-align:right;font-size:20px;font-weight:700}}
.total{{margin-top:24px;color:#8FA0C8;font-size:14px}}</style></head>
<body><h1>Senior Radio</h1><p>Broj reproduciranja</p>
<table><tr><th>Emisija</th><th>Danas</th><th>Ukupno</th></tr>{rows}</table>
<p class="total">Ukupno svih emisija: {total_all}</p>
</body></html>"""
    return html


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
