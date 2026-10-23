# Variance risk premium (S&P 500)

Pre-registration, drafted 23 October 2026, before any backtest result is seen. Yasanji Ratnaike. A strategy of the volatility sleeve. Every rule is fixed before the first result; any change is a dated amendment, committed before the result it affects.

## 1. The question

Does selling S&P 500 index variance — short volatility, because option-implied vol is on average higher than the volatility that is subsequently realised — earn a premium after costs? And can the strategy's daily P&L be attributed cleanly to the greeks (theta, gamma, vega, and the second-order vol greeks), so the source of the return is understood rather than assumed?

**What is known.** The variance risk premium is one of the most documented facts in equity derivatives: 30-day implied variance (VIX squared) exceeds subsequently realised variance on average, by a few vol points, as compensation for bearing crash risk (Carr and Wu, 2009; Bollerslev, Tauchen and Zhou, 2009). The premium is earned steadily and paid back sharply in crises. The test here is our own implementation, its greek attribution, and the forward record — not a claim that the premium is new.

## 2. Signal

- **Implied vol:** the 30-day fair variance-swap vol. Live, this is `vol/surface.py`'s `var_swap_vol(30d)` (which reproduces VIX to about 0.05 vol points, `vol/VOL_SURFACE_DESIGN.md`). In the backtest, where historical option chains are not available, it is **VIX** itself.
- **Realised vol:** close-to-close S&P 500 return volatility over the trailing 21 trading days, annualised.
- **Signal:** `VRP = implied − realised`. The sleeve is **short volatility while VRP > θ** (θ = 0 fixed), and flat otherwise. It does not scale with the size of the signal.

## 3. Instrument and trade

1. **Instrument.** A one-month **at-the-money straddle** on the S&P 500 (one call and one put struck at the forward), **sold**, and **delta-hedged daily** in index futures so the position carries vol risk, not direction. The pure form of the trade is a variance swap; the delta-hedged straddle is its listed-options realisation and is what can be paper-traded on Interactive Brokers.
2. **Entry.** Sell the one-month ATM straddle at each monthly roll when the signal is short.
3. **Delta hedge.** Rebalance to zero delta at each daily close. This isolates the vol P&L and is what makes the greek attribution meaningful.
4. **Exit / roll.** Hold to expiry, then roll into a new one-month straddle. Close early only on the risk stop (s. 6).
5. **Size.** Scaled so the position's vega matches the volatility sleeve's target risk (the pod risk NAV × 6% / √2 times the sleeve's share), in whole contracts, capped.

## 4. P&L attribution into the greeks (fixed method)

Each day the position's full revaluation P&L is decomposed by a second-order Taylor expansion, using the **start-of-day** greeks, into:

```
ΔV ≈ delta·ΔS            (direction — neutralised by the delta hedge)
   + ½·gamma·ΔS²         (gamma: gains from realised moves)
   + theta·Δt            (time decay: the premium collected)
   + vega·Δσ             (vega: change in implied vol)
   + vanna·ΔS·Δσ         (spot–vol cross)
   + ½·volga·Δσ²         (vol-of-vol)
   + residual            (higher-order, should be small)
```

The gamma and theta terms together equal `½·gamma·S²·(realised_var − implied_var)` over the day — the identity that *is* the variance risk premium: as a seller you are short gamma (lose when the market moves) and long theta (collect decay), and you keep the difference when realised comes in below implied. Cumulative P&L is reported by component, and the residual is tracked as a check that the attribution is complete. Greeks are measured with Black-Scholes at the day's implied vol (VIX in the backtest), spot, rate and dividend yield.

## 5. Costs

Option half-spread at entry and roll (0.5 vol point of the straddle premium, recorded), plus one index-future tick per daily delta rebalance. No borrow.

## 6. Risk

Short volatility is short crash risk: the premium is earned steadily and lost sharply (2008, Feb 2018, March 2020). The sleeve is **closed if its cumulative net loss exceeds 2.5 times its target annual volatility**, as for the other pods. A protective wing (a further-OTM long option) may be added only by a dated amendment. The daily loss and the running drawdown are reported.

## 7. Tests and pass marks (fixed before running)

- **Development:** 2006–2015. **Hold-out:** 2016 to September 2026, **run once**, honouring the book's reserved volatility data.
- **Pass (development):** positive return after costs with Newey-West t ≥ 2.0.
- **Pass (hold-out):** Sharpe ≥ 0.30, t ≥ 1.0, positive return in both halves — the book's incubation rule.
- Reported whatever the result, with the greek attribution and the drawdowns.

## 8. Disclosure and limits

Set before any result: the backtest uses **VIX** as the 30-day implied (the live sleeve uses the surface's variance-swap vol, which matches it to about 0.05 vol points); it prices the straddle and greeks with **Black-Scholes at the VIX level**, not a full historical surface (free historical option chains do not exist); rate and dividend yield are simplified constants; the index removes survivorship concerns. These change the data behind the test, not the method, and are fixed here before the backtest is run.
