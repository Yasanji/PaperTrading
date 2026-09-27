"""Price data loading and alignment for the stat-arb engine.

The default source is a CSV you control, so a backtest is fully reproducible
with no network and no dependency beyond the standard library. Two optional
sources are included: a keyless daily download, and the IBKR gateway's own
historical endpoint via ibkr.py.

A price series here is a list of (date_string, close_price) in ascending date
order. `align` inner-joins two series on date so the backtest sees matched rows.
"""

from __future__ import annotations

import csv
from pathlib import Path


def load_csv(path: str, date_col: str = "date", price_col: str = "close") -> list[tuple[str, float]]:
    """Load (date, price) rows from a CSV with a header. Rows with a blank or
    unparseable price are skipped. Result is sorted ascending by date."""
    rows: list[tuple[str, float]] = []
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        if date_col not in reader.fieldnames or price_col not in reader.fieldnames:
            raise ValueError(f"CSV must have '{date_col}' and '{price_col}' columns; "
                             f"found {reader.fieldnames}")
        for r in reader:
            raw = (r.get(price_col) or "").strip()
            if not raw:
                continue
            try:
                price = float(raw)
            except ValueError:
                continue
            rows.append((r[date_col].strip(), price))
    rows.sort(key=lambda t: t[0])
    return rows


def align(series_a: list[tuple[str, float]],
          series_b: list[tuple[str, float]]) -> tuple[list[str], list[float], list[float]]:
    """Inner-join two (date, price) series on date. Returns aligned dates, and
    the two price lists in the same order."""
    map_b = dict(series_b)
    dates, a_prices, b_prices = [], [], []
    for d, pa in series_a:
        if d in map_b:
            dates.append(d)
            a_prices.append(pa)
            b_prices.append(map_b[d])
    return dates, a_prices, b_prices


# -- optional source 1: keyless daily download -----------------------------

def fetch_stooq(symbol: str) -> list[tuple[str, float]]:
    """Download daily closes from Stooq (no key needed). Example symbols:
    'spy.us', 'qqq.us', '^spx'. Needs network. Returns (date, close) ascending.

    This is a convenience source; for a reproducible backtest, save the CSV and
    load it with load_csv instead.
    """
    import requests
    url = f"https://stooq.com/q/d/l/?s={symbol}&i=d"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    lines = resp.text.strip().splitlines()
    reader = csv.DictReader(lines)
    out = []
    for r in reader:
        if r.get("Close"):
            try:
                out.append((r["Date"], float(r["Close"])))
            except ValueError:
                continue
    out.sort(key=lambda t: t[0])
    return out


# -- optional source 2: the IBKR gateway -----------------------------------

def closes_from_history(history_response: dict) -> list[tuple[str, float]]:
    """Extract (timestamp, close) from an ibkr.history() response.

    The gateway returns bars with 't' (Unix ms) and 'c' (close). Prices may be
    scaled by a priceFactor on some contracts; this returns 'c' as given, so
    check priceFactor for your contract before relying on absolute levels.
    """
    from datetime import datetime, timezone
    bars = history_response.get("data", []) if isinstance(history_response, dict) else []
    out = []
    for b in bars:
        if b.get("t") is not None and b.get("c") is not None:
            dt = datetime.fromtimestamp(b["t"] / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
            out.append((dt, float(b["c"])))
    out.sort(key=lambda t: t[0])
    return out


def save_csv(rows: list[tuple[str, float]], path: str,
             date_col: str = "date", price_col: str = "close") -> None:
    """Save a (date, price) series to CSV so a run is reproducible later."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([date_col, price_col])
        w.writerows(rows)
