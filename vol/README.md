# vol: the equity volatility surface

Builds an arbitrage-free implied-volatility surface from listed option quotes, and reads
pricing, greeks and risk views off it. Method and rationale are in `VOL_SURFACE_DESIGN.md`;
this file is the run order and what each module does. Market data and analytics only — it
sends no orders.

## Run

```
cd vol
python build.py                      # today, SPY, into ../delta1/delta1.db
python build.py 2026-10-23 SPY       # a given date and underlying
python build.py --db /tmp/x.db --max-expiries 14 --no-store   # a quick scratch run
python test_synth.py                 # self-test on a known surface (no network)
```

A run fetches the chain, cleans it, implies the forward, inverts to implied vol, fits a
smile per expiry, removes calendar crossings, runs the QA gate, and stores the raw quotes,
the fitted parameters and the QA results point-in-time in `delta1.db`.

## Files, in pipeline order

| File | What it does |
| --- | --- |
| `chain.py` | Fetch the option chain and spot (Yahoo/SPY) and store it point-in-time. The only module that touches the data vendor. |
| `clean.py` | Cleaning rules: drop non-positive/crossed/wide quotes, keep OTM options, remove static-arbitrage outliers. |
| `forward.py` | Forward `F` and discount `D` per expiry from put-call parity. |
| `bs.py` | Black-76 price/vega (for inversion and pricing) and Black-Scholes spot greeks. |
| `imply.py` | Invert Black-76 to implied vol; return total variance `w = sigma^2 T` per quote. |
| `svi.py` | Fit the SVI smile per expiry, vega-weighted; butterfly (Gatheral) check; calendar repair. |
| `surface.py` | The `Surface`: `vol(K,T)`, `price`, `greeks`, ATM term structure, 25-delta risk reversal and butterfly, forward vol, and the variance-swap (VIX) replication. |
| `qa.py` | The QA gate: arbitrage-free, fit error, VIX cross-check, reprice error. |
| `build.py` | Orchestrates the pipeline for one day and stores the result. |
| `db.py`, `schema_vol.sql` | `delta1.db` access and the vol tables (append-only, every run logged). |
| `test_synth.py` | Generates prices from a known SVI surface and checks the pipeline recovers it. |

## Tables added to `delta1.db`

`option_quotes` (raw chain), `vol_forwards` (implied F, D per expiry), `vol_surface_params`
(fitted SVI parameters per expiry), `vol_surface_qa` (each run's checks), `vol_clean_log`
(how many quotes each cleaning rule removed, whole-chain and per expiry), `vol_surface_summary`
(constant-maturity 30-day ATM, variance-swap, 25d RR and BF — for the stability check). Raw
and fitted are both stored, so any day's surface rebuilds exactly.

## What a run tells you

- Per expiry: forward, ATM vol, 25-delta risk reversal (skew) and butterfly (curvature), fit error, and whether the slice is arbitrage-free.
- QA checks (stored in `vol_surface_qa`):
  - `coverage` — enough expiries and clean quotes survived (hard gate).
  - `arbitrage_free` — no butterfly or calendar violations (hard gate).
  - `fit_rmse_volpts` — per-slice model-vs-market fit error (flag above 1.5 vol pts).
  - `vix_cross_check` — surface variance-swap 30d vol vs VIX (flag above 3 vol pts).
  - `reprice_vol_error` — surface vol vs market implied vol (flag above median 1.0 / p95 3.0 vol pts).
  - `stability_dod` — day-over-day move in constant-maturity 30d vol (flag above 5 vol pts).

A note on staleness: Yahoo gives no reliable per-quote timestamp, so there is no quote-age
filter; the spread and arbitrage filters are the proxy for staleness on this feed. A vendor
feed with timestamps would add a true age check in `clean.py`.

## Known limits (see the design note, section 12)

Free Yahoo quotes are delayed and wide; SPY options are American (OTM-only limits the bias);
one snapshot a day. The method is unchanged by the data — a vendor feed or SPX drops in at
`chain.py`. For a trading mark, use a real feed.

## Plugging into the book

A nightly run (`python vol/build.py` after the US close) can sit alongside the collector.
A vol *strategy* on top of the surface (e.g. relative value against the clean surface, or a
variance/term-structure trade) would be its own dated pre-registration, after the surface is
trusted.
