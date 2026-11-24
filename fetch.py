"""每天抓 S&P 500 與 Nasdaq 日K（含成交量，從 2006-01-01 起；2007 年前的一年用來暖機算均線與訊號），以及現金替代標的 BOXX、BIL 的還原收盤，還有 BIL 上市前用的三個月期國庫券利率 ^IRX，存成 docs/data.json。
失敗時保留舊檔，不會覆蓋成空資料。BOXX / BIL / IRX 抓不到時仍會寫出指數資料（能沿用舊的就沿用），網頁會依現有資料計算現金報酬，都沒有時改回 0%。"""
import json, sys, time, datetime as dt, os
import yfinance as yf

SYMBOLS = {"S&P 500": "^GSPC", "Nasdaq": "^IXIC"}
CASH = {"BOXX": "BOXX", "BIL": "BIL"}  # 現金部位用還原收盤（auto_adjust）；BOXX 2022/12 上市前用 BIL
IRX = "^IRX"  # 13 週國庫券利率（年率 %）；BIL 2007/5 上市前的現金報酬
OUT = os.environ.get("DD_OUT", "docs/data.json")
START = "2006-01-01"   # 網頁從 2007-01-01 開始回測，前面一年拿來算 MA50 與訊號

def fetch(sym, tries=3, auto_adjust=False, ohlc=True, min_rows=100):
    need = ["Open", "High", "Low", "Close"] if ohlc else ["Close"]
    for k in range(tries):
        try:
            df = yf.download(sym, start=START, auto_adjust=auto_adjust, progress=False)
            if hasattr(df.columns, "get_level_values"):
                df.columns = df.columns.get_level_values(0)
            df = df.dropna(subset=need)
            if len(df) > min_rows:
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

old = {}
if os.path.exists(OUT):
    try:
        old = json.load(open(OUT)).get("data") or {}
    except Exception:
        old = {}

def keep_or_skip(name, rows=None):
    if rows is not None:
        out["data"][name] = rows
        print(name, len(rows), "筆，最新", rows[-1]["t"])
        return
    if isinstance(old.get(name), list) and len(old[name]) > 10:
        out["data"][name] = old[name]
        print(f"抓不到 {name}，沿用舊資料 {len(old[name])} 筆", file=sys.stderr)
    else:
        print(f"抓不到 {name}，略過（網頁會用剩餘的現金資料，都沒有則現金報酬改回 0%）", file=sys.stderr)

for name, sym in CASH.items():
    df = fetch(sym, auto_adjust=True, ohlc=False, min_rows=20)
    if df is None:
        keep_or_skip(name)
        continue
    keep_or_skip(name, [
        {"t": d.strftime("%Y-%m-%d"), "c": round(float(r.Close), 4)}
        for d, r in df.iterrows()
    ])

df = fetch(IRX, auto_adjust=False, ohlc=False, min_rows=20)
if df is None:
    keep_or_skip("IRX")
else:
    keep_or_skip("IRX", [
        {"t": d.strftime("%Y-%m-%d"), "c": round(float(r.Close), 4)}
        for d, r in df.iterrows()
    ])

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w") as f:
    json.dump(out, f, separators=(",", ":"))
