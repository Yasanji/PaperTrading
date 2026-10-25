# Pre-registration: term-structure carry and the measurability of skew on a public-data surface

**Yasanji Ratnaike** · Independent Researcher
Committed before the backtest is run. Draft date: October 2026.

This document fixes the design, the signals, the sample split and the decision rules before any result is examined. It is the companion to the variance risk premium study, which tested the level of the surface; this one tests its shape, and it is honest from the outset that free data supports the two halves of the shape very differently.

## 1. Motivation and scope

The variance risk premium study asked where a delta-hedged short-volatility P&L comes from, at the money. It left the shape of the surface untouched. Two features define that shape: the term structure, the slope of implied volatility across expiries, and the skew, the slope across strikes. Each carries a documented premium, the term-structure premium of Johnson (2017) and the skew premium of Kozhan, Neuberger and Schneider (2013), and the two are not equally reachable from free data.

The term structure is reachable. The VIX complex gives a long, independent history of the one- and three-month implied levels, so a carry signal has real data to run on. The skew is not. Trading a 25-delta risk reversal needs a history of the surface's wings, and the variance premium study found the wings to be the least trustworthy part of a free-data surface, worst where this trade would live. So the paper is deliberately asymmetric. The term-structure carry is run as a full backtest. The skew is run as a measurement: can a free-data surface even pin down the risk reversal reliably enough to trade it? If the wings are too noisy to measure, that null is the result, and it is the sharper half of the contribution because the free-data repositories that fit these surfaces never ask it.

A third shape premium, the correlation premium behind dispersion (Driessen, Maenhout and Vilkov, 2009), needs single-name option data and is out of scope; it is named here only to mark the boundary.

## 2. Data

Two series, both already in hand, neither requiring a fresh fetch.

- The VIX complex history: date, VIX, VIX3M, the slope VIX3M minus VIX, and the CBOE SKEW index, from January 2012 to the build date, at roughly every second trading day. This carries the term-structure signal and the published skew proxy.
- The daily variance premium series from the companion study: SPX spot, VIX, and 21-day realised volatility from 2005, with the full greek-attributed daily P&L of the delta-hedged short straddle. This carries the position the carry signal is applied to, and the realised volatility the term structure is paid against.

The live SPX surface rebuilt by the pipeline supplies the current 25-delta risk reversal per expiry, which is the snapshot the skew measurement works from. The caveats of the variance premium study carry over, with extra weight on the wings: the 25-delta strikes the risk reversal depends on are exactly where spreads are widest and quotes stalest.

## 3. The trades, fixed before results

### 3.1 Term structure (vol carry) — the backtested leg

The signal is the term-structure slope, VIX3M minus VIX, cross-checked against the three-month minus one-month fitted volatility on the live surface. Two constructions are run, both committed here:

- Primary, as a timing filter on the variance premium. The companion study's delta-hedged short straddle is held only when the slope is in contango beyond a threshold fixed here at +1 volatility point, and held flat otherwise. The slope is forward-filled to each trading day, which is defensible because it is slow-moving. This construction is fully computable from data in hand and tests Johnson's (2017) result directly: does the term structure time the variance premium.
- Secondary, as a variance term-structure calendar. Short the longer-dated variance and long the shorter-dated, vega-matched and delta-hedged, put on in contango beyond the same +1 volatility-point threshold and held flat in backwardation. It is never reversed, because the short-gamma risk of a reversed trade in a stressed market is not the premium under test. This leg is marked from the VIX and VIX3M levels rather than from traded futures, so its P&L is a first-order proxy for the carry and is reported as such, with the limitation stated in Section 9.

### 3.2 Skew (risk reversal) — the measured leg

The design, committed so that it is tradable if and only if the data turns out to support it: a one-month SPX 25-delta risk reversal, short the 25-delta put and long the 25-delta call, sized vega-neutral at the money to isolate the skew from the level, delta-hedged at each close. The direction is short the downside skew, the documented sign of the premium, carrying the crash risk that goes with it.

The primary deliverable for this leg is not a P&L but a measurement: on what fraction of days can the free-data surface quote both 25-delta wings cleanly enough to put the trade on, and how stable is the fitted risk reversal day to day. The CBOE SKEW index is used as the published proxy for whether the skew premium is present at all over the sample. A P&L is reported only over the days that pass the wing gates in Section 8, and only as an upper bound, with the excluded fraction stated alongside it so the reader can judge what the number is worth.

## 4. Sizing and hedging

Both trades are sized to a constant vol-target exposure, the same convention as the variance premium study, so the figures describe how the trade behaves and are not a return on capital. Delta is rehedged at each day's close. The at-the-money vega neutrality of the risk reversal, and the vega match of the carry calendar, are re-struck at each roll.

## 5. P&L attribution

Each day's P&L is decomposed by a second-order expansion into theta, the hedged delta, gamma, vega, vanna, volga and a residual, reconciling to the net. The expectations, stated in advance: the carry calendar's P&L loads on the vega and theta differential across the two tenors; the risk reversal's P&L, on the days it can be measured, loads mainly on vanna, the sensitivity to spot and volatility moving together, which is what a skew position is. Confirming or refuting those expectations is part of the result.

## 6. Samples and pre-registration

- Development: sample start to 31 December 2015.
- Hold-out: 1 January 2016 to the build date, run once.

The split and the trading rules above are fixed before any result is examined. The thresholds stated in Section 3, the +1 volatility-point contango, and the gates in Section 8, are the committed values.

## 7. Hypotheses and decision rule

- H1 (carry, primary): the contango-gated short-volatility position earns a higher mean P&L per unit of risk than the ungated position over the development period, with a Newey-West t-statistic on the difference beyond 2.
- H2 (carry, secondary): the variance term-structure calendar earns a positive mean P&L over the development period, with a Newey-West t-statistic beyond 2.
- H3 (skew): stated as a measurement, not a return. The free-data surface quotes both 25-delta wings cleanly on a high enough fraction of days to support a tradable risk reversal, provisionally fixed at 80% of days.

A carry premium is reported as supported only if it is positive in both the development and the hold-out period, with the hold-out run once. The skew is reported as measurable only if H3 holds; if it fails, the paper reports the null and does not show a tradable skew P&L. Every figure is reported as an upper bound, for the reasons in Section 9.

## 8. Reliability gates

The surface must pass the checks of the variance premium study: round-trip recovery, arbitrage-free fit, and a thirty-day variance-swap volatility that tracks VIX. Two gates are added here because the skew leg depends on the wings:

- Wing coverage: each 25-delta strike used must have a two-sided quote whose relative spread is below a threshold fixed here at 25% of the mid. Days on which either wing fails are excluded and counted.
- Skew stability: the day-to-day change in the fitted 25-delta risk reversal is capped at a threshold fixed here at 3 volatility points; a larger jump is treated as a bad print, excluded and counted.

The excluded fraction is itself a headline result. If it is high, the honest conclusion is that the free-data wings cannot support the measurement, independent of whether the premium exists.

## 9. Frictions and limitations, stated in advance

The wing bid-ask, worst on free data, hits the risk reversal hardest, since both its legs are out of the money. The carry calendar is marked from VIX-complex levels rather than traded futures, so it omits the futures basis and the roll cost, and overstates the clean carry; its figure is an upper bound on an upper bound. The daily close rehedge is cleaner than anything achievable in practice. VIX stands in for the implied level throughout. The vol-target sizing means the figures are not a return on capital. The short-skew position carries real and large tail risk, concentrated in exactly the fast down-moves where the wings also become unquotable, so its worst days and its worst data coincide.

## 10. What counts as an honest failure

Three outcomes are reported plainly if they occur: the carry does not survive the hold-out; the excluded-day fraction is high enough that the wings cannot support a reliable skew measurement, which is the result this paper most expects; or the greek attribution does not reconcile. Any of these ends the relevant trade as a tradable idea on this data, and each is worth stating.
