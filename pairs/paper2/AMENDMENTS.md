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
