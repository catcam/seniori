import json
import re
import time
import urllib.request
from flask import Flask, jsonify, render_template

app = Flask(__name__)

USER_AGENT = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
BASE_URL = "https://radio.hrt.hr/slusaonica"
CACHE_TTL = 15 * 60  # 15 minuta

_cache = {}


def fetch_episode(slug):
    now = time.time()
    if slug in _cache and now - _cache[slug]["ts"] < CACHE_TTL:
        return _cache[slug]["data"]

    req = urllib.request.Request(
        f"{BASE_URL}/{slug}",
        headers={"User-Agent": USER_AGENT, "Accept-Language": "hr-HR,hr;q=0.9"},
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
        return jsonify(fetch_episode(slug))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
