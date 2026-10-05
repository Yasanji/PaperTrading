# Paper 2: results log after the main sample

A dated record of every analysis run on 5 October 2026 after MAIN_RESULTS.md, in order. Each entry states its status: pre-registered, pre-specified check, exploratory (not pre-registered), audit, or post-audit (after amendment 3).

## 1. Hold-out, pre-registered (step3_holdout.py)

20 March 2023 to September 2026, about 890 days per market, with the pre-registered equation.

| Market | Threshold | Calendar in the last week |
| --- | --- | --- |
| US (Step 1 equation) | +0.265 (t 0.83) | +0.128 (t 0.87) |
| Germany, local | +0.361 (t 1.00) | -0.202 (t -2.58, IVX p 0.013) |
| Germany, with US signals | +0.535 (t 1.45) | -0.250 (t -2.64, IVX p 0.011) |
| UK, local | +0.217 (t 1.18) | -0.100 (t -1.42) |
| UK, with US signals | +0.217 (t 1.18) | -0.076 (t -1.04) |

## 2. Pre-specified checks and economic significance (step4_checks.py)

Month-end coefficient (Calendar in the last week), pre-registered equation. Each check changes the data and the start date together.

| Check | Main-sample overlap | Hold-out |
| --- | --- | --- |
| Germany, DAX price index | +0.036 (t 0.72), from 2014 | -0.212 (t -2.62) |
| EURO STOXX 50 with Bund | -0.092 (t -1.62), from 2008 | -0.194 (t -2.43) |
| Germany, bond ETF (EXX6) | -0.017 (t -0.37), from 2009 | -0.197 (t -2.67) |
| UK, gilt ETF (IGLT) | -0.105 (t -1.94), from 2009 | -0.116 (t -1.75) |

Threshold model with the band estimated: Germany 1.25%, UK 2.0%; the test against a linear model does not reject (bootstrap p 0.18 and 0.62).

Month-end strategy, net of 1 basis point a trade on each leg: UK Sharpe ratio 0.57 in the main sample and 0.19 in the hold-out; Germany -0.02 and 1.71.

## 3. Exploratory, not pre-registered (step5_exploratory.py, step5b_profiles.py)

Month-end coefficient by period, pre-registered equation and primary data.

| Period | Germany | UK |
| --- | --- | --- |
| 1999-2008 | -0.171 (t -2.43) | -0.315 (t -4.33) |
| 2009-2016 | -0.097 (t -1.76) | -0.147 (t -2.20) |
| 2017 to March 2023 | +0.132 (t 2.03) | -0.015 (t -0.20) |
| Hold-out | -0.202 (t -2.58) | -0.100 (t -1.42) |
| Equal in all four periods | rejected, p 0.001 | p 0.076 |

Without its five most influential months, the German main-sample coefficient falls from -0.103 to -0.030 (t -0.95); the UK coefficient falls from -0.201 to -0.139 (t -3.81).

By week of the month, the week 4 coefficient is US -0.170 (t -3.41), UK -0.209 (t -4.78) and Germany -0.119 (t -3.36); the US week 3 coefficient is +0.126 (t 2.36). By day, the negative coefficients fall between about six and two trading days before month-end in all three markets, the last-day coefficient is positive in all three (significant in the US only), and no day after month-end is significant. The day profile contains 45 coefficients, so a few would pass t = 2 by chance.

## 4. Audit (audit1_data.py, audit2_checks.py, audit3_stats.py)

The findings are recorded in amendment 3 of AMENDMENTS.md. In addition, with Harvey, Mazzoleni and Melone's full equation on the primary data, the German month-end coefficient is -0.092 (t -1.56) in the main sample and -0.122 (t -1.31) in the hold-out, and the UK coefficient is -0.179 (t -3.04) and -0.038 (t -0.40).

## 5. Corrected analysis, post-audit (step6_corrected.py)

Run once after amendment 3 was committed: the full equation in every test, and ECB euro-area AAA yields for Germany.

| | Germany, 2005 to March 2023 | Germany, hold-out | UK, 1999 to March 2023 | UK, hold-out |
| --- | --- | --- | --- | --- |
| Threshold | -0.138 (t -0.92) | +0.147 (t 0.50) | -0.180 (t -1.57) | +0.243 (t 1.34) |
| Calendar in the last week | -0.052 (t -0.63) | -0.061 (t -0.70) | -0.179 (t -3.04, IVX p 0.005) | -0.038 (t -0.40) |
| Calendar, with US signals | -0.095 (t -0.98) | -0.096 (t -1.01) | -0.159 (t -3.19, IVX p 0.014) | -0.018 (t -0.19) |

The UK month-end results in the main sample are supported under the pre-registered rule and survive the Holm adjustment across 21 tests (Holm p 0.029 to 0.045). No other result is supported. The UK month-end effect does not meet the reversal rule, as the day-10 effect (+0.306, t 0.86) overshoots. The UK minus German adjustment coefficient is -0.043 (t -0.28). The German test has limited power: its standard error of about 0.082 means an effect of the UK's size would be detected about 59% of the time.

## Code change

step2_main.py now runs its tests only when executed directly, so that later scripts can import its functions. No calculation changed.

## 6. Numbers added to the paper (step7_paper_numbers.py)

Run on 5 October 2026 after the corrected analysis, for the paper draft.

- Exploratory, not pre-registered: UK month-end coefficient with the full equation, -0.299 (t -3.30) over 1999-2008, -0.156 (t -2.06) over 2009-2016 and +0.088 (t +0.75) over 2017 to March 2023. This replaces the breakdown in section 3, which used the pre-registered equation.
- Power to detect the UK main-sample effect (0.179) at 5%: UK hold-out 48%, Germany main sample 58% and Germany hold-out 53%.
- UK month-end strategy, net of 1 basis point a trade on each leg: Sharpe ratio 0.57 (t 2.78) over the main sample and 0.19 (t 0.35) over the hold-out.

The paper is in paper/, as the PDF posted to SSRN.
