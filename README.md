# tokai-or-inaka-eki

鉄道駅の都会度を10段階で当てるクイズアプリ。

## データと再生成
- `stations.js` … 47都道府県別の駅DB（`status`: `calibrated`=確定 / `unverified`=手動推定 / `estimated`=自動推定）
- 自動推定の再生成: `python3 tools/fetch_wikidata.py <dir>` → `python3 tools/fetch_ksj.py <ksj_dir>` → `python3 tools/build_stations.py <dir> <ksj_dir>`
- 出典: 国土数値情報（駅別乗降客数データ）（国土交通省）を加工して作成 / Wikidata（CC0）。原データはリポジトリに含めません。
