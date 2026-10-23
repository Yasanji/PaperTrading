# vrp: variance risk premium sleeve

Sells S&P 500 variance through a delta-hedged one-month ATM straddle, and attributes the daily
P&L to the greeks. Rules are fixed in `VRP_PREREGISTRATION.md` (committed before any result).
Market analytics and backtest only — it sends no orders.

## Run

```
cd vol/vrp
python backtest.py vrp_backtest.json    # run the backtest, write the data JSON, print stats
python make_viewer.py                   # run it and (re)build the standalone viewer.html
open viewer.html                         # standalone AG Grid app (any browser; CDN needs internet)
```

## What it does

- **Signal:** implied volatility (VIX in the backtest; the surface's 30-day variance-swap vol live) minus trailing 21-day realised S&P 500 vol. Short vol while that premium is positive.
- **Instrument:** a one-month ATM straddle, sold and **delta-hedged daily** so the position carries vol risk, not direction. Rolled monthly.
- **P&L attribution:** each day's P&L is decomposed by a second-order Taylor expansion into delta (hedged away), gamma, theta, vega, vanna, volga and a residual. `theta + gamma` is the variance risk premium: collect decay, pay for realised moves, keep the difference.

## Files

| File | What it does |
| --- | --- |
| `VRP_PREREGISTRATION.md` | The pre-registered rules: signal, instrument, sizing, risk stop, test windows, attribution method. |
| `pnl_attribution.py` | Decomposes one day's option P&L into the greeks; reconciles to the full revaluation. |
| `backtest.py` | Delta-hedged short-straddle backtest 2006-2026; greek attribution, trade blotter, current book; writes the JSON. |
| `make_viewer.py` | Runs the backtest and builds the standalone `viewer.html`. |
| `viewer_template.html` | The viewer UI (AG Grid); `__DATA__` is replaced with the backtest JSON. |
| `viewer.html` | The generated standalone app (open in a browser). |

## The viewer

Five tabs:
- **Composition** — cumulative P&L by greek, performance by window (dev / hold-out / full), worst drawdowns.
- **Book** — the current straddle legs with per-leg greeks, the net, and the delta hedge in S&P mini-futures.
- **Blotter** — every trade: straddle rolls and the daily delta hedges, with quantities and prices, most recent first.
- **Daily P&L** — the cumulative line and a row-per-day grid with the full greek breakdown, net delta and the hedge.
- **Vol Curve** — the live S&P 500 surface term structure (ATM vol, 25-delta risk reversal and butterfly).

## How it updates

The viewer is a **static end-of-day snapshot**: the data is embedded when `make_viewer.py` runs.
To refresh, re-run it (a nightly batch after the US close, alongside the book's evening chain). It
makes no live connection. Intraday marking would need the page to pull a JSON over HTTPS (polling)
or subscribe to a WebSocket feed — see the note in the handover discussion; the paper book trades
once a day, so end-of-day is the matching cadence.

## Results (recorded with the code, per the pre-registration)

Development 2006-2015: Sharpe 1.67, Newey-West t 6.9, positive in both halves (passes). Hold-out
2016-2026: Sharpe 1.52, t 5.0, positive in both halves (passes). The premium shows up as about
+$25M of theta against -$17M of gamma over the period (a net +$7.7M VRP core); vega, vanna and
volga are second-order and the residual is small. Max drawdown is the March 2020 vol spike.
Caveats as pre-registered: VIX stands in for a tradeable straddle, constant vega sizing, simplified
rates and costs, idealised daily rehedge; real naked short-vol tail risk is worse than the
delta-hedged series shown.
