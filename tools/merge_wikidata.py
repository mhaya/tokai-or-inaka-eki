"""fetch_wikidata.py の出力を結合し、(都道府県, 駅名) 単位に統合した駅リストを返す。"""
import json, re, collections
EXCLUDE_NAME = re.compile(r"(信号場|信号所|操車場|貨物|仮乗降場|臨時|保守|車両基地|検車|連絡線|分岐|一覧|地名|ナンバリング|旧|新駅|ステーション$|工場|埠頭|荷扱所|ターミナル$)")
CLOSED = {"東滝川", "抜海", "雄信内"}  # 廃駅（明示除外）
def load(W):
    L = lambda n: json.load(open(f"{W}/{n}.json"))
    A, B, C, P, D = L("A"), L("B"), L("C"), L("prefs"), L("D")
    cname = {x["c"]["value"].rsplit("/", 1)[1]: x["cname"]["value"] for x in L("E")}
    par = collections.defaultdict(list)
    for c, m in L("G"): par[c].append(m)
    lab = {x["c"]["value"].rsplit("/", 1)[1]: x["l"]["value"] for x in L("H")}
    def muni(c):
        """町丁レベルの所在地から、最も近い 区→市町村 の祖先（QID, 名称）を返す"""
        frontier, seen = [c], {c}
        for _ in range(5):
            for q in frontier:
                if lab.get(q, "").endswith(("区", "市", "町", "村")): return q, lab[q]
            frontier = [m for q in frontier for m in par.get(q, []) if m not in seen]
            seen |= set(frontier)
            if not frontier: break
        return None, None
    coord = {}
    for x in L("F"):
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", x["coord"]["value"])
        if m: coord[x["s"]["value"].rsplit("/", 1)[1]] = (float(m.group(2)), float(m.group(1)))
    qp = {v: k for k, v in P.items()}; qid = lambda u: u.rsplit("/", 1)[1]
    c2p, pop = collections.defaultdict(set), {}
    for x in C:
        c = qid(x["c"]["value"]); c2p[c].add(qp[qid(x["pref"]["value"])])
        if "pop" in x: pop[c] = max(pop.get(c, 0), float(x["pop"]["value"]))
    st = {}
    for x in A:
        s = qid(x["s"]["value"]); d = st.setdefault(s, {"name": x["name"]["value"], "cities": set()})
        if "city" in x: d["cities"].add(qid(x["city"]["value"]))
    lines = collections.defaultdict(dict)
    for x in B:
        if "lname" in x: lines[qid(x["s"]["value"])][qid(x["line"]["value"])] = x["lname"]["value"]
    ops = collections.defaultdict(set)
    for x in D: ops[qid(x["s"]["value"])].add(x["oname"]["value"])
    merged = {}
    for s, d in st.items():
        raw = re.sub(r"\s*[(（][^)）]*[)）]\s*$", "", d["name"])
        if not re.search(r"(駅|停留場|電停|停留所)$", raw): continue
        name = re.sub(r"(駅|停留場|停留所)$", "", raw)
        name = re.sub(r"^JR(北海道|東日本|東海|西日本|四国|九州)?(?=.)", "", name)
        if EXCLUDE_NAME.search(name) or name in CLOSED: continue
        if not lines.get(s) and not ops.get(s): continue
        prefs = set()
        for c in d["cities"]:
            prefs |= c2p.get(c, set())
            if c in qp: prefs.add(qp[c])
        if len(prefs) != 1: prefs = prefs if prefs else None
        if not prefs: continue
        pref = sorted(prefs)[0]
        e = merged.setdefault((pref, name), {"pref": pref, "name": name, "lines": {}, "pop": 0, "cities": set()})
        e["lines"].update(lines.get(s) or {}); e["cities"] |= d["cities"]
        if not lines.get(s): e["noline"] = True; e["ops"] = e.get("ops", set()) | ops[s]
        ms = [muni(c) for c in d["cities"]]
        e["pop"] = max([e["pop"]] + [pop.get(m, 0) for m, _ in ms if m])
        e["cnames"] = e.get("cnames", set()) | {n for _, n in ms if n}
        if s in coord: e.setdefault("coords", []).append(coord[s])
    return list(merged.values())
