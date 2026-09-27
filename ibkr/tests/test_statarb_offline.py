"""Offline test of the stat-arb engine on labelled synthetic data.

The series here are generated deterministically to check the maths and, in
particular, that the backtest uses no future information. They are synthetic
test fixtures, not market data.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from statarb import ols_beta, zscore, backtest, latest_signal


def approx(a, b, tol=1e-6):
    return abs(a - b) < tol


def run():
    # OLS on exact linear data recovers the coefficients.
    xs = [1, 2, 3, 4, 5]
    ys = [2 * v + 1 for v in xs]           # beta 2, alpha 1
    beta, alpha = ols_beta(xs, ys)
    assert approx(beta, 2.0) and approx(alpha, 1.0), (beta, alpha)

    # zscore of a value one sd above a simple sample.
    z = zscore(3.0, [1.0, 2.0, 3.0])       # mean 2, sample sd 1
    assert approx(z, 1.0), z

    # Build a cointegrated pair: y = 1.5 x + stationary mean-reverting spread.
    n = 400
    x = [100 + 0.1 * t + 5 * math.sin(t / 5.0) for t in range(n)]
    spread = [3 * math.sin(t / 3.0) for t in range(n)]   # mean-reverts around 0
    y = [1.5 * x[t] + spread[t] for t in range(n)]

    res = backtest(y, x, lookback=30, entry_z=1.0, exit_z=0.2)
    print("summary:", res.summary())
    assert res.trades > 0, "expected the mean-reverting spread to generate trades"
    assert res.total_pnl > 0, f"expected positive pnl on a reverting spread, got {res.total_pnl}"

    # No-lookahead: truncating the future must not change past pnl.
    full = backtest(y, x, lookback=30, entry_z=1.0, exit_z=0.2)
    trunc = backtest(y[:-1], x[:-1], lookback=30, entry_z=1.0, exit_z=0.2)
    k = len(trunc.pnl_curve)
    assert full.pnl_curve[:k] == trunc.pnl_curve, "backtest used future data (lookahead)"
    print("no-lookahead check passed: past pnl identical when future is removed")

    # latest_signal is consistent with a flat prior when the spread is stretched.
    sig = latest_signal(y[:200], x[:200], lookback=30, entry_z=1.0, exit_z=0.2, prev_target=0)
    assert sig.target in (-1, 0, 1)
    print("latest signal at t=199:", sig.target, "z=", None if sig.z is None else round(sig.z, 2))

    print("\nAll stat-arb assertions passed.")


if __name__ == "__main__":
    run()
