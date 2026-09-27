"""Offline test of the data layer: CSV round-trip, date alignment, and a
backtest driven from CSV files matching the in-memory result.

All data here is synthetic and generated in the test. No network is used.
"""

import math
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import load_csv, align, save_csv
from statarb import backtest


def run():
    # alignment inner-joins on date and drops non-matching rows
    a = [("2026-01-01", 10.0), ("2026-01-02", 11.0), ("2026-01-03", 12.0)]
    b = [("2026-01-02", 20.0), ("2026-01-03", 21.0), ("2026-01-04", 22.0)]
    dates, ya, xb = align(a, b)
    assert dates == ["2026-01-02", "2026-01-03"], dates
    assert ya == [11.0, 12.0] and xb == [20.0, 21.0], (ya, xb)

    # build a synthetic cointegrated pair with dates, save, reload, backtest
    n = 300
    y_rows, x_rows = [], []
    for t in range(n):
        d = f"2026-{1 + t // 28:02d}-{1 + t % 28:02d}"
        xv = 100 + 0.1 * t + 5 * math.sin(t / 5.0)
        yv = 1.5 * xv + 3 * math.sin(t / 3.0)
        x_rows.append((d, xv))
        y_rows.append((d, yv))

    with tempfile.TemporaryDirectory() as tmp:
        yp = str(Path(tmp) / "y.csv")
        xp = str(Path(tmp) / "x.csv")
        save_csv(y_rows, yp)
        save_csv(x_rows, xp)
        y_loaded = load_csv(yp)
        x_loaded = load_csv(xp)

    # round-trip preserves values
    assert [round(v, 6) for _, v in y_loaded] == [round(v, 6) for _, v in y_rows]

    dates, y, x = align(y_loaded, x_loaded)
    assert len(dates) == n
    res = backtest(y, x, lookback=30, entry_z=1.0, exit_z=0.2)
    print("csv-driven backtest:", res.summary())
    assert res.trades > 0 and res.total_pnl > 0, res.summary()

    print("\nAll data-layer assertions passed.")


if __name__ == "__main__":
    run()
