# Book: Amendment 2

Dated 9 October 2026, after the backtests of Pods 2, 4 and 6 were committed, and before any of them trades.

1. **Pod 2 (equity carry, Sleeve B)** failed its development test (carry/sleeveB/DEV_RESULTS.md) and is closed: config.SCALE[2] = 0.
2. **Pod 6 (volatility)** failed its development test (pods/pod6/DEV_RESULTS.md) and is closed: config.SCALE[6] = 0.
3. **Pod 4 (pre-dividend)** passed development, diversification and hold-out (pods/pod4/DEV_RESULTS.md, HOLDOUT_RESULTS.md). Under its pre-registration it moves to full risk under the incubation rule: config.SCALE[4] = 1.0, positions of 10% of allocated capital, at most 20. It trades in the paper account through the same chain, with its own exit rule overriding the minimum holding period, as for Pod 3.
4. **Pod 4 in the chain.** pods/pod4/refresh.py runs in the evening chain before book.py. Announced ex-dates are read from Yahoo's calendar for held stocks; if none is announced, a position closes on its 30th trading day. Hong Kong orders are rounded down to board lots from delta1/pod4/hk_lots.csv, or 500 shares if the file is missing. US stocks route through SMART with no primary exchange.
5. **Freed risk.** The risk shares of Pods 2 and 6 are not reallocated. The book runs below its 6% target until a further amendment.
