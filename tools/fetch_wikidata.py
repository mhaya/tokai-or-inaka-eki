#!/usr/bin/env python3
"""Wikidata から全国の現役駅（駅名・所在地・路線・自治体人口）を取得して OUT_DIR に保存する。
使い方: python3 tools/fetch_wikidata.py <OUT_DIR>   (query.wikidata.org への接続が必要)
"""
import json, sys, time, urllib.request, urllib.parse, os
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
CUR = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]
def q(query):
    for i in range(5):
        try:
            r = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": query}),
                headers={"Accept": "application/sparql-results+json", "User-Agent": "station-quiz-research/1.0"})
            return json.load(urllib.request.urlopen(r, timeout=175))["results"]["bindings"]
        except Exception as e:
            print("retry", str(e)[:60], flush=True); time.sleep(20)
    raise SystemExit("query failed")
def dump(name, rows): json.dump(rows, open(f"{OUT}/{name}.json", "w"), ensure_ascii=False); print(name, len(rows), flush=True)
prefs = q('SELECT ?p ?l WHERE{?p wdt:P31 wd:Q50337; wdt:P17 wd:Q17. ?p rdfs:label ?l FILTER(LANG(?l)="ja")}')
P = {r["l"]["value"]: r["p"]["value"].rsplit("/", 1)[1] for r in prefs if r["l"]["value"] in CUR}
assert len(P) == 47; json.dump(P, open(f"{OUT}/prefs.json", "w"), ensure_ascii=False)
STATION = 'wdt:P31/wdt:P279* wd:Q55488; wdt:P17 wd:Q17. FILTER NOT EXISTS{?s wdt:P576 ?d}'
dump("A", q(f'SELECT ?s ?name ?city WHERE {{ ?s {STATION} ?s rdfs:label ?name FILTER(LANG(?name)="ja") OPTIONAL{{?s wdt:P131 ?city}} }}'))
time.sleep(5)
vals = " ".join("wd:" + v for v in P.values())
dump("C", q(f'SELECT ?c ?pref ?pop WHERE {{ VALUES ?pref {{{vals}}} ?c wdt:P131+ ?pref. OPTIONAL{{?c wdt:P1082 ?pop}} }}'))
time.sleep(5)
dump("B", q(f'SELECT ?s ?line ?lname WHERE {{ ?s {STATION} ?s wdt:P81 ?line. OPTIONAL{{?line rdfs:label ?lname FILTER(LANG(?lname)="ja")}} }}'))
time.sleep(5)
# 路線(P81)が未入力の駅向けに運営会社(P137)も取得
dump("D", q(f'SELECT ?s ?oname WHERE {{ ?s {STATION} ?s wdt:P137 ?o. ?o rdfs:label ?oname FILTER(LANG(?oname)="ja") }}'))
