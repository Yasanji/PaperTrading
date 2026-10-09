# Sleeve B (Pod 2): development results

Run once on 9 October 2026 with sleeveB_backtest.py, rules of PREREGISTRATION.md s.4 to s.7, over 2006 to 2015, on the data in MANIFEST.md (sectors committed before the run). Daily returns of the sleeve scaled to 5% volatility, after costs and borrowing; Newey-West t with 10 lags.

| Period | Return a year | Volatility | Sharpe | Newey-West t |
| --- | --- | --- | --- | --- |
| 2006 to 2015 | 0.18% | 5.5% | 0.03 | 0.10 |
| 2006 to 2010 | 2.10% | 5.5% | 0.39 | 0.76 |
| 2011 to 2015 | -1.60% | 5.5% | -0.29 | -0.62 |

Regions before scaling, Sharpe over 2006 to 2015: Europe -0.32, US 0.54, Hong Kong 0.01.

**Verdict: fails the development test.** It neither passes (t of at least 2.0) nor qualifies as a weak signal (positive in both halves). Under s.9 it is not tested further: no factor, diversification or hold-out test is run, and Pod 2 does not enter the book.

Implementation choices, recorded with the result: weights held at target between rebalances; a stock with no price on a day contributes zero; the 2x gross cap was not applied, which can only raise volatility before scaling and does not change the sign; 105 of 1,049 tickers have no Yahoo sector and 36 have no prices.
