"""Download dividend- and split-adjusted daily closes for the holdings in holdings.json.

Writes data/prices.json for the dashboard. Standard library only, so it runs on
GitHub Actions or any computer with Python 3.9+:

    python fetch_prices.py
"""

import json
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TAIPEI = timezone(timedelta(hours=8))
HOSTS = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]

# A one-day spike that reverts the next day by more than this is a bad tick.
SPIKE = 0.15
# A lasting one-day move bigger than this means the history before it was not
# split-adjusted, so only what follows is kept.
BREAK = 0.30


def yahoo_symbol(symbol: str) -> str:
    # Taiwan listed codes contain digits and get ".TW"; "XXXX.TWO" (OTC) and
    # letter-only tickers such as "QQQ" are passed through as written.
    if "." in symbol or not any(ch.isdigit() for ch in symbol):
        return symbol
    return f"{symbol}.TW"


def download(symbol: str) -> dict:
    now = int(time.time())
    last_error = None
    for attempt in range(4):
        host = HOSTS[attempt % len(HOSTS)]
        url = (f"https://{host}/v8/finance/chart/{yahoo_symbol(symbol)}"
               f"?period1=0&period2={now}&interval=1d&events=div%2Csplit")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.load(resp)["chart"]["result"]
            if result:
                return result[0]
            last_error = "empty result"
        except Exception as exc:  # network errors, 429, bad JSON
            last_error = exc
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{symbol}: download failed ({last_error})")


def adjusted_series(result: dict) -> list:
    stamps = result.get("timestamp") or []
    adj = result["indicators"]["adjclose"][0]["adjclose"]
    points = []
    for ts, value in zip(stamps, adj):
        if value is None or value <= 0:
            continue
        day = datetime.fromtimestamp(ts, TAIPEI).strftime("%Y-%m-%d")
        if points and points[-1][0] == day:
            points[-1] = [day, value]
        else:
            points.append([day, value])

    clean = []
    for i, (day, value) in enumerate(points):
        if 0 < i < len(points) - 1:
            a = value / points[i - 1][1] - 1
            b = value / points[i + 1][1] - 1
            if abs(a) > SPIKE and abs(b) > SPIKE and (a > 0) == (b > 0):
                continue
        clean.append([day, value])

    start = 0
    for i in range(1, len(clean)):
        if abs(clean[i][1] / clean[i - 1][1] - 1) > BREAK:
            start = i
    return [[day, round(value, 3)] for day, value in clean[start:]]


def main() -> int:
    holdings = json.loads((ROOT / "holdings.json").read_text(encoding="utf-8"))
    out = []
    for h in holdings:
        series = adjusted_series(download(h["symbol"]))
        if not series:
            raise RuntimeError(f"{h['symbol']}: no prices")
        out.append({"symbol": h["symbol"], "name": h["name"], "series": series})
        print(f"{h['symbol']} {len(series)} rows {series[0][0]}..{series[-1][0]} last {series[-1][1]}")
        time.sleep(1)

    data = {
        "updated": datetime.now(TAIPEI).isoformat(timespec="minutes"),
        "source": "Yahoo Finance adjusted close",
        "holdings": out,
    }
    target = ROOT / "data" / "prices.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {target} ({target.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
