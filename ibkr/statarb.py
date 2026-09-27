"""Systematic market-neutral relative-value (statistical arbitrage) engine.

The trade is a spread between two instruments held market-neutral: long one
leg, short a hedge ratio of the other, so the position is on the spread and not
on market direction. A rolling z-score of the spread drives entry and exit, so
it is a short-horizon mean-reversion approach.

Everything is computed point-in-time: at each step the hedge ratio and the
z-score statistics use only data strictly before that step, so there is no
lookahead. Pure Python, no dependencies.

The engine is asset-agnostic. It works for two index futures, a calendar
spread, or any two aligned price series you choose. It outputs beta-neutral
target legs that map onto the existing pair and risk rules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def ols_beta(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Simple linear regression ys = alpha + beta * xs. Returns (beta, alpha).

    beta = cov(x, y) / var(x). Raises if x has no variance or lengths differ."""
    n = len(xs)
    if n < 2 or n != len(ys):
        raise ValueError("need two aligned series of length >= 2")
    mx = sum(xs) / n
    my = sum(ys) / n
    var_x = sum((x - mx) ** 2 for x in xs)
    if var_x == 0:
        raise ValueError("x has zero variance; hedge ratio undefined")
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    beta = cov / var_x
    alpha = my - beta * mx
    return beta, alpha


def zscore(value: float, sample: list[float]) -> float | None:
    """Z-score of value against a sample's mean and standard deviation.
    Returns None when the sample has no spread to measure against."""
    n = len(sample)
    if n < 2:
        return None
    m = sum(sample) / n
    var = sum((s - m) ** 2 for s in sample) / (n - 1)
    sd = math.sqrt(var)
    if sd == 0:
        return None
    return (value - m) / sd


@dataclass
class Signal:
    index: int
    beta: float          # hedge ratio used, from data before this step
    spread: float        # y - beta * x at this step
    z: float | None      # z-score of the spread against the prior window
    target: int          # +1 long spread, -1 short spread, 0 flat


def latest_signal(y: list[float], x: list[float], lookback: int,
                  entry_z: float, exit_z: float, prev_target: int = 0) -> Signal:
    """Signal for the most recent point, using only the trailing window.

    y and x are aligned price series ending at the point to decide. The hedge
    ratio and the z statistics come from the window before the last point, so
    the decision uses no information from the point itself beyond its price.
    """
    if len(y) != len(x):
        raise ValueError("y and x must be the same length")
    if len(y) < lookback + 1:
        raise ValueError(f"need at least lookback+1 ({lookback + 1}) points")

    win_y = y[-(lookback + 1):-1]
    win_x = x[-(lookback + 1):-1]
    beta, _ = ols_beta(win_x, win_y)
    window_spread = [wy - beta * wx for wy, wx in zip(win_y, win_x)]
    spread_now = y[-1] - beta * x[-1]
    z = zscore(spread_now, window_spread)

    target = prev_target
    if z is not None:
        if prev_target == 0:
            if z >= entry_z:
                target = -1          # spread rich, short it
            elif z <= -entry_z:
                target = 1           # spread cheap, long it
        else:
            if abs(z) <= exit_z:
                target = 0           # reverted, close
            elif prev_target == 1 and z >= entry_z:
                target = -1          # flipped
            elif prev_target == -1 and z <= -entry_z:
                target = 1
    return Signal(len(y) - 1, beta, spread_now, z, target)


def target_legs(target: int, beta: float, y_price: float, x_price: float,
                gross_per_leg: float) -> dict:
    """Convert a spread target into beta-neutral notional legs.

    gross_per_leg is the notional you put on the y leg; the x leg is scaled by
    the hedge ratio so the pair is market-neutral. Returns notionals; convert to
    contracts with each instrument's multiplier when you place orders.
    """
    if target == 0:
        return {"y_notional": 0.0, "x_notional": 0.0}
    y_notional = target * gross_per_leg
    x_notional = -target * beta * gross_per_leg
    return {"y_notional": y_notional, "x_notional": x_notional}


@dataclass
class BacktestResult:
    steps: int
    trades: int
    wins: int
    hit_rate: float | None
    total_pnl: float
    max_drawdown: float
    pnl_curve: list[float]

    def summary(self) -> dict:
        return {
            "steps": self.steps,
            "trades": self.trades,
            "wins": self.wins,
            "hit_rate": self.hit_rate,
            "total_pnl": self.total_pnl,
            "max_drawdown": self.max_drawdown,
        }


def backtest(y: list[float], x: list[float], lookback: int,
             entry_z: float, exit_z: float, fee_per_switch: float = 0.0) -> BacktestResult:
    """Point-in-time backtest of the spread strategy.

    At each step i the hedge ratio and z come from prices strictly before i.
    The position decided at i is held into i+1 and marked on the realised move,
    using the beta fixed when the trade opened. PnL is in price units of y per
    one unit of the spread (long 1 y, short beta x); it is not currency and
    every number here is computed from the series you pass, nothing assumed.
    """
    if len(y) != len(x):
        raise ValueError("y and x must be the same length")
    n = len(y)
    if n < lookback + 2:
        raise ValueError("series too short for the lookback")

    position = 0
    entry_beta = 0.0
    trade_pnl = 0.0
    pnl_curve: list[float] = []
    cum = 0.0
    trades = 0
    wins = 0

    def close_trade(pnl: float):
        nonlocal trades, wins
        trades += 1
        if pnl > 0:
            wins += 1

    for i in range(lookback, n - 1):
        win_y = y[i - lookback:i]
        win_x = x[i - lookback:i]
        beta, _ = ols_beta(win_x, win_y)
        spread_i = y[i] - beta * x[i]
        z = zscore(spread_i, [wy - beta * wx for wy, wx in zip(win_y, win_x)])

        new_pos = position
        if z is not None:
            if position == 0:
                if z >= entry_z:
                    new_pos = -1
                elif z <= -entry_z:
                    new_pos = 1
            else:
                if abs(z) <= exit_z:
                    new_pos = 0
                elif position == 1 and z >= entry_z:
                    new_pos = -1
                elif position == -1 and z <= -entry_z:
                    new_pos = 1

        # handle transitions
        cost = 0.0
        if new_pos != position:
            if position != 0:
                close_trade(trade_pnl)
                trade_pnl = 0.0
            if new_pos != 0:
                entry_beta = beta
                cost += fee_per_switch
            if position != 0 and new_pos != 0:
                cost += fee_per_switch  # closing one and opening the other

        position = new_pos
        # mark the held position over [i, i+1] using the entry beta
        step_pnl = 0.0
        if position != 0:
            step_pnl = position * ((y[i + 1] - y[i]) - entry_beta * (x[i + 1] - x[i]))
        step_pnl -= cost
        trade_pnl += step_pnl if position != 0 else 0.0
        cum += step_pnl
        pnl_curve.append(cum)

    if position != 0:
        close_trade(trade_pnl)

    # max drawdown of the cumulative pnl curve
    peak = -float("inf")
    max_dd = 0.0
    for v in pnl_curve:
        peak = max(peak, v)
        max_dd = max(max_dd, peak - v)

    hit_rate = (wins / trades) if trades else None
    return BacktestResult(len(pnl_curve), trades, wins, hit_rate, cum, max_dd, pnl_curve)
