#!/usr/bin/env python3
"""駅周辺の店舗・施設・事務所ノードを OpenStreetMap(Overpass) から取得し、JSON Lines にキャッシュする。
  python3 tools/fetch_osm.py <WIKIDATA_DIR> <OUT.jsonl> [--calibrated-only] [--limit N]
- 利用規約に沿い、用途が分かる User-Agent・低頻度(既定 2.5秒間隔)・ミラー切替・取得済みはスキップ(再開可能)。
- ブラウザ偽装はしない。"""
import json, re, sys, time, random, urllib.request, urllib.parse, os
sys.path.insert(0, os.path.dirname(__file__))
from merge_wikidata import load
W, OUT = sys.argv[1], sys.argv[2]
UA = "station-urbanity-quiz-research/1.0 (non-commercial hobby project; low-rate queries)"
MIRRORS = ["https://overpass.kumi.systems/api/interpreter", "https://overpass-api.de/api/interpreter"]
RADIUS, INTERVAL = 600, 2.5
M = load(W)
src = open(os.path.join(os.path.dirname(__file__), "..", "stations.js"), encoding="utf-8").read()
D = json.loads(re.sub(r",(\s*[\]}])", r"\1", src[src.index("{"):src.rindex("}") + 1]))
want = {(p, x[0]) for p, rs in D.items() for x in rs if (x[3] == "calibrated" or "--calibrated-only" not in sys.argv)}
done = set()
if os.path.exists(OUT):
    for l in open(OUT, encoding="utf-8"): r = json.loads(l); done.add((r["pref"], r["name"]))
todo = [e for e in M if (e["pref"], e["name"]) in want and e.get("coords") and (e["pref"], e["name"]) not in done]
if "--limit" in sys.argv: todo = todo[:int(sys.argv[sys.argv.index("--limit") + 1])]
print("todo", len(todo), flush=True)
def query(lat, lon):
    a = f"(around:{RADIUS},{lat},{lon})"
    data = f"[out:json][timeout:40];(node{a}[shop];node{a}[amenity];node{a}[office];node{a}[tourism];);out skel;"
    for i in range(6):
        url = MIRRORS[i % len(MIRRORS)]
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": data}).encode(), headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=90))["elements"]
        except Exception as ex:
            print("retry", i, str(ex)[:60], flush=True); time.sleep(10 * (i + 1))
    return None
with open(OUT, "a", encoding="utf-8") as f:
    for n, e in enumerate(todo):
        lat = sum(c[0] for c in e["coords"]) / len(e["coords"]); lon = sum(c[1] for c in e["coords"]) / len(e["coords"])
        els = query(lat, lon)
        if els is None: continue
        pts = [[round(x["lat"], 5), round(x["lon"], 5)] for x in els if "lat" in x]
        f.write(json.dumps({"pref": e["pref"], "name": e["name"], "lat": lat, "lon": lon, "pts": pts}, ensure_ascii=False) + "\n"); f.flush()
        if n % 20 == 0: print(n, e["name"], len(pts), flush=True)
        time.sleep(INTERVAL + random.random())
print("done")
