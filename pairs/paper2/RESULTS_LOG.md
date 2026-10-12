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

## Step 8: US through 2025 (exploratory, not pre-registered), 8 October 2026

Run with step8_us_through_2025.py after it was committed. Checks Harvey, Mazzoleni and Melone's statement (working paper of 14 January 2026, footnote 32) that results "become even stronger" with the sample extended through 2025. Coefficients with HC1 t-statistics; Newey-West (9 lags) in step8_us_through_2025.csv.

| Data | Period | N | Threshold | Calendar x last week |
| --- | --- | --- | --- | --- |
| Index and yields | 1997 to Mar 2023 | 6,373 | -0.407 (t -3.46) | -0.200 (t -2.67) |
| Index and yields | Mar 2023 to Dec 2025 | 695 | +0.407 (t 1.14) | +0.195 (t 1.10) |
| Index and yields | 1997 to 2025 | 7,068 | -0.348 (t -3.10) | -0.180 (t -2.48) |
| Futures (ES, ZN) | 2001 to Mar 2023 | 5,388 | -0.518 (t -3.93) | -0.259 (t -2.86) |
| Futures (ES, ZN) | Mar 2023 to Dec 2025 | 703 | +0.317 (t 0.87) | +0.196 (t 1.11) |
| Futures (ES, ZN) | 2001 to 2025 | 6,091 | -0.453 (t -3.62) | -0.233 (t -2.68) |
| ETFs (SPY, IEF) | 2003 to Mar 2023 | 4,942 | -0.549 (t -4.10) | -0.243 (t -2.45) |
| ETFs (SPY, IEF) | Mar 2023 to Dec 2025 | 700 | +0.227 (t 0.62) | +0.211 (t 1.10) |
| ETFs (SPY, IEF) | 2003 to 2025 | 5,642 | -0.488 (t -3.85) | -0.216 (t -2.28) |

On all three data sources both coefficients are positive and not significant over March 2023 to December 2025, and adding those months makes the full-sample coefficients and t-statistics smaller. This does not reproduce the statement in footnote 32, for which no estimates are published. Limits: the futures series are unadjusted front-month contracts with roll days kept; the index-and-yields main sample has 6,373 observations here against 6,293 in Step 1, a difference not yet explained.

### Step 8 follow-up: set-up checks, 8 October 2026

1. **Observation gap explained.** Step 1 downloads Treasury yields from 1997, so momentum (which needs 252 days) is missing for the first months of the sample and about 80 days drop out (6,293). Step 8 downloads from 1996 and keeps them (6,373). With the full start, the Threshold coefficient is -0.407 against -0.414 published. The Calendar gap (-0.200 against -0.303) remains.
2. **The hold-out regressions alone do not show the effect has gone.** Estimated on 1997 to 2025 with the rebalancing coefficients allowed to change after 20 March 2023 (other coefficients held fixed, HC1), the change is +0.067 (t 0.28) for Threshold and +0.021 (t 0.21) for Calendar x last week on index and yields, and +0.075 (t 0.31) and +0.051 (t 0.45) on ETFs. The positive hold-out coefficients in the table above come largely from re-estimating every control on about 700 days. The data cannot distinguish "the effect has gone" from "the effect is unchanged".

## Amendment 4.3 data checks, 11 October 2026

Run with a4_step1_yields.py after it was committed (two later commits fixed the Australian file reader only). Bond returns only; no equity data touched.

| Market | Official yield | Coverage 2005 to Sep 2026 | Timing check (same day / previous day) | Result |
| --- | --- | --- | --- | --- |
| Canada | Bank of Canada 10-year benchmark | Yes | 0.87 / 0.06 against XGB.TO | **Pass** |
| Australia | RBA F2, 10-year | Yes | 0.72 / 0.05 against IGB.AX | **Pass** |
| Japan | Ministry of Finance, 10-year | Yes | 0.46 / 0.00 against 1482.T | Fail (rule 2) |
| Sweden | Riksbank, 10-year | Yes | No traded series on Yahoo | Fail (rule 2) |
| Switzerland | SNB Confederation 10-year spot | Ends 31 Jul 2025 | 0.41 / 0.05 against CSBGC0.SW | Fail (rules 1 and 2) |
| France, Netherlands, Spain, Italy | Banque de France, DNB, Banco de Espana, Banca d'Italia | Not reached from this workspace | | Pending a manual download |

Notes recorded with the result: the Japanese and Swiss ETFs may be less liquid or shorter in duration than a 10-year bond, so a low same-day correlation may reflect the ETF rather than the yield's timing; under rule 2 the markets fail all the same. The four euro-area markets are not failed: their official daily series are to be downloaded by hand and checked by the same script before any equity data is used.

## Amendment 4 main tests, 11 October 2026

Run once with a4_step2_main.py after it and Amendment 5 were committed. Common basis (price index, bond price change, no carry); equation of Harvey, Mazzoleni and Melone plus lagged US signals. Coefficients with t-statistics (pooled: clustered by date; single markets: Newey-West).

| Test | Threshold | Calendar x last week |
| --- | --- | --- |
| **Pooled, Canada and Australia, 1999-2023 (primary)** | **-0.314 (t -3.06)** | **-0.202 (t -2.69)** |
| Change after March 2023, Canada and Australia (primary) | +0.032 (t 0.48; 95% CI -0.098 to 0.162) | -0.090 (t -1.25; CI -0.230 to 0.051) |
| Pooled, all five markets | -0.273 (t -3.44) | -0.164 (t -2.75) |
| Change after March 2023, all five | +0.067 (t 0.99) | -0.045 (t -0.75) |
| Canada, 2002-2023 | -0.374 (t -2.07; IVX p 0.02) | -0.239 (t -2.40; IVX p 0.02) |
| Australia, 1999-2023 | -0.269 (t -2.08; IVX p 0.01) | -0.165 (t -2.67; IVX p 0.03) |
| UK, 1999-2023 | -0.240 (t -2.62) | -0.151 (t -3.08) |
| Germany, 2014-2023 (price index) | +0.140 (t 0.92) | +0.113 (t 1.53) |
| US, 1999-2023 | -0.429 (t -3.66) | -0.212 (t -2.90) |

Holm-adjusted across these 18 tests: pooled Canada and Australia Threshold p = 0.034 (supported); its Calendar signal p = 0.085; pooled all five Threshold p = 0.010; US Threshold 0.005; UK Calendar 0.033. Single new markets pass the per-market rule but not after Holm. No change after March 2023 is significant, so the data cannot say whether the effect has weakened.

Pre-registered checks (4.7.1): with 40% and 30% equity targets the pooled Canada and Australia coefficients are -0.280 (t -2.85) and -0.301 (t -2.90) for Threshold and -0.205 (t -2.74) and -0.234 (t -2.76) for Calendar; no change after March 2023 is significant. The global equity leg (4.7.2) is not yet run.

Reading, recorded with the result: the effect found in the US replicates out of sample in two new markets whose data had not been used; on a common return basis the UK effect also holds for both signals; Germany shows nothing over its short price-index sample.

## Independent audit of the main tests, 11 October 2026

An independent reviewer reproduced the Canada regression exactly (thr -0.3735, t -2.07; calw4 -0.2390, t -2.40) and found no look-ahead. Two findings led to Amendment 7: bond returns were computed before aligning yields to equity dates (a small error), and Canada, which closes with the US, receives the previous day's US signal under the registered rule.

## Amendments 6 to 8: checks, run once on 12 October 2026 (a4_step3_battery.py; a4_step3_results.csv)

All with the alignment fix (7.1). Pooled = Canada and Australia unless stated.

**Primary tests after the alignment fix.** Pooled Threshold -0.321 (t -3.10), Calendar x last week -0.201 (t -2.67); change after March 2023 +0.032 (CI -0.098 to 0.162) and -0.087 (CI -0.227 to 0.052). All five pooled: -0.265 (t -3.35) and -0.162 (t -2.72). Canada -0.368 (t -2.12) and -0.240 (t -2.40); Australia -0.282 (t -2.17) and -0.161 (t -2.64).

**Canada with the same-day US signal (7.2).** Canada Threshold -0.505 (t -3.00), Calendar -0.071 (t -0.67). Pooled Threshold -0.384 (t -3.73), Calendar -0.128 (t -1.73). The Threshold result strengthens; the month-end result in Canada does not survive.

**Inference for few markets and persistence.** Wild bootstrap by date: pooled Threshold p 0.004, Calendar p 0.008. Romano-Wolf over 14 tests: pooled Threshold p 0.019, all-five Threshold p 0.010, US Threshold 0.018; every Calendar test 0.06 to 0.12. Driscoll-Kraay: pooled Threshold t -2.35, Calendar t -3.00. Joint Wald (both zero): pooled p 0.001. Multivariate IVX with White variance: Threshold and Calendar negative and significant in the US, UK, Canada and Australia (t between -1.97 and -3.32), not in Germany. Ibragimov-Mueller across market estimates: two new markets, Threshold p 0.083 (one degree of freedom); all five, p 0.068 (Germany pulls it down).

**Error correction (5 lags).** With four extra lagged returns the Threshold coefficient weakens everywhere (Canada -0.437, t -1.93; Australia -0.269, t -1.67; US -0.277, t -1.51), while Calendar holds (Canada t -2.32, Australia -2.52). Half-lives of a Threshold deviation: 1.2 days (Canada), 2.2 (Australia), 2.1 (US), 5.1 (UK).

**Reversal (local projections, pooled, Driscoll-Kraay).** Calendar: -0.200 at day 1 (t -2.92), -0.147 at day 5, +0.139 at day 10 (CI -0.239 to 0.517): it reverses, as temporary price pressure should. Threshold: -0.323, -0.617, -0.927 at days 1, 5, 10 (all t below -2.3): it does not reverse but accumulates, which a persistent signal repeating its pressure would also produce.

**Global equity leg (6.3).** First run invalid: the MSCI World index closes with the US, after the UK, German and Australian closes, so the global signal used later information (large positive coefficients). Re-run with the previous global close for those markets (a4_step3_global_fixed.csv): the global signal predicts nothing in the UK, Germany or Australia, while the local signals keep their sign (Australia Threshold -0.353, t -2.01; Calendar -0.230, t -3.17). In Canada local and global signals are collinear (correlation 0.69) and neither is significant alone in the joint regression.

**Spillover (6.4).** Two lagged S&P 500 returns change nothing (pooled -0.314, t -3.11; -0.201, t -2.68).

**Placebos (6.6).** Calendar interacted with weeks 1, 2 and 3: +0.172 (t 1.74), +0.065, +0.096; the negative effect is only in the last week.

**Which leg (6.7).** The equity return carries it (Threshold -0.268, t -2.77; Calendar -0.186, t -2.78); the bond return moves the other way, weakly (+0.053, t 1.99).

**Stability (6.8, 8.5).** Threshold -0.246 (t -1.81) in 1999-2008 and -0.376 (t -2.58) in 2009-2023; Calendar -0.297 (t -2.72) and -0.132 (t -1.36). Equal Threshold across Canada and Australia: p 0.57. No extra effect after a down month (-0.078, t -0.90).

**Economic value (6.9, 8.3).** Out-of-sample R-squared from 2010: US 1.0%, UK 0.10%, Australia 0.19%, Canada -0.37%, Germany -7.9%; Clark-West t: US 2.00, UK 3.07, Australia 2.27, Canada 1.61. Month-end trade Sharpe after 1bp a leg, 1999-2023: US 0.37, UK 0.59, Australia 0.42, Canada 0.20, Germany -0.37.

**Reading.** The Threshold effect is the robust result: pooled, bootstrapped, Romano-Wolf adjusted, IVX, Driscoll-Kraay, spillover-controlled, stronger with Canada's same-day US signal, and equal across the two new markets. It weakens when four lagged returns are added and does not reverse, so it may partly capture short-run return dynamics rather than pure price pressure. The month-end effect behaves like price pressure (only in the last week, on the equity leg, reversing within ten days) but is weaker statistically: it fails Romano-Wolf and does not survive Canada's same-day US signal.
