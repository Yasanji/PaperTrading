# Pod 4: development results

Run once on 9 October 2026 with pod4_backtest.py, rules of POD4_PREREGISTRATION.md, over 2006 to 2015, on the Sleeve B data downloaded the same day (carry/sleeveB/sleeveB_universe.py, sleeveB_data.py; manifest committed with this file). Daily returns on the pod's allocated capital, after costs; Newey-West t with 10 lags.

| Period | Return a year | Volatility | Sharpe | Newey-West t |
| --- | --- | --- | --- | --- |
| 2006 to 2015 | 12.5% | 15.0% | 0.83 | 2.75 |
| 2006 to 2010 | 24.2% | 17.6% | 1.38 | 3.26 |
| 2011 to 2015 | 0.8% | 11.8% | 0.06 | 0.15 |

3,086 trades, mean hedged return 0.41% a trade, 54% positive, 94% closed on the actual ex-date. By region: Europe 1,373 trades at +0.56%, the US 1,635 at +0.33%, Hong Kong 78 at -0.55%.

**Verdict: passes the development test** (s.8.1: positive return, t of at least 2.0, positive in both halves). The diversification test (s.8.2) comes next, then the hold-out, run once.

Read with care, recorded before the next test:
1. Almost all of the return comes from 2006 to 2010; 2011 to 2015 is close to zero.
2. The universe is today's index members, so stocks that fell out or failed before 2026 are missing. This favours a long-only stock trade, and most strongly in 2006 to 2010, which includes 2008.
3. Volatility of 15% is three times the book's 5% sleeve norm because positions are 10% of capital each with up to 20 open, as specified; Sharpe and t are unaffected.
4. 36 universe tickers have no Yahoo data (mostly Reuters-style codes in the STOXX list) and are absent.

Implementation choices: the index proxies are ^STOXX, ^GSPC and ^HSI from Yahoo; a stock with no price on a day contributes zero that day; liquidity is checked at the month-end before entry.
