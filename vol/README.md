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
(fitted SVI parameters per expiry), `vol_surface_qa` (each run's checks). Raw and fitted are
both stored, so any day's surface rebuilds exactly.

## What a run tells you

- Per expiry: forward, ATM vol, 25-delta risk reversal (skew) and butterfly (curvature), fit error, and whether the slice is arbitrage-free.
- QA: arbitrage-free (hard gate), per-slice fit error, VIX cross-check (surface variance-swap vol vs VIX), and reprice error.

## Known limits (see the design note, section 12)

Free Yahoo quotes are delayed and wide; SPY options are American (OTM-only limits the bias);
one snapshot a day. The method is unchanged by the data — a vendor feed or SPX drops in at
`chain.py`. For a trading mark, use a real feed.

## Plugging into the book

A nightly run (`python vol/build.py` after the US close) can sit alongside the collector.
A vol *strategy* on top of the surface (e.g. relative value against the clean surface, or a
variance/term-structure trade) would be its own dated pre-registration, after the surface is
trusted.
