# skew_term: term-structure carry and the measurability of skew

Companion to the variance risk premium sleeve (`vol/vrp`). The VRP sleeve tested the *level* of
the surface; this one tests its *shape*: the term structure across expiries and the skew across
strikes. Rules are fixed in `SKEW_TERM_PREREGISTRATION.md`, committed before any result is examined.
Market analytics and backtest only, it sends no orders.

The sleeve is deliberately asymmetric, because free data supports the two halves very differently:

- **Term structure (carry):** backtestable. The VIX complex gives a long, independent history of the
  one- and three-month implied levels, so the slope has real data to run on. Tests Johnson (2017).
- **Skew (risk reversal):** a measurement, not a traded leg. A tradable 25-delta risk reversal needs
  a history of the surface's wings, which free data does not provide. The question asked is whether a
  free-data surface can even pin the risk reversal down reliably enough to trade. Tests Kozhan,
  Neuberger & Schneider (2013) only in the sense of asking whether it is measurable at all.

## Run

```
cd vol/skew_term
python backtest.py skew_term_backtest.json   # run the backtest, write the data JSON, print stats
```

## What it does

- **Carry signal:** the term-structure slope, VIX3M minus VIX. Primary construction gates the VRP
  sleeve's short-vol position to contango (slope > +1 vol pt), flat otherwise. Secondary construction
  is a variance term-structure calendar marked from the VIX/VIX3M levels.
- **Skew measurement:** on what fraction of days the free-data surface quotes both 25-delta wings
  cleanly enough (relative spread below 25% of mid, day-to-day RR jump below 3 vol pts) to put the
  trade on. A high excluded fraction is itself the result.
- **P&L attribution:** same second-order Taylor decomposition as the VRP sleeve (`pnl_attribution.py`),
  reconciling each day's P&L to theta, gamma, vega, vanna, volga and a residual.

## Files

| File | What it does |
| --- | --- |
| `SKEW_TERM_PREREGISTRATION.md` | The pre-registered design: signals, constructions, sizing, test windows, reliability gates, decision rules. Committed before any result. |
| `backtest.py` | The carry backtest and the skew measurement; greek attribution; writes the JSON. |

## Anchors

- Johnson, T. (2017). Risk premia and the VIX term structure. *JFQA* 52(6), 2461-2490.
- Kozhan, R., Neuberger, A. & Schneider, P. (2013). The skew risk premium in the equity index market. *RFS* 26(9), 2174-2203.
