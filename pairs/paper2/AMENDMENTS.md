# Paper 2: amendments to the pre-registration

The pre-registration in PREREGISTRATION.md is left unchanged. Each amendment below is dated and states whether it was made before or after any European or UK data was used.

## 1. Threshold band range

Made on 5 October 2026, during the US replication in Step 1 and before any European or UK data was used.

The pre-registration describes the Threshold signal as the average across bands from 0% to 2%, as in Harvey, Mazzoleni and Melone. That range misreads their paper. Their main signal, in their equation (2), averages bands from 0% to 2.5% in steps of 0.1 percentage points, and the 0% to 2% range is one of their sensitivity checks (their Appendix Table D.6). The intent was to follow their construction, so the code and every later test use bands from 0% to 2.5% in steps of 0.1 points.

## 2. Step 1 result

Run on 5 October 2026 with step1_us_replication.py, on the S&P 500 index and 10-year Treasury yields, over 10 September 1997 to 17 March 2023.

| Coefficient | This replication | Published (Table 1, column 1) |
| --- | --- | --- |
| Threshold | -0.360 (0.117) | -0.414 (0.115) |
| Calendar in the last week of the month | -0.191 (0.075) | -0.303 (0.081) |
| Calendar | 0.018 (0.065) | 0.055 (0.071) |
| Momentum | 0.0021 (0.0006) | 0.0023 (0.0006) |
| Trailing one-day return | -0.035 (0.030) | -0.020 (0.029) |
| Observations | 6,293 | 6,226 |

Heteroskedasticity-consistent standard errors in brackets.

The pass mark asks for coefficients close in size to the published estimates without defining close, and it is not defined after the result has been seen, so the comparison is reported in full. The Threshold coefficient is within half a standard error of the published value. The Calendar coefficient in the last week of the month has the same sign and is significant, at about 60% of the published size, which is consistent with the use of index and yield data in place of futures and with a sample 67 days longer. The European and UK tests proceed as specified, with the band range in amendment 1.

## 3. Corrections after an audit of the main and hold-out results

Made on 5 October 2026, after the main-sample and hold-out results in MAIN_RESULTS.md had been seen, and committed before the corrected analysis was run. The corrected analysis is reported as post-audit, alongside the original results.

An audit of the data, construction and statistics found two errors.

1. The regression in the pre-registration omits two terms in the equation of Harvey, Mazzoleni and Melone: the Calendar signal on its own and the last-week indicator. Without them, any average difference in returns in the last week of the month can load onto the Calendar term. The corrected analysis uses their full equation in every test.
2. The Bundesbank's daily 10-year yield is not measured at the market close. Bond returns computed from it correlate 0.47 with a German government bond ETF on the same day and 0.47 on the previous day, against 0.87 on the same day for the UK series. The corrected analysis uses the ECB's euro-area AAA 10-year spot yield, whose returns correlate 0.79 with the same ETF on the same day and 0.11 on the previous day. That series starts in September 2004, so the German sample starts in late 2005, once the momentum signal has a year of data.

Everything else is unchanged: the UK and US data, the hypotheses, the pass rule, the periods and the hold-out.

The audit also recorded the following.

- The false-positive rates of the Newey-West, IVX and Hodrick tests, in 300 simulations of UK-like data with no predictability, are 2.3% to 3.7% at a nominal 5%, and 1.3% for the Hodrick test at a 10-day horizon. The bootstrap was not simulated.
- Signals rebuilt with data only up to a given day match the full-sample signals for the Threshold signal, momentum and the trailing return.
- The gap between the Step 1 Calendar coefficient and the published one remains unexplained: total-return ETFs (SPY and IEF) give -0.242 against -0.217 for index and yield data over 2003 to 2023, against -0.303 published.
- The effect of UK dividend dates cannot be measured with free data. The last-week indicator in the corrected equation absorbs any average difference in last-week returns.

## 4. More markets and a revised design

Made on 8 October 2026, after the UK, German and US results (including Step 8) had been seen, and before any data for the markets in 4.2 has been downloaded. It responds to the set-up audit in SETUP_AUDIT.md. The UK and Germany are re-run under these rules but, having been seen, are reported apart from the new markets.

### 4.1 Question

Does a local rebalancing signal predict the next day's local equity-minus-bond return across developed markets, and did the relation change after 17 March 2023, the end of Harvey, Mazzoleni and Melone's sample?

### 4.2 Markets

Candidates, chosen for size and for having a 10-year government bond and a main equity index: France, the Netherlands, Spain, Italy, Sweden, Switzerland, Japan, Canada and Australia. A candidate enters only if it meets all of the rules in 4.3. Markets that fail are listed with the reason. No market is added or dropped for any other reason.

### 4.3 Data rules, applied before any equity-minus-bond return is computed

1. **Bond yield.** An official daily 10-year government yield (central bank, finance ministry or debt office) covering at least 1 January 2005 to 30 September 2026, with no gap longer than ten business days.
2. **Timing check.** Daily bond returns computed from the yield are correlated with returns on a traded local government bond series (an ETF or a futures contract). The yield passes if the same-day correlation is at least 0.6 and at least three times the previous-day correlation, over the common sample. This is the check that found the Bundesbank problem (0.47 and 0.47).
3. **Equity index.** The main local index, from Yahoo Finance, covering the same period.
4. **The checks in rules 2 and 3 use bond returns only.** Equity returns, signals and the regression are not computed for any market until every market's inclusion has been decided and recorded.

### 4.4 Return basis, the same for every market

Both legs exclude income: the equity leg is the price index, and the bond leg is the change in price of a constant-maturity 10-year bond at the new yield, with no carry. This is the basis available for every market and the closest available to the futures used by Harvey, Mazzoleni and Melone. The UK and Germany are rebuilt on it (for Germany, the DAX price index replaces the total-return DAX). Where a total-return index or ETF pair exists, the main results are repeated on it as a check.

### 4.5 Equation

Main specification: Harvey, Mazzoleni and Melone's Table 1 equation, as in Step 1 (Threshold, Calendar, last-week indicator, Calendar in the last week, momentum and the current return), plus the lagged US Threshold and Calendar-in-last-week signals, taken from the last US close before the local day. Check: the same with the current and four previous returns, as in the pre-registration. Newey-West t-statistics with the existing lag rule decide the tests; HC1 t-statistics are reported alongside.

### 4.6 Tests

1. **Pooled, new markets (primary).** All markets that pass 4.3, stacked, with a constant and controls per market and common coefficients on the Threshold signal and the Calendar signal in the last week. Standard errors clustered by date, so that markets moving together on the same day are not counted as independent. Main sample: 1 January 1999 (or the first date with a year of data for momentum) to 17 March 2023.
2. **Change after March 2023 (primary).** The same pooled regression over the whole period to 30 September 2026, adding each signal multiplied by an indicator for dates from 20 March 2023. The test is on that interaction. Separate hold-out regressions are reported only as description.
3. **Each new market (secondary).** The main specification per market, with the existing pass rule (negative coefficient, Newey-West t below -2, IVX p below 5%).
4. **All markets including the UK, Germany and the US (secondary).** Tests 1 and 2 repeated with the seen markets added.

A pooled coefficient is supported if it is negative with a t-statistic below -2. The change after March 2023 is reported with its confidence interval whatever its sign. Holm adjustment covers every test in this section.

### 4.7 Pre-registered variants (checks, not primary)

1. Equity targets of 40% and 30% in place of 60%.
2. A global equity leg: the MSCI World price index converted to local currency, against the local bond, from the first date the series is available. This tests the assumption that local investors' rebalancing runs through local equities.

### 4.8 Unchanged

The Threshold band range (amendment 1), the Calendar construction, the last-week definition, momentum, the main-sample end date of 17 March 2023 and the hold-out end of 30 September 2026. Anything not specified here is labelled exploratory.
