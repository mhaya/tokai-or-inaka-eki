#!/usr/bin/env python3
"""国土数値情報「駅別乗降客数データ」(S12, 令和4年度=2022) をダウンロードして展開する。
  python3 tools/fetch_ksj.py <OUT_DIR>
出典: 国土数値情報（駅別乗降客数データ）（国土交通省） https://nlftp.mlit.go.jp/ksj/ — 原データはリポジトリに含めない。"""
import sys, os, urllib.request, zipfile
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
URL = "https://nlftp.mlit.go.jp/ksj/gml/data/S12/S12-23/S12-23_GML.zip"
req = urllib.request.Request(URL, headers={"User-Agent": "station-urbanity-quiz-research/1.0 (non-commercial hobby project)"})
z = f"{OUT}/S12-23_GML.zip"; open(z, "wb").write(urllib.request.urlopen(req, timeout=120).read())
zipfile.ZipFile(z).extractall(OUT); print("ok", OUT)
