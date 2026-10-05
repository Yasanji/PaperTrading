# Paper 2: main-sample results

Run once on 5 October 2026, with local_data.py and step2_main.py, over January 1999 to 17 March 2023. The hold-out from 20 March 2023 had not been run when these results were committed.

## Results by hypothesis

A hypothesis is supported only if the coefficient has the predicted sign, its Newey-West t-statistic is beyond 2, and the IVX test rejects at the 5% level.

| Hypothesis | Germany | UK |
| --- | --- | --- |
| 1. Local Threshold | -0.253 (t -2.04, IVX p 0.43): not supported | -0.180 (t -1.58, IVX p 0.13): not supported |
| 2. Local Calendar in the last week | -0.103 (t -2.38, IVX p 0.03): supported | -0.201 (t -4.23, IVX p < 0.001): supported |
| 3. Local Calendar with the US signals | -0.120 (t -2.17, IVX p 0.055): not supported; orthogonal version IVX p 0.03 | -0.180 (t -4.38, IVX p < 0.001): supported in both versions |
| 3. Local Threshold with the US signals | -0.203 (t -1.56): not supported | -0.150 (t -1.27): not supported |
| 4. UK adjustment coefficient smaller than Germany's | UK minus Germany 0.073 (t 0.55): not supported | |
| 5. Calendar effect reverses by day 10 | Day 1 -0.102, day 10 +0.208 (t 0.85): does not meet the rule, as the effect overshoots | Day 1 -0.201, day 10 +0.032 (t 0.12): reverses |
| 5. Threshold effect reverses by day 10 | Day 1 -0.253, day 10 -1.033 (t -1.22): does not reverse | Day 1 -0.180, day 10 -0.970 (t -1.10): does not reverse |

Observations: Germany 6,147 and UK 6,115. Adjusted R-squared of the local regression: Germany 0.003 and UK 0.016.

## Adjustment for multiple testing

Of 21 coefficient tests, three remain significant after the Holm adjustment, all for the UK Calendar signal: local only (Holm p 0.0004), with the US signals (0.0003), and orthogonal to them (0.0003). The German Calendar result does not survive the adjustment (Holm p 0.31).

## Notes on what the results do and do not show

- The month-end effect in the UK is local, survives the US signals and reverses within ten days, which is consistent with temporary price pressure from local rebalancing flows.
- Hypothesis 4 predicted a weaker UK effect, given UK defined-benefit pensions' low equity allocations. The result goes the other way for the Calendar signal, which suggests that other UK investors rebalance at month-end.
- The half-lives implied by the Threshold coefficient (2.4 days for Germany and 3.5 for the UK) are not reported as findings, given that the coefficient is not significant.

## Choices not fixed in the pre-registration

Each was fixed in the code before the main tests were run.

- Regression: as written in the pre-registration's equation, with the Calendar term entering only through its last-week interaction.
- Newey-West standard errors use the standard lag rule, floor(4(T/100)^(2/9)), which gives 9 lags.
- IVX: the single-coefficient version of Kostakis, Magdalinos and Stamatogiannis (2015), applied after partialling out the other regressors, with an instrument persistence of 1 − 1/T^0.95.
- Bootstrap: 499 replications of a stationary bootstrap with a mean block length of 21 days on the residuals under the null, keeping the regressors fixed so that their persistence is preserved; seed 7.
- Hodrick (1992) standard errors: version 1B, with residuals from the one-period return under the null of no predictability.
- The US signals for local day t are taken from the last US close before day t.
