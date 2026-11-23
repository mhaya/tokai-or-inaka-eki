#!/usr/bin/env python3
"""stations.js を拡張する。
  python3 tools/build_stations.py <WIKIDATA_DIR>
- 既存の calibrated / unverified 駅は一切変更しない。
- Wikidata にあって未収録の現役駅を status='estimated'（自動推定）として追加する。
- 推定ランク: 確定基準駅(calibrated)から作った「自治体人口 × 路線数」バケットの中央値（上限7）。
  （確定データに対する検証: 平均誤差0.89 / ±1以内77%）
"""
import json, re, sys, statistics as st
from merge_wikidata import load
W = sys.argv[1]; OUT = __file__.rsplit("/tools/", 1)[0] + "/stations.js"
src = open(OUT, encoding="utf-8").read()
head = src.split("const PREFECTURE_STATIONS")[0]
D = json.loads(re.sub(r",(\s*[\]}])", r"\1", src[src.index("{"):src.rindex("}") + 1]))
for p in D: D[p] = [x for x in D[p] if x[3] != "estimated"]
M = load(W); idx = {(e["pref"], e["name"]): e for e in M}
def kind(e):
    """人口が取れない自治体を区別する: ward=東京23区・政令市の区(都市部) / town=町村 / city=人口未登録の市"""
    if e["pop"]: return "N"
    ns = e.get("cnames", set())
    if any(n.endswith("区") for n in ns): return "T" if e["pref"] == "東京都" else "O"
    if ns and all(n.endswith(("町", "村")) for n in ns): return "town"
    return "city"
def pb(e):
    k = kind(e)
    if k in ("T", "O"): return 5
    if k == "town": return 0
    if k == "city": return 2
    p = e["pop"]; return 0 if p < 20000 else 1 if p < 60000 else 2 if p < 150000 else 3 if p < 400000 else 4
def key(e):
    n = 1 if e.get("noline") else len(e["lines"])
    k = kind(e)
    return (k if k in ("T", "O") else "N", pb(e), 0 if n <= 1 else 1 if n == 2 else 2)
tab = {}
for p, rs in D.items():
    for x in rs:
        e = idx.get((p, x[0]))
        if x[3] == "calibrated" and e and not e.get("noline"): tab.setdefault(key(e), []).append(x[2])
coarse = {}
for k, v in tab.items(): coarse.setdefault((k[0], k[1]), []).extend(v)
def estimate(e):
    k = key(e); v = tab.get(k, [])
    if len(v) < 3: v = coarse.get((k[0], k[1]), []) or [5]
    r = max(1, min(7, round(st.median(v))))
    # 確定データは主要駅に偏るため、人口不明(東京23区・政令市の区)の単独路線駅は6を上限にする
    if k[0] != "N" and k[2] == 0: r = min(r, 6)
    return r
have = {(p, x[0]) for p, rs in D.items() for x in rs}
added = 0
for e in sorted(M, key=lambda e: e["name"]):
    if (e["pref"], e["name"]) in have: continue
    ls = sorted(set(e["lines"].values()))
    line = "・".join(ls[:3]) + ("ほか" if len(ls) > 3 else "") if ls else "・".join(sorted(e.get("ops", []))) or "（路線不明）"
    D[e["pref"]].append([e["name"], line, estimate(e), "estimated"]); added += 1
out = head + "const PREFECTURE_STATIONS = {\n"
for p, rs in D.items(): out += f'  "{p}": [\n' + "".join("    " + json.dumps(x, ensure_ascii=False) + ",\n" for x in rs) + "  ],\n"
open(OUT, "w", encoding="utf-8").write(out + "};\n")
print("added", added, "total", sum(len(v) for v in D.values()))
