# The equity volatility surface: data to calibration

Design note, drafted 23 October 2026. Yasanji Ratnaike. This is the specification for the `vol/` module: what it builds, from what data, under what rules. The code is written to this note, and results come after it, as for the rest of the book.

The aim is a surface you can defend end to end: every input named, every cleaning rule written down, the calibration method and its no-arbitrage constraints stated, and the outputs (implied vol at any strike and expiry, plus the risk sensitivities) checked against things that must hold. It is written so each stage can be explained on its own.

---

## 1. What a volatility surface is, and why a desk needs one

An option's price can be quoted as one number, its **Black-Scholes implied volatility**: the volatility that, put into the Black-Scholes formula, returns the option's market price. Implied vol is not constant across strikes and expiries. Plotted against strike (or log-moneyness) and time to expiry, it forms a **surface**: low-strike puts trade at higher implied vol than at-the-money options (the **skew**), and the whole smile flattens as expiry lengthens (the **term structure**).

A volatility desk needs the surface for four things, and these are the four the technology has to serve:

1. **Pricing.** Any option, including strikes and expiries that are not listed, is priced off the surface. So are the vol-sensitive parts of structured products and Delta 1 trades (variance swaps, dividend and index exposure).
2. **Risk sensitivities (the greeks).** Delta, gamma, vega and theta, and the second-order vol greeks (vanna, volga), are all read off the surface. A book's risk is expressed as vega bucketed by expiry, skew exposure and term-structure exposure.
3. **Relative value.** Mispriced strikes, a skew that is too steep, a calendar that is inverted: these are found by comparing the market to a clean, arbitrage-free surface.
4. **Marking and P&L.** The book is marked to the surface each day; the day-on-day change in the surface explains the vega P&L.

The surface is the central market-data object of the whole business. Everything upstream (the option quotes, the rates, the dividends) feeds it; everything downstream (pricing, greeks, risk, P&L) reads it. That upstream-to-downstream dependency is exactly what has to be mapped, documented and kept correct.

---

## 2. The pipeline at a glance

```
  raw option chain            clean quotes             per-expiry inputs
  (strikes, expiries,  ──►   (liquidity +      ──►    forward F(T),
   bid/ask, volume, OI)       arbitrage filters)       discount D(T)
        │                                                   │
        │                                                   ▼
        │                                            implied vol per quote
        │                                            (invert Black-Scholes
        │                                             on OTM options)
        ▼                                                   │
   underlying spot,                                         ▼
   rates, dividends  ─────────────────────────►     calibrate a smile
                                                     per expiry (SVI,
                                                     no-arbitrage constrained)
                                                            │
                                                            ▼
                                                     stitch across expiries
                                                     → arbitrage-free surface
                                                            │
                        ┌───────────────────────────────────┼───────────────┐
                        ▼                                   ▼               ▼
                 query σ(K,T)                         greeks / risk       QA checks
                 ATM term structure                   (delta, gamma,      (arb-free,
                 skew, risk reversal                   vega, vanna,        fit error,
                 butterfly                             volga; vega         VIX cross-
                                                       buckets)            check)
```

Each box is one module. The sections below are in pipeline order.

---

## 3. Input data (the upstream dependencies)

A surface is only as good as its inputs. Four data items are needed, each with its own source, latency and quality problem.

### 3.1 Option chain

The core input: for one underlying, every listed option, with
`expiry, strike, right (call/put), bid, ask, last, volume, open_interest`.

- **Default source for the paper book: Yahoo Finance option chains via `yfinance`** (`Ticker.option_chain(expiry)`), on **SPY** (the S&P 500 ETF). This is free, already installed, and enough to build and demonstrate the full pipeline. It is captured point-in-time into `delta1.db`, as with the rest of the book, so a surface can always be rebuilt as it stood on a date.
- **What the free feed costs us, and why it is still enough.** Yahoo quotes are delayed, sometimes stale, and spreads are wide away from the money. These are the *same* problems a real feed has, only larger, so the cleaning stage (section 4) is where the real learning is and it transfers directly. The pipeline is written so the source is swappable: a vendor feed (OptionMetrics/IvyDB for history, a live exchange or Bloomberg feed for intraday) drops in at `chain.py` without changing anything downstream.

### 3.2 Underlying price

The spot level of SPY, taken at the same time as the chain so the two are consistent. A surface built from a stale spot has a false skew, because moneyness is measured from the wrong centre. Consistency of timestamp between spot and chain matters more than the absolute freshness of either.

### 3.3 Interest rates

A discount curve, to present-value option payoffs and to compute forwards. For the paper book: the US Treasury par-yield curve already collected by the book, interpolated to each expiry. Precision here is second-order for short-dated equity options but must be present and documented.

### 3.4 Dividends and borrow

SPY pays dividends; its forward is below spot by the present value of dividends over the option's life, net of borrow cost. Rather than model dividends explicitly, the pipeline **implies the forward from the option prices themselves** (section 5), which captures dividends, borrow and rate in one number and avoids a separate dividend feed. This is the standard desk approach and it is self-consistent with the quotes.

### 3.5 A note on American vs European options

SPY options are **American** and the underlying pays dividends, so they carry an early-exercise premium: inverting Black-Scholes (a European formula) on them introduces a small bias, largest for deep in-the-money and longer-dated options. Three honest ways to handle it, in order of preference:

1. Use only **out-of-the-money** options (section 5), where the early-exercise premium is smallest, and accept the residual bias for short expiries.
2. Move to **SPX** index options (European, cash-settled) when a feed is available; this removes the problem entirely and is what a desk uses.
3. De-Americanize with a binomial model before inverting. Most work for least gain at this stage; noted, not done now.

The module uses option 1 and records the choice. This distinction is itself a core piece of vol-desk knowledge and a real data-requirement decision.

---

## 4. Cleaning (where a surface is made or ruined)

Raw quotes cannot be calibrated directly. The cleaning rules below are applied in order, each one logged with the count of quotes it removes, so the pipeline is auditable and the effect of each rule is visible.

1. **Drop non-positive and crossed quotes.** `bid <= 0`, `ask <= 0`, or `bid > ask` are removed. A zero bid means no one is buying; the quote carries no information.
2. **Spread filter.** Remove quotes whose relative spread `(ask - bid) / mid` exceeds a threshold (default 0.60 for the free feed; tighter for a real feed). Wide spreads are stale or illiquid.
3. **Liquidity filter.** Require `open_interest > 0` or `volume > 0`. Optional and recorded, because it can thin short-dated wings.
4. **Mid price.** Use the bid-ask mid as the working price. Last-traded is ignored: it can be hours old and on either side.
5. **Choose one right per strike.** Keep **out-of-the-money** options: puts below the forward, calls above it. OTM options are the most liquid and carry the least early-exercise premium. At-the-money, blend put and call.
6. **Intrinsic bound.** Remove any quote below its intrinsic value (`max(F - K, 0)` discounted, for a call), which cannot be inverted.
7. **Monotonicity and convexity pre-filter.** Within an expiry, call prices must fall as strike rises and be convex in strike; the reverse for puts. Quotes that violate this are static-arbitrage outliers (usually a bad print) and are dropped before fitting, not fitted through.
8. **Minimum strikes per expiry.** An expiry with fewer than a set number of clean quotes (default 5) is dropped: too few points to fit a smile.

The output of this stage is, per expiry, a set of clean OTM mid prices with strikes — the input to the forward and the inversion.

---

## 5. Forward and discounting

For each expiry, two numbers are implied from the clean quotes before any vol is computed.

- **Put-call parity** says `C(K) - P(K) = D(T) · (F - K)`, where `F` is the forward, `D(T)` the discount factor, `C` and `P` call and put prices at strike `K`. Regressing `(C - P)` on `K` across strikes that have both a call and a put gives a straight line: the slope is `-D(T)` and the intercept is `D(T)·F`. From these, **the forward `F(T)` and the discount `D(T)` are read off directly**, with dividends and borrow already baked in.
- The strike nearest the forward defines **at-the-money**; log-moneyness is `k = ln(K / F)`.

This is the step that makes the surface self-consistent: the same quotes that will be inverted also define the forward they are measured against.

---

## 6. Implied volatility (inversion)

For each clean OTM quote, solve Black-Scholes for the volatility that returns the mid price, given `F(T)`, `D(T)`, `K` and `T`. Because price is monotonic in vol, this is a one-dimensional root-find (Brent's method, bracketed); a vega-based Newton step is the fast path with Brent as the safe fallback.

The working quantity is not vol itself but **total implied variance** `w(k, T) = σ_BS(k, T)² · T`. Total variance is the natural coordinate for calibration: no-arbitrage conditions are cleanest in it, and it is additive along the term structure.

The output is a cloud of points `(k, w)` per expiry — the empirical smile to be fitted.

---

## 7. Calibration (fitting a smile that cannot be arbitraged)

A calibrated surface is not just a fit; it must be **arbitrage-free**, or the greeks and prices read off it are nonsense. Two arbitrages have to be excluded:

- **Butterfly arbitrage** (within one expiry): the implied risk-neutral density must be non-negative. A smile too curved implies a negative probability somewhere.
- **Calendar arbitrage** (across expiries): total variance `w(k, T)` must not decrease as `T` increases, at fixed `k`. A later expiry cannot have less total variance than an earlier one.

### 7.1 Per-expiry model: SVI

Each expiry's smile is fitted with the **SVI** (Stochastic Volatility Inspired) parameterization of total variance, in its raw form:

```
w(k) = a + b · ( ρ · (k - m) + sqrt( (k - m)² + σ² ) )
```

Five parameters per expiry: `a` (overall level), `b` (slope of the wings), `ρ` (asymmetry → skew), `m` (horizontal shift of the smile), `σ` (how smooth the curve is near the money). SVI is the desk standard because five interpretable parameters fit equity smiles well and the no-arbitrage conditions are known in closed form.

- **Fit** by least squares of model `w` against market `w`, weighted by each quote's vega (so liquid near-the-money quotes count more than noisy wings), with parameter bounds that keep the smile sane.
- **Butterfly constraint.** After fitting, check Gatheral's condition (the function `g(k) ≥ 0`); if it fails, refit with the constraint active or shrink `b`. No slice is published that fails the check.

### 7.2 Across expiries

Fit each expiry independently, then **enforce calendar monotonicity**: order the slices by `T` and, where a later slice dips below an earlier one in total variance at some `k`, lift it to remove the crossing. Between listed expiries, interpolate **in total variance, linearly in `T`** at fixed `k` (which preserves no-calendar-arbitrage); convert back to vol as `σ = sqrt(w / T)`. Beyond the last expiry, extrapolate flat in vol and flag it.

The result is a function `σ(K, T)` defined for any strike and expiry, arbitrage-free by construction.

---

## 8. Outputs

What the module exposes, and what the desk actually looks at:

- **Point query:** `σ(K, T)` for any strike and expiry; and the option price and greeks at that point.
- **ATM term structure:** `σ_ATM(T)` against `T` — the market's expected vol path. The 30-day point should track VIX (section 9).
- **Skew:** the slope of the smile at the money, per expiry; and the **25-delta risk reversal** (25Δ put vol minus 25Δ call vol), the desk's standard skew measure.
- **Curvature:** the **25-delta butterfly** (average wing vol minus ATM vol), the standard smile-convexity measure.
- **Risk sensitivities (greeks):**
  - First order: **delta** (spot), **vega** (vol), **theta** (time), **rho** (rate).
  - Second order: **gamma** (delta vs spot), **vanna** (delta vs vol / vega vs spot), **volga/vomma** (vega vs vol).
  - **Vega buckets:** vega grouped by expiry, the way a vol book's risk is reported and hedged.
- **Forward vol:** vol between two future dates, from the difference in total variance — what calendar and forward-vol trades are priced on.

These are precisely the "risk sensitivities" a vol and Delta 1 book is managed by.

---

## 9. Quality assurance (how we know the surface is right)

No surface is published unless it passes, and every check is logged with its result:

1. **Arbitrage-free:** no butterfly violation on any published slice; total variance monotone in `T`. Hard gate.
2. **Fit error:** root-mean-square error of model vs market implied vol, per expiry, in vol points. A slice above a threshold (default 1.5 vol points) is flagged for review.
3. **VIX cross-check:** the 30-day ATM vol from the SPX/SPY surface should sit close to VIX on the same day. A large gap means a data or forward error. This is a free, independent check and a good daily sanity test.
4. **Reprice error:** feed each clean market quote back through the surface and reprice it; the price error distribution should be centred near zero and inside the bid-ask for most quotes.
5. **Day-over-day stability:** parameters and ATM vols should move smoothly between days; a jump flags a data problem or a market event, and the two are told apart by eye.

Points 1 and 2 are the acceptance criteria; 3 to 5 are monitoring.

---

## 10. How it plugs into the paper book

Consistent with `delta1` (point-in-time, append-only, one job per command, every run logged):

- **New tables in `delta1.db`:** `option_quotes` (raw chain, point-in-time), `vol_forwards` (implied `F`, `D` per expiry per day), `vol_surface_params` (the fitted SVI parameters per expiry per day), `vol_surface_qa` (each day's check results). Raw and fitted are both stored, so any day's surface rebuilds exactly.
- **CLI:** `python vol/build.py YYYY-MM-DD` runs fetch → clean → forward → imply → calibrate → QA, logging to the `runs` and `events` tables like `collect.py`. A nightly job can call it after the US close, alongside the collector.
- **Nothing is sent or traded by this module.** It is market data and analytics only. A vol *strategy* on top (relative value against the clean surface) would be a separate pre-registration, after the surface is trusted.

---

## 11. What this maps to in the role

For the Millennium equities-vol BA/PM work, each stage above is a BA artifact as much as a piece of code:

- **Market-data requirements:** sections 3 and 4 are a data-sourcing and data-quality specification — upstream dependencies, fields, latency, cleaning rules, acceptance thresholds.
- **Pricing and analytics:** sections 5 to 8 are the pricing-and-analytics methodology the surface serves.
- **Risk sensitivities:** section 8's greeks and vega buckets are the risk methodology the book is run on.
- **Testing and release validation:** section 9 is the acceptance and monitoring spec.
- **Documentation:** this note plus the per-stage writeups are the user guide and functional spec.

The point is to be able to sit between a vol trader and the technology team and speak both sides: what the surface is for, what data it needs, how it is validated, and where it breaks.

---

## 12. Known limits (recorded before any result)

- Free (Yahoo) quotes are delayed and wide; the surface is for learning and paper work, not a trading mark.
- SPY options are American; the OTM-only choice reduces but does not remove the early-exercise bias. SPX is the real fix.
- No intraday capture yet: one snapshot per day near the close.
- Rates are coarse; borrow and dividends are implied, not sourced independently.
- No live vendor feed; the history depth is whatever we capture from today forward.

None of these change the method. They change the data behind it, and the module is built so the data can be upgraded without rewriting the pipeline.
