"""每天抓三大指數日K（含成交量）存成 docs/data.json。
失敗時保留舊檔，不會覆蓋成空資料。"""
import json, sys, time, datetime as dt
import yfinance as yf

SYMBOLS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC"}
OUT = "docs/data.json"

def fetch(sym, tries=3):
    for k in range(tries):
        try:
            df = yf.download(sym, period="5y", auto_adjust=False, progress=False)
            if hasattr(df.columns, "get_level_values"):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=["Open", "High", "Low", "Close"])
            if len(df) > 100:
                return df
        except Exception as e:
            print(f"{sym} 第{k+1}次失敗: {e}", file=sys.stderr)
        time.sleep(5 * (k + 1))
    return None

out = {"updated": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "data": {}}
for name, sym in SYMBOLS.items():
    df = fetch(sym)
    if df is None:
        print(f"抓不到 {name}，保留舊的 data.json", file=sys.stderr)
        sys.exit(1)
    out["data"][name] = [
        {"t": d.strftime("%Y-%m-%d"), "o": round(float(r.Open), 2), "h": round(float(r.High), 2),
         "l": round(float(r.Low), 2), "c": round(float(r.Close), 2),
         "v": int(r.Volume) if r.Volume == r.Volume else 0}
        for d, r in df.iterrows()
    ]
    print(name, len(df), "筆，最新", out["data"][name][-1]["t"])

with open(OUT, "w") as f:
    json.dump(out, f, separators=(",", ":"))
