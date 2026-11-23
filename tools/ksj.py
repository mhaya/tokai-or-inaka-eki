"""国土数値情報 S12 (駅別乗降客数) を読み込み、駅(名称+座標)ごとの1日乗降客数を引けるようにする。"""
import json, math, collections
GEOJSON = "UTF-8/S12-23_NumberOfPassengers.geojson"
def _hav(a, b, c, d):
    r = math.radians; x = math.sin(r(c - a) / 2) ** 2 + math.cos(r(a)) * math.cos(r(c)) * math.sin(r(d - b) / 2) ** 2
    return 12742 * math.asin(math.sqrt(x))
def load_pax(dir_):
    """返り値: pax(e) -> 同名駅グループ(複数事業者の乗換駅を含む)の合計1日乗降客数 or None"""
    K = []
    for f in json.load(open(f"{dir_}/{GEOJSON}", encoding="utf-8"))["features"]:
        p = f["properties"]; co = f["geometry"]["coordinates"]
        while isinstance(co[0], list): co = co[len(co) // 2] if isinstance(co[0][0], list) else co[0]
        v = None
        for k in range(11, -1, -1):  # 12年分(2011-2022)から新しい順に有効値を採用。項目は4つ1組 [有無,備考,備考,乗降客数]
            b = 9 + 4 * k; val = p.get(f"S12_{b:03d}")
            if val and val > 0 and p.get(f"S12_{b - 3:03d}") == 1: v = val; break
        K.append({"name": p["S12_001"], "grp": p["S12_001g"], "pax": v, "lat": co[1], "lon": co[0]})
    grp = collections.defaultdict(float); byname = collections.defaultdict(list)
    for k in K:
        if k["pax"]: grp[k["grp"]] += k["pax"]
        byname[k["name"]].append(k)
    def pax(e):
        if not e.get("coords"): return None
        lat = sum(c[0] for c in e["coords"]) / len(e["coords"]); lon = sum(c[1] for c in e["coords"]) / len(e["coords"])
        gs = {k["grp"] for k in byname.get(e["name"], []) if _hav(lat, lon, k["lat"], k["lon"]) < 1.5}
        return (sum(grp[g] for g in gs) or None) if gs else None
    return pax
