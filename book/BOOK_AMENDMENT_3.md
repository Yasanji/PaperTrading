# Book: Amendment 3, two pods

Dated 11 October 2026, after the backtests of Pods 2, 4 and 6 and before the restructured book trades. It changes the book's structure and risk budget, not any strategy's rules.

## 1. Why

After Amendment 2 only three strategies trade (trend, index events, pre-dividend) and one is in a forward test (Sleeve C), but risk was still split as if six pods traded, so every pod ran small, several futures sat near the half-contract cut-off and the book ran well below its 6% target. The book is also meant to show a Delta One pod's record, which is clearer with fewer, sharper pods.

## 2. Structure

| Pod | Strategies | Risk |
| --- | --- | --- |
| A. Systematic macro | Trend (80% of the pod) and Sleeve C, month-end rebalancing (20%, forward test) | NAV x 6% / sqrt(2) |
| B. Delta One events | Index events (Pod 3, forward test at 25%) and pre-dividend (Pod 4, full size) | Pods 3 and 4 keep the allocated capital they were tested at, NAV / 6 each |
| Research (not traded) | Paper 2 rebalancing signals, the dividend futures model | none |

Code keeps the strategy numbers (pod 1 = macro, pods 3 and 4 = events) so that records stay continuous.

## 3. Other changes

1. **Currency carry (Sleeve A)** stops trading. Its 14-year hold-out Sharpe of 0.03 passed only a weak rule (carry/sleeveA/HOLDOUT_RESULTS.md). Its signals are logged daily to book/carry_shadow_log.csv as a shadow record, so it can be re-admitted by amendment on forward evidence.
2. **Pod 5 (REIT discounts)** is parked: not built, no NAV history to test. SCALE[5] = 0.
3. **Contract sizes.** Trend targets scale with the new pod risk from the 9 October contract check. Nasdaq-100, 30-year Treasuries and gold stay out until the check is re-run with Interactive Brokers at the new size, when they may come in.
4. **Sleeve C** keeps one contract a leg, as pre-registered; its share is now 20% of the macro pod (sleeve amendment 2).
5. **Correlation check.** Risk per pod uses the square root of two, which assumes the pods are roughly uncorrelated. The monthly report shows the correlation of pod returns; above 0.5 over 126 days, the pod risk is cut to NAV x 6% / 2 until a further amendment.

## 4. Real money later

Real-money trading is subject to household compliance rules: broad ETFs (more than ten holdings) and mutual funds without restriction, single stocks only with prior approval and a holding of at least 30 days, and no short positions. None of the strategies above can trade real money in their current form. A compliant version (for example, long-only index additions held 30 days or more) needs its own pre-registration and backtest, and starts only once the paper book has run.
