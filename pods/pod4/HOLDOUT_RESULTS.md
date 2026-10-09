# Pod 4: hold-out results

Run once on 9 October 2026 with pod4_backtest.py, after the development and diversification results were committed. Same rules, data and code.

| Period | Return a year | Volatility | Sharpe | Newey-West t |
| --- | --- | --- | --- | --- |
| 2016 to September 2026 | 6.9% | 17.7% | 0.39 | 1.29 |
| 2016 to 2020 | 7.0% | 19.5% | 0.36 | 0.83 |
| 2021 to September 2026 | 6.9% | 16.0% | 0.43 | 1.01 |

3,378 trades, mean 0.24% a trade, 52% positive.

**Verdict: passes the hold-out** (s.8.3: Sharpe at least 0.30, t at least 1.0, positive in both halves). Under s.8 the pod moves to full risk under the portfolio's incubation rule.

Limits that still apply: the universe is today's index members (survivorship), Yahoo data, and the index-level hedge in place of futures. The hold-out Sharpe is about half the development figure.
