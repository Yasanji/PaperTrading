# monitor: skew & term-structure monitor

The relative-value screen: the live S&P 500 surface cross-section, and where today's volatility
signals sit versus their own history. Market analytics only — it sends no orders.

## Run

```
cd vol/monitor
python monitor.py monitor.json    # fetch indices + live surface, print the signals
python make_monitor.py            # build the standalone monitor.html
open monitor.html                  # any browser (AG Grid + Plotly load from a CDN)
```

## What it shows

- **Term structure** — ATM vol by tenor today (VIX9D 9d → VIX6M 180d), with the live SPX surface
  ATM points overlaid; and the slope `VIX3M − VIX` over history. Positive = contango (calm),
  negative = backwardation (stress).
- **Skew** — the live 25-delta risk reversal (put vol − call vol) and butterfly by expiry from our
  surface; and the CBOE SKEW index over history.
- **Signals** — VIX, the term slope, and SKEW, each with its 1- and 5-year percentile and z-score,
  and a plain read (rich / cheap / normal, contango / backwardation).

## Data

Live cross-section (25d RR, butterfly, ATM) comes from `vol/` (the calibrated SPX surface).
History comes from the **CBOE VIX-complex indices** (`^VIX9D`, `^VIX`, `^VIX3M`, `^VIX6M`, `^SKEW`),
which have years of data where free option-surface history does not. So the live detail is
cross-sectional (today, every expiry) and the "vs history" context is at fixed tenors — the same
split a desk uses when it has a live surface but only index history for the long look-back.

## How it updates

Static end-of-day snapshot, rebuilt by `make_monitor.py`. The VRP daily job (`vol/vrp/update.sh`,
launchd `com.yasanji.vrp.plist`) rebuilds this monitor too, each weekday evening.

## Reading it (relative value)

A high SKEW percentile means downside protection is expensive (skew rich — consider selling it); a
low term-slope percentile (flat or inverted curve) signals stress or an event priced into the front;
a high VIX percentile means vol is elevated versus its recent range. These are starting points for
the relative-value trades the surface is built to find, not signals to trade blindly.
