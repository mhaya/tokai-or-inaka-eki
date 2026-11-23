#!/usr/bin/env python3
"""stations.js を拡張する。
  python3 tools/build_stations.py <WIKIDATA_DIR>
- 既存の calibrated / unverified 駅は一切変更しない。
- Wikidata にあって未収録の現役駅を status='estimated'（自動推定）として追加する。
- 推定ランク: 確定基準駅(calibrated)から作った「自治体人口 × 路線数」バケットの中央値（上限7）。
  （確定データに対する検証: 平均誤差0.86 / ±1以内80% / ぴったり50%）
"""
import json, re, sys, statistics as st
from merge_wikidata import load
W = sys.argv[1]; OUT = __file__.rsplit("/tools/", 1)[0] + "/stations.js"
src = open(OUT, encoding="utf-8").read()
head = src.split("const PREFECTURE_STATIONS")[0]
D = json.loads(re.sub(r",(\s*[\]}])", r"\1", src[src.index("{"):src.rindex("}") + 1]))
for p in D: D[p] = [x for x in D[p] if x[3] != "estimated"]
M = load(W); idx = {(e["pref"], e["name"]): e for e in M}
def is_ward(e): return any(n.endswith("区") for n in e.get("cnames", ()))
def pb(e):
    """自治体規模バケット。人口不明は町村=0 / 市=2。区(都心の昼間人口が居住人口に出ない)は粗く3段階まで"""
    p = e["pop"]
    if p == 0: return 0 if e.get("cnames") and all(n.endswith(("町", "村")) for n in e["cnames"]) else 2
    b = 0 if p < 20000 else 1 if p < 60000 else 2 if p < 150000 else 3 if p < 400000 else 4
    return min(b, 2) if is_ward(e) else b
def key(e):
    n = 1 if e.get("noline") else len(e["lines"])
    ward = "T" if e["pref"] == "東京都" and is_ward(e) else "O" if is_ward(e) else "N"
    return (ward, pb(e), 0 if n <= 1 else 1 if n == 2 else 2)
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
    # 確定データは主要駅に偏るため、区(東京23区・政令市)の単独路線駅は6を上限にする
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
