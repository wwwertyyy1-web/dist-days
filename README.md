# 出貨日・停滯日

1. 建立 GitHub repo，把這個資料夾內容全部推上去。
2. 本機先跑一次：`pip install yfinance pandas && python fetch.py`，產生 `docs/data.json`，一起推上去。
3. Settings → Pages → Source 選 `Deploy from a branch`，資料夾選 `/docs`。
4. Actions 每週二到週六台灣早上 6 點自動更新；也可在 Actions 頁手動 Run workflow。

本機預覽：`cd docs && python -m http.server`，開 http://localhost:8000
