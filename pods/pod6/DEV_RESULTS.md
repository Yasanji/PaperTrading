# Pod 6: development results

Run once on 9 October 2026 with pod6_backtest.py, rules of POD6_PREREGISTRATION.md s.3, over 2006 to 2015. Data: Cboe daily settlements for every monthly VIX futures contract (pod6_data.py; no month missing from 2006 to October 2026; settlements before 26 March 2007 divided by ten), VIX and S&P 500 closes from Yahoo Finance. Returns are daily P&L on the pod's allocated capital (NAV / 6), after costs.

| Period | Return a year | Volatility | Sharpe | Newey-West t |
| --- | --- | --- | --- | --- |
| 2006 to 2015 | 0.02% | 1.08% | 0.02 | 0.07 |
| 2006 to 2010 | 0.43% | 0.94% | 0.45 | 1.03 |
| 2011 to 2015 | -0.38% | 1.21% | -0.32 | -0.75 |

63 trades, 8 closed by the stop.

**Verdict: fails the development test** (s.5.1 requires a positive return with t of at least 2.0 and a positive return in both halves). Under s.5 the pod is closed. The hold-out is not run, so that the 2016 to 2026 data stays unused for any later volatility design, and the diversification test is not needed.

Notes, recorded with the result and not used to change it:
1. Volatility is about 1% of allocated capital a year because the size rule (a doubling of the future loses at most 3% of capital) is set for the tail, so the pod would add little to the book even if it passed.
2. The entry filter is checked once a month; the trade is held to three days before expiry whatever happens to the curve in between.
