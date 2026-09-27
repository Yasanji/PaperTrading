"""Run the stat-arb backtest on two price CSVs.

Each CSV needs a header with a date column and a close column. The two files
are inner-joined on date, so they must share a date format.

    python statarb_backtest.py y.csv x.csv

Edit the CONFIG block for the lookback and z thresholds. Nothing is assumed:
the stats printed are computed from the prices in your files.
"""

import sys

from data import load_csv, align
from statarb import backtest, latest_signal

# --- CONFIG ---------------------------------------------------------------
LOOKBACK = 60            # rolling window for the hedge ratio and z-score
ENTRY_Z = 2.0            # enter when |z| is at least this
EXIT_Z = 0.5             # exit when |z| falls back to this
FEE_PER_SWITCH = 0.0     # cost charged when the position changes, in spread units
DATE_COL = "date"
PRICE_COL = "close"
# --------------------------------------------------------------------------


def main():
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python statarb_backtest.py y.csv x.csv")

    y_rows = load_csv(sys.argv[1], DATE_COL, PRICE_COL)
    x_rows = load_csv(sys.argv[2], DATE_COL, PRICE_COL)
    dates, y, x = align(y_rows, x_rows)
    if len(dates) < LOOKBACK + 2:
        raise SystemExit(f"Only {len(dates)} matched dates; need more than {LOOKBACK + 1}.")

    print(f"{len(dates)} matched dates, {dates[0]} to {dates[-1]}")
    res = backtest(y, x, LOOKBACK, ENTRY_Z, EXIT_Z, FEE_PER_SWITCH)
    s = res.summary()
    print(f"trades      {s['trades']}")
    print(f"hit rate    {s['hit_rate'] if s['hit_rate'] is None else round(s['hit_rate'], 3)}")
    print(f"total pnl   {round(s['total_pnl'], 4)}  (spread units, long 1 y vs beta x)")
    print(f"max dd      {round(s['max_drawdown'], 4)}")

    sig = latest_signal(y, x, LOOKBACK, ENTRY_Z, EXIT_Z)
    print(f"\nlatest: beta {round(sig.beta, 4)}, spread {round(sig.spread, 4)}, "
          f"z {None if sig.z is None else round(sig.z, 2)}, target {sig.target}")


if __name__ == "__main__":
    main()
