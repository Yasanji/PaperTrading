# Sleeve B: equity carry (dividend yield)

Pre-registration, drafted 5 October 2026, before any returns are computed. Yasanji Ratnaike.

Every rule below is fixed before any return is computed. Where a rule leaves a case undecided, the case is resolved in the more conservative direction and recorded as a dated amendment before the result it affects is seen.

## 1. The question

Do stocks with high dividend yields outperform stocks with low dividend yields in the same sector, after costs, in Europe, the US and Hong Kong, and does the strategy add to a book holding trend and currency carry? Koijen, Moskowitz, Pedersen and Vrugt (2018) define the carry of an equity as its expected dividend yield, and this sleeve tests the cross-sectional version within each region. The sleeve uses the trailing dividend yield, from dividends already paid, as a proxy for the expected yield. No news, announcements or dividend forecasts are used.

**Disclosure.** Dividend yield has not been tested in the earlier work. The equity value proxy of Ratnaike (2026), which failed, is related, and the sleeve is counted as a further strategy tried.

## 2. Universe

1. **Stocks.** Current constituents of the STOXX Europe 600 (the list in pairs/part2/stoxx600\_constituents.csv, mapped to Yahoo tickers by the country suffixes in pairs/part2/get600.py), the S&P 500 (from the Wikipedia constituents list on 5 October 2026) and the Hang Seng Index (from the Wikipedia constituents list on 5 October 2026). Japan is excluded, given that no reliable constituent list was available.
2. **Survivorship.** Using current constituents introduces survivorship bias, which grows the further back the test goes, and is reported as a limitation.
3. **Sector.** Each stock's sector is Yahoo Finance's sector field, read once on the date of the data download and held fixed for the whole test. It is not point in time, which is reported as a limitation.

4) **Changes to the universe.** The lists are frozen as of 5 October 2026 for the development and hold-out tests. In the forward test, the lists stay frozen unless revised by a dated amendment, and any revision applies only from the next monthly rebalance after it is committed.

## 3. Data

1. **Prices.** Yahoo Finance daily data from 1 January 2004: the split-adjusted close (Close, with auto\_adjust off) for yields, and the adjusted close (Adj Close), which includes dividends, for returns.
2. **Dividends.** Yahoo Finance dividend history, by ex-dividend date, split-adjusted as Yahoo supplies it.
3. **Volume.** Yahoo Finance daily share volume.
4. **Downloads.** All data is downloaded once and saved with the download date. Before the development run, a manifest listing each data file's name, row count and SHA-256 checksum is committed to the repository. The data itself is not redistributed, in line with Yahoo Finance's terms of use.

## 4. Eligibility at each month-end

A stock is eligible at a month-end only if all of the following hold.

1. It has a price on at least 240 of the previous 252 trading days.
2. Its first recorded dividend is at least 24 months before the month-end.
3. Its trailing dividend yield (Section 5) is above 0.1% and at or below 15%. Yields outside this range are treated as data errors, typically a dividend recorded in a different currency or unit from the price, and the stock is excluded that month.
4. Its median daily traded value (close times volume, in local currency) over the previous 63 trading days is above the 20th percentile of that measure across its region's stocks that month.

Stocks that pay no dividend are not eligible, so the sleeve ranks payers against payers.

## 5. The signal

1. **Regular dividends.** A dividend is special, and excluded, if it is more than twice the median of the same stock's previous four dividends. If a stock has fewer than four previous dividends, the median of those it has is used. A stock's first recorded dividend is treated as regular.
2. **Trailing yield.** The sum of a stock's regular dividends with ex-dates in the 365 calendar days up to and including the month-end, divided by its split-adjusted close on the month-end.
3. **Ranking.** Within each region and sector, eligible stocks are ranked by trailing yield, highest first, with ties broken by ticker in alphabetical order. A sector is used only if it has at least five eligible stocks that month.

## 6. Positions

1. **Selection.** In each qualifying sector, with n eligible stocks, the sleeve buys the top k and shorts the bottom k, where k is n divided by 5, rounded down, and at least 1.
2. **Weights.** Within each region, every long position has the same weight and every short position has the same weight, with the long side summing to 1 and the short side to minus 1.
3. **Region rule.** A region is traded in a month only if at least three of its sectors qualify. Otherwise its weight that month is zero.
4. **Market hedge.** Each region's long–short portfolio is hedged to zero beta against the equal-weighted average daily return of all that region's eligible stocks, with beta estimated over the previous 252 trading days.
5. **Combining regions.** Each traded region receives equal risk, with risk measured as the realised volatility of its hedged portfolio over the previous 126 trading days. In the first 126 days, regions receive equal weight.
6. **Timing.** Signals use data up to the close of the last trading day of each month, and positions are taken at the close of the next trading day and held until the next rebalance.
7. **Currency.** Each region's returns are in local currency. The portfolio is long–short within each region, so currency exposure is small, and it is not hedged separately.

8) **Stocks that stop trading between rebalances.** If a stock held by the sleeve has no price for five consecutive trading days, because of a delisting, takeover or suspension, its position is closed at its last available price on the first of those days, the proceeds earn nothing until the next rebalance, and no replacement is bought before then.

## 7. Costs, borrowing and scaling

1. **Trading costs,** on each traded amount: 3 basis points in Europe, 2 in the US and 5 in Hong Kong, and 1 basis point on hedge trades.
2. **Borrowing.** Short positions are charged 0.45% a year in Europe and the US, as in Ratnaike (2026), and 1% a year in Hong Kong, where borrowing is typically dearer, accrued daily.
3. **Scaling.** The combined sleeve is scaled to 5% annual volatility using its realised volatility over the previous 126 trading days, reset at each monthly rebalance. Gross exposure, the sum of the absolute values of all stock and hedge positions, is capped at 2 times the capital allocated to the sleeve. If the scaling would exceed the cap, all positions are reduced in proportion until it is met.

## 8. Periods

1. **Development:** 1 January 2006 to 31 December 2015, with halves 2006–2010 and 2011–2015.
2. **Hold-out:** 1 January 2016 to 30 September 2026, run once after the development results are committed.
3. **Forward test:** live in the paper account from its start date.

## 9. Tests and pass marks

All statistics use the daily returns of the scaled sleeve after costs. t-statistics are Newey–West with 10 lags.

1. **Development test.** The sleeve passes if its return is positive with a t-statistic of at least 2.0, and positive in both halves. It qualifies as a weak signal if it is positive in both halves with a t-statistic below 2.0. Passing or qualifying admits the sleeve to the remaining tests. Otherwise it fails and is not tested further.
2. **Factor test.** Each region's development returns are regressed on the Fama–French five factors and momentum for that region (Developed Europe for Europe, North America for the US, and Asia Pacific excluding Japan for Hong Kong, from Kenneth French's data library), with Newey–West standard errors. The three regional alphas are combined using each region's average share of the sleeve's risk over the development period. The sleeve passes only if the combined alpha is positive. Each alpha and its t-statistic are reported whatever their value.
3. **Diversification test.** Over 1 July 2006 to 31 December 2015, a book holding trend, Sleeve A and Sleeve B at equal risk must have a higher Sharpe ratio than a book holding trend and Sleeve A at equal risk.
4. **Hold-out test.** The sleeve passes only if its hold-out Sharpe ratio is at least 0.30, its t-statistic is at least 1.0, and its return is positive in both halves of the hold-out (2016–2020 and 2021 to September 2026). Otherwise it does not enter the book.

The sleeve is admitted to the hold-out only if it passes or qualifies under test 1 and passes tests 2 and 3. It enters the book only if it then passes test 4, and it then trades live under the incubation rule of the portfolio pre-registration before receiving its full share of the book's risk.

## 10. Stress tests (descriptive)

The stress tests describe how the sleeve behaves in macro shocks. They are reported whatever they show and are not used to admit or remove the sleeve.

| Episode | Dates | Period |
| --- | --- | --- |
| Global financial crisis | 1 September 2008 to 31 March 2009 | Development |
| Euro crisis | 1 July 2011 to 30 September 2011 | Development |
| Swiss franc shock | 15 January 2015 to 30 January 2015 | Development |
| Covid crash | 19 February 2020 to 23 March 2020 | Hold-out |
| Rate shock | 3 January 2022 to 14 October 2022 | Hold-out |
| Tariff shock | 2 April 2025 to 30 April 2025 | Hold-out |

1. **Measures.** For each episode: the sleeve's return, its worst five-day return and its largest drawdown within the episode, alongside the same measures for trend and Sleeve A.
2. **Timing.** Development episodes are reported with the development results, and hold-out episodes with the hold-out results, so that no hold-out episode is seen early.
3. **Overlap with other sleeves.** For each episode, the report states whether Sleeve B lost money at the same time as trend or Sleeve A.

## 11. Reporting and amendments

1. Every test result is committed to the repository before the next test is run, whatever it shows.
2. A change to the code is allowed only to make it match these rules, and each is recorded as a dated amendment stating whether any result had been seen.
3. No rule, threshold, period or universe is changed after a result is seen.

## 12. Amendments

**Amendment 1.** Made on 6 October 2026, after the pre-registration was committed and before any data was downloaded or any result seen.

1. **Holding buffer.** A stock enters when it is in the top or bottom fifth of its sector, as in Section 6.1, and stays until it leaves the top or bottom 30%, to cut turnover.
2. **Minimum holding and no-trade band.** Every position is held for at least 15 trading days, unless a risk limit or an error forces it closed. A position is adjusted only when its target changes by more than 25% of its current size.
3. **Tradable hedge.** Section 6.4 is replaced: each region is hedged with its index future (the STOXX Europe 600, the S&P 500 and the Hang Seng), with the index levels from Yahoo Finance as a proxy in the backtest.
4. **Dividends.** Returns are computed from the split-adjusted close plus dividends. Dividends on long positions are credited net of 15% withholding tax, and dividends on short positions are charged in full.
