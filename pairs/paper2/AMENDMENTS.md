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
