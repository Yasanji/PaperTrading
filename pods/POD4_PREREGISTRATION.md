# Pod 4: pre-dividend trade

Pre-registration, drafted 6 October 2026, before any returns are computed. Yasanji Ratnaike. Every rule is fixed before any return is computed. Any change is a dated amendment, committed before the result it affects is seen.

## 1. The question

Do stocks earn higher returns in the weeks before they go ex-dividend? Hartzmark and Solomon (2013) find higher returns in months when a dividend is expected. The pod buys about three weeks before the expected ex-date and sells at the ex-date close, hedged against the market. Holding for about three weeks meets the book's minimum holding period and keeps trading costs low.

**Status.** The pod launches as a forward test at 25% of its target risk, under the portfolio pre-registration. The backtest below runs in parallel, and the pod moves to full risk only if it passes.

## 2. Universe and data

1. **Stocks.** The Sleeve B universe: the STOXX Europe 600, S&P 500 and Hang Seng constituents frozen on 5 October 2026, with the same survivorship limitation.
2. **Data.** Yahoo Finance daily closes (split-adjusted), dividends by ex-date, and volume, as in Sleeve B, with the same manifest of file names, row counts and checksums committed before the first run.
3. **Hedge.** Each region is hedged with a tradable index future: the STOXX Europe 600, the S&P 500 and the Hang Seng. The backtest uses the index levels from Yahoo Finance as a proxy for the futures.

## 3. Which dividends qualify

Only information known at entry is used. A stock qualifies for an expected dividend only if all of the following hold.

1. **Expected amount.** The expected dividend is the stock's previous regular dividend, under Sleeve B's rule for excluding specials.
2. **Expected ex-date.** The expected ex-date is the anniversary of the matching ex-date one year earlier. The stock must have at least two years of regular dividends, so that the pattern is known.
3. **Size.** The expected dividend is at least 0.5% of the close on the entry day.
4. **Liquidity and history.** As in Sleeve B: median traded value above the region's 20th percentile, and a price on at least 240 of the previous 252 trading days.
5. **Data check.** The expected dividend is at most 15% of the entry-day close.

## 4. The trade

1. **Entry.** Buy at the close 15 trading days before the expected ex-date.
2. **Exit.** Sell at the close on the actual ex-date. If no dividend goes ex within 30 trading days of entry, sell at the close of the 30th day.
3. **Dividend.** The actual dividend is credited net of 15% withholding tax.
4. **Hedge.** Each position is hedged with its region's index future, using the stock's beta over the previous 252 trading days.
5. **Return.** Exit close plus the net dividend, minus the entry close, divided by the entry close, minus beta times the index return over the holding period, minus costs.

## 5. Sizing

1. **Position size.** Each position is 10% of the pod's allocated capital.
2. **Limit.** At most 20 positions at once, so gross exposure stays within 2 times the pod's capital.
3. **Ranking.** If more stocks qualify on one day than the limit allows, those with the highest expected dividend as a share of price are taken first, with ties broken by ticker in alphabetical order.
4. **No early exit.** A position is held to its exit date, unless a risk limit or an error forces it closed.
5. **Days without trades.** Capital not in positions is held in cash. Returns are measured on the pod's allocated capital, including those days.

## 6. Costs

On each traded amount, each way: 3 basis points in Europe, 2 in the US and 5 in Hong Kong, and 1 basis point on hedge trades.

## 7. Periods

1. **Development:** 1 January 2006 to 31 December 2015, with halves 2006–2010 and 2011–2015.
2. **Hold-out:** 1 January 2016 to 30 September 2026, run once after the development results are committed.
3. **Forward test:** live from the book's launch, at 25% of the pod's target risk.

## 8. Tests and pass marks

Statistics use the pod's daily returns on its allocated capital, after costs. t-statistics are Newey–West with 10 lags.

1. **Development.** The pod passes if its return is positive with a t-statistic of at least 2.0 and positive in both halves.
2. **Diversification.** Over 1 July 2006 to 31 December 2015, a book holding trend, Sleeve A and Pod 4 at equal risk must have a higher Sharpe ratio than a book holding trend and Sleeve A.
3. **Hold-out.** The pod passes only if its hold-out Sharpe ratio is at least 0.30, its t-statistic is at least 1.0, and its return is positive in both halves (2016–2020 and 2021 to September 2026).

If the pod passes all three, it moves to full risk under the portfolio's incubation rule. If it fails any, it is closed and the result is reported.

## 9. Stress tests and reporting

1. **Stress tests.** Reported for the same six episodes as Sleeve B, descriptive only, each with the period it falls in.
2. **Reporting.** Every result is committed before the next test is run, whatever it shows. No rule, threshold, period or universe changes after a result is seen.
