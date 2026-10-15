# Amendment 9: analysis plan for the SSRN extensions

Written 15 October 2026, before the run it governs. Status: **draft for review. Not to be run until approved and committed.**

## 0. What has already been seen (disclosure)

These tests are not confirmatory. The registered tests (Amendments 4 and 5) and later checks (Amendments 6 to 8) are reported elsewhere. On 15 October, before this plan, a rough version of most tests below was run once (`a4_step4_extensions.py`, output `a4_step4_results.csv`). It is committed unchanged as a record. Seen from that run:

- Threshold barely moves with volatility controls (−0.320, t −3.20).
- Under a binary high-volatility split, the effect is larger on high-volatility days.
- The US and UK survive HMM's crisis exclusion; Canada and Australia do not.
- Every market is null after March 2023.
- The US Threshold signal does not predict Canada, Australia or the UK one market at a time.
- A sign-only strategy is profitable in Germany despite a null regression, which shows that test is unsuitable.

The choices below were made knowing this. To limit the damage:

- (a) each choice follows HMM or the registered design where one exists, not the rough run;
- (b) where the rough run used a choice made on the spot, this plan replaces it with a choice that needs no cut-off;
- (c) every test below is judged after one multiple-testing correction across the whole family;
- (d) the paper reports them in a separate section labelled exploratory.

## 1. Common elements

- **Signals, returns, controls, timing:** as in Amendments 4, 5 and 7 (common price basis, alignment fix, equation (3), US signal from the last US close before the local close, Canada on the previous US day).
- **Windows:**
  - main window: 1 January 1999 (Canada 2002, Germany 7 March 2014) to 17 March 2023;
  - later window: 20 March 2023 to 30 September 2026.
- **Pooled tests:** Canada and Australia, market-specific constants and controls, common coefficients on the tested terms, standard errors clustered by date.
- **Single-market tests:** Newey–West with lags by floor(4(T/100)^(2/9)).
- **Further inference for every test in the family:**
  - wild bootstrap by date, Rademacher weights, null imposed, B = 1,999, seed 20261015;
  - for single-market Threshold coefficients, IVX (Kostakis et al., 2015) as a check.

## 2. The tests (family F, 18 tests)

**E1. Volatility as a confound (2 tests).** Add two lagged controls to the pooled main-window regression:

- RV, local realised volatility, the standard deviation of daily local equity returns over the previous 22 trading days, annualised;
- VIX at the last US close before the local close, divided by 100.

Tests: Threshold and Calendar × last week coefficients. Prediction: both stay negative.

**E2. Volatility as an amplifier (2 tests).** Replaces the binary split of the rough run, which used a cut-off chosen on the spot. Add the interactions Threshold × z(RV) and Calendar × last week × z(RV) to E1. Here z(RV) is RV standardised by its own expanding mean and standard deviation up to day t, with at least 252 days of history. Tests: the two interaction coefficients. Prediction: negative, meaning a stronger effect when volatility is high.

**E3. Crisis exclusion matched to HMM (5 tests).** Main-window Threshold coefficient, dropping 1 September 2008 to 31 March 2009 and 1 to 31 March 2020 (HMM, Section 4). Run for each of US, UK, Canada and Australia, and pooled Canada and Australia. Germany is excluded because its main window starts in 2014.

**E4. Equity and bond legs (2 tests).** Pooled main window, same right-hand side as the main test. The dependent variable is the next-day local equity return, then the next-day local bond return. Tests: the Threshold coefficient in each. Prediction (HMM, Section 3.2): negative for equity, positive for bonds.

**E5. HMM's strategy (3 tests).** Strategy return = (local equity return − local bond return) × w, as in HMM Section 4:

- w is the average of −Thr/1.5% and a modified Calendar signal;
- the modified Calendar signal is sign(−C) in the last five trading days of the month, sign(C at t−4) on the first trading day of the next month, and 0 otherwise.

The t−4 reading of HMM's notation is our interpretation and is stated as such.

Costs: 1 basis point per leg per unit change in |w|. Tests: mean strategy return greater than zero (one-sided) in the main window for Canada, Australia and the two pooled at equal weight. The Sharpe ratio is reported, not tested. The sign-only strategy of the rough run is dropped.

**E6. HMM's spillover test (4 tests).** HMM Section 3.5:

- the next-day local equity return is regressed on the lagged US Threshold signal, the lagged US Calendar × last week, and the two trailing S&P 500 daily returns;
- no local signals are included.

Run for UK, Germany, Canada and Australia, main window. The test in each market is the US Threshold coefficient. Prediction: negative, if HMM's aggregate result holds market by market.

The Calendar coefficients are reported but are not in F.

**Total: 2 + 2 + 5 + 2 + 3 + 4 = 18 tests.**

## 3. Multiple testing and pass rule

- Romano–Wolf step-down across all 18 tests, using the joint wild-bootstrap draws (dates shared across tests).
- A test is "supported" if its Romano–Wolf p is below 0.05 and its sign matches the prediction.
- Holm-adjusted p-values are reported alongside, as a simpler cross-check.

## 4. Descriptive only (not tested, not in F)

- **D1.** Threshold coefficients for all five markets in three periods: 1999–2008, 2009 to March 2023 (the registered split), and the later window. Each comes with its 95% interval. No claims of significance in individual cells.
- **D2.** Funded pension assets as a share of GDP for the five markets, from a single OECD source and year (to be confirmed with the user before fetching). Shown against each market's main-window Threshold coefficient. With five points this is an illustration, not a test. No correlation p-value is reported.

## 5. What will not change after the run

- The main text keeps the registered results as the headline.
- Exploratory results go in their own section, with the disclosure in Section 0 and the Romano–Wolf p-values.
- No further variations are run to rescue a test that fails.
- If a step in this plan turns out to be wrong or impossible to run as written, the change is made as a dated note to this file before re-running, and both results are reported.

## 6. Review before running

An independent reviewer, with no access to the rough run's output, checks this plan for:

- ambiguity;
- choices that favour the expected result;
- tests whose inference is unsuitable.

Changes from that review are committed before the run.
