# Paper 3 (planned, the proper paper): who leans against the market under stress

Status, 15 October 2026: design drafted, literature checked, data feasibility passed. Nothing tested. Register before any test.

Design doc (Claude Docs): "Who rebalances under stress: research design", https://claude.ai/code/artifact/ebed6588-0b26-4563-9796-3140531789fd

## Question

After large market moves, how do institutional and retail traders adjust equity and bond positions, and how does market stress change that? Institutions with fixed allocations should lean against moves; retail tends to extrapolate. Which side dominates decides whether moves are absorbed or amplified. Motivation: Paper 2 found rebalancing price pressure concentrated in 2008 and 2020-22, absent otherwise. Behaviour changing with stress would explain that.

## Data (feasibility checked 12 October)

- CFTC Traders in Financial Futures, futures only, public Socrata API (publicreporting.cftc.gov, dataset gpe5-46if). Weekly 13 Jun 2006 to 6 Oct 2026, 1,061 weeks, no gaps. E-mini S&P 500 code 13874A; 10-year T-note 043602. Copies: tff_ES.csv, tff_TY.csv.
  - Asset managers net long about 28% of ES open interest (sd 10 pts; weekly change sd 3.3 pts). Non-reportables about 12% of OI (weekly change sd 1.7 pts).
- VIX from FRED (vix.csv). S&P 500 cached in pairs/paper2/a4_step3_raw.pkl.
- Blocked from the cloud: AAII sentiment, ICI flows, Investment Association stats, APRA. User could download and attach.
- Rejected: inferring fund rebalancing rules from daily balanced-fund NAVs. VBINX test: never-rebalance clearly rejected (286 bp/yr tracking error vs 93) but daily, monthly and band rules within 5 bp of each other. Too noisy.

## Hypotheses (draft)

H1 asset managers contrarian; H2 asymmetric (stronger after losses); H3 small traders extrapolate; H4 institutional response weaker when VIX high (deferral); H5 stress shifts balance towards amplification; H6 same in Treasury futures; H7 (secondary) weak-rebalancing weeks followed by bigger reversals. Fit 2006-2019, hold-out 2020-2026.

## Literature gap (searches 12 October)

- Closest: Smales (2016) Review of Financial Economics 28(1) 46-55: old COT categories in S&P futures; small traders and speculators positive feedback, hedgers contrarian, reversed in 2008-09, volatility matters. Chen and Yang (2021) J. Empirical Finance 61: TFF types in VIX futures, regime above VIX about 24. Also Chen and Maher (2013), Mogford and Pain (2006), Wang (2003) JFM, Barth et al. (2024) FEDS, TBAC Q1 2024 (basis trade).
- Institutions: Bams, Schotman and Tyagi (2016) asymmetry from annual pension data; Timmer (2017/2018); Duijm and Steins Bisschop (2015); Kayacetin (2026) infers deferral from prices.
- Retail: fund flows extrapolate (Greenwood and Shleifer 2014; Ben-Rephael, Kandel and Wohl 2012); direct trading data show dip-buying, including March 2020.
- Gap: TFF categories, ES and Treasuries together, returns split by sign and interacted with VIX, asset managers vs small traders on the same weeks, through 2020 and 2022. Do one final SSRN/Google Scholar check focused on TFF papers before registering.

## Threats to handle

Futures are a partial view (cash equitisation); Treasury basis trade from about 2018 (asset managers long, leveraged funds short); non-reportables are small traders, not retail; claims are "consistent with" biases, no psychology data (user has no survey access); stress endogenous (use lagged regime); US only; weekly data cannot time month-end.

## Lessons from Economics Letters 2012 (accepted) vs Finance Research Open 2026 (desk reject)

Broad question with one clear answer; gap the field recognises; breadth; no error history in the abstract; build on published work; journal fit. Apply here.

## Next steps

1. Final literature check on TFF papers.
2. Fix every choice and commit as the registration.
3. Collect macro calendar (FOMC, CPI, NBER) and alternative stress measures.
4. Run 2006-2019, then the hold-out once.
5. Optional: learn Databricks Free Edition with this data (user to sign up; Claude prepares notebooks and files).
