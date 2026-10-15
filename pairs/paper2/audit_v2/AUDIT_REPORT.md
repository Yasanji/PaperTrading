# Referee audit (v2): "Rebalancing pressure outside the US: a pre-registered replication"

Auditor: independent re-computation, 12 Oct 2026. Draft exported from Claude Docs (rev 12) to `draft.md`.
Code in this folder: `indep.py` (own re-implementation of bond returns, drift, Threshold, Calendar, last-week, momentum, US-signal merge, pooled OLS with date-clustered / HC1 / Newey-West / Driscoll-Kraay errors), `ledger.py` (every draft number plus robustness; output `ledger_out.txt`), `extra.py` (IVX via the repo estimator on my panel, US-signal checks; `extra_out.txt`), `chow.py` (full-interaction break test; `chow_out.txt`), `rolling_own.csv`. Only `a4_step3_raw.pkl` was taken from the repo as input (plus the repo's `ivx_multi` estimator in `extra.py`).

**Bottom line.** All the core numbers reproduce to the third decimal place from an independent pipeline. There are no look-ahead or alignment errors. The main problems are in the framing:
- what is called "registered";
- the "has it faded?" narrative, where a full break test that the draft does not report finds a significant decline (t = 2.11);
- an apples-to-oranges size comparison with HMM;
- a selective global-leg claim;
- an omitted registered sub-period split;
- one wrong citation fact (McConnell and Xu: 31 of 35 countries, not 30).

## 1. Claim ledger

Status codes: PASS = reproduced (|Δ| ≤ rounding, or Monte Carlo noise for bootstrap). FAIL = wrong. UNV = cannot be verified from data or code. Wording codes: OK, OVER (overclaim), UNDER (underclaim), MISL (misleading).

| # | Location | Claim | Reproduced | Status | Wording |
|---|---|---|---|---|---|
| 1 | Abstract | Registered before data used | True for CA/AU under Amend. 4–5 (8 and 11 Oct). Not true for the original pre-registration (5 Oct, UK/DE), which was redesigned after its results were seen | PARTLY | MISL: must say "registered by amendment, after results in other markets were seen" |
| 2 | Abs/T2 | Pooled CA+AU Threshold -0.32, t -3.10 | -0.321, t -3.10 (N 11,442) | PASS | OK. This is the post-hoc alignment-fixed run; the registered run gave -0.314 (t -3.06) |
| 3 | Abs/T2 | Wild bootstrap p 0.004 | 0.001 (own draws; repo 0.004) | PASS | Added by Amend. 8, after the primary results |
| 4 | Abs | -0.37 in the US | -0.368 (t -3.20) | PASS | OK |
| 5 | Abs | Holds separately from the US signal | Yes with US controls. But AU without US controls gives -0.207 (t -1.91), and the lagged US Thr enters AU with a + sign (+0.128, t 1.75) | PASS | Fragile in AU: significance needs the US control (suppression) |
| 6 | Abs | Modest before 2020 | 1999–2019: -0.180 (t -2.10). 2009–2019: -0.120 (t -1.13). No 4-year window ending before Dec 2019 has \|t\| > 1.7 | PASS | "Modest" is generous: outside 1999–2008 and 2020–22 the effect is insignificant |
| 7 | Abs | Large in 2020–2023 | -0.998 (t -3.07) | PASS | OK |
| 8 | Abs | Close to zero since Mar 2023 | Separate regression +0.064 (t 0.43) | PASS | Unregistered estimate |
| 9 | Abs/§3 | A formal test cannot separate decline from noise | Registered restricted test: +0.032 [-0.098, 0.162]. Full-interaction (Chow) test, not reported: Δ = +0.386 (t 2.11, p ≈ 0.035) | CONTESTED | MISL: depends on the test. The registered test excludes full disappearance, while the full break test rejects stability |
| 10 | Abs | UK same effect on a consistent basis | -0.247 (t -2.74) | PASS | MISL: the basis change came after the UK null (-0.180, t -1.57). UK RW p = 0.11. UK local Thr is t -1.50 with the global leg. UK 2009–19 t -1.07; post-2023 t -0.28 |
| 11 | Abs | Germany shows none, short sample | +0.127 (t 0.79), from 2014-03-07 | PASS | OK |
| 12 | Abs | Month-end does not survive multiple testing | RW 0.067 (own 0.072). Registered Holm 0.085 | PASS | OK |
| 13 | Intro | HMM: about $16bn a year | NBER abstract: "$16 billion annually" | PASS | OK |
| 14 | Intro | HMM international test uses US signals on a non-US index | Supported in the literature review. That it is one index is the review's unverified inference | UNV | Soften |
| 15 | Intro | Chosen by a data rule fixed in advance | Amend. 4.3 committed 8 Oct, before the yields check (11 Oct) | PASS | OK |
| 16 | Intro | Survives bootstrap and multiple-testing adjustments | RW p 0.019 (own 0.027). Registered Holm p 0.034 (pre-fix run, from the log) | PASS | Report the registered Holm. RW and bootstrap are post-hoc |
| 17 | Intro | Close to US value | -0.32 vs -0.37 | PASS | OK |
| 18 | T1 | HMM sample about 2000 to Mar 2023 | 6,226 daily obs to 17 Mar 2023 implies a start around 1998. The repo replication uses 10 Sep 1997 | likely FAIL | Say "about 1998 (their Table 1)", or check |
| 19 | T1 | HMM: about 17 bp lower for typical overweight | NBER abstract: equity returns fall 17 bp the next day when stocks are overweight | PASS | OK |
| 20 | T1 | Kayaçetin: 30 countries, 1994–2023, 10 bp vs 0 | Verified | PASS | OK |
| 21 | T1 | McConnell & Xu: TOM in 30 of 35 countries | Abstract says 31 of 35 | FAIL | Fix to 31 |
| 22 | T1 | Etula et al.: month-end pattern, cash needs, equities and Treasuries | Consistent with the paper and the review | PASS | OK |
| 23 | T1 | Da et al.: Chile, coordinated switches moved prices, reversed | Consistent | PASS | OK |
| 24 | T1 | Parker et al.: TDF rebalancing, temporary pressure then reversal | Review: "temporary price pressure and reversals"; reversal detail not verified in the original | UNV (plausible) | OK |
| 25 | T1 | Camanho et al.: funds US/UK/EA/Canada, FX | Verified | PASS | OK |
| 26 | §2 | Drift formula | Code `drift()` identical | PASS | OK |
| 27 | §2 | Bands 0–2.5% step 0.1, 26 bands, reset if \|s\| > d after recording | `np.arange(0, .02501, .001)`, 26 bands; s recorded then reset | PASS | OK |
| 28 | §2 | Calendar reset at month-end; LW = last 5 trading days | Matches (market's own calendar) | PASS | OK |
| 29 | §2 | Bond: par 10y semi-annual, c = y(t-1); DE zero | Matches. Yields forward-filled ≤ 5 days onto equity dates | PASS | OK |
| 30 | §2 | Mom: signs over 11–20 d and 1, 2, 3, 6, 12 m | Code takes ½(mean of fast) + ½(mean of slow), not the mean of all 15 | PASS | Minor: state the equal weighting of the two groups |
| 31 | §2 | t* = last US close before local close | `merge_asof` strictly before local date. No look-ahead for AU/UK/DE. CA gets the previous US day (conservative) | PASS | OK |
| 32 | §2 | Admission: CA, AU pass; JP, SE, CH fail; FR/NL/ES/IT not obtainable | Matches RESULTS_LOG | PASS | OK |
| 33 | §2 | Sample 1999 (CA 2002) to 17 Mar 2023, date clustering | CA from 2002-01-04, AU 1999-01-04 | PASS | OK |
| 34 | §2 | Romano-Wolf across 14 tests | 7 families × 2 signals = 14 | PASS | OK |
| 35 | T2 | Calendar pooled -0.201 (-2.67) | -0.201 (-2.67) | PASS | |
| 36 | T2 | Wild p cal 0.008 / RW 0.067 | 0.014 / 0.072 (Monte Carlo) | PASS | |
| 37 | T2 | Change: +0.032 [-0.098, 0.162]; -0.087 [-0.227, 0.052] | Identical | PASS | |
| 38 | T2 | CA -0.368 (-2.12), -0.240 (-2.40) | Identical | PASS | |
| 39 | T2 | CA same-day -0.505 (-3.00), -0.071 (-0.67) | Identical | PASS | |
| 40 | T2 | AU -0.282 (-2.17), -0.161 (-2.64) | Identical | PASS | |
| 41 | T2 | UK -0.247 (-2.74), -0.150 (-3.06) | Identical | PASS | |
| 42 | T2 | DE +0.127 (0.79), +0.116 (1.57) | Identical | PASS | |
| 43 | T2 | US -0.368 (-3.20), -0.206 (-2.84) | Identical | PASS | |
| 44 | T2 | All five -0.265 (-3.35), -0.162 (-2.72) | Identical | PASS | |
| 45 | §3 | -0.32 means 32 bp per 1 pp overweight, "close to" HMM's 17 bp | Per-1pp arithmetic is right. SD of Thr is 0.45 pp, so one SD gives about 14 bp | PASS (arith.) | MISL: compares per-1pp with HMM's "typical" figure. Like-for-like is about 14 bp per SD |
| 46 | §3 | IVX CA t -2.61, AU t -2.59 | -2.61, -2.59 | PASS | |
| 47 | §3 | DK t -2.35 | -2.38 (own kernel) / repo -2.35 | PASS | |
| 48 | §3 | 2 lagged S&P returns: -0.314 | -0.315 | PASS | |
| 49 | §3 | Wald CA=AU p 0.57 | 0.57 | PASS | |
| 50 | §3 | IM p 0.08 | 0.083 | PASS | |
| 51 | §3 | Clark-West AU t 2.27, CA 1.61 | 2.27, 1.61. OOS R²: AU +0.19%, CA -0.37% | PASS | Add that OOS R² is tiny or negative |
| 52 | §3 | Later period alone +0.06 (t 0.43) | +0.064 (0.43) | PASS | |
| 53 | §3 | 1999–2019 -0.18 (t -2.1); 2020–Mar 23 -1.00 (t -3.07) | -0.180 (-2.10); -0.998 (-3.07) | PASS | |
| 54 | §3 | Latest 4-year window zero | Repo +0.003 (to Sep 2026). Own -0.066 (t -0.49) to Jun 2026 | PASS | |
| 55 | §3 | Ex Feb–May 2020: -0.20 (t -2.55) | -0.200 (t -2.51) | PASS (t off by 0.04) | Removing 4 months cuts the coefficient by 38%, so the crash matters a lot |
| 56 | §3 | Test holds controls fixed, which explains the disagreement | True. Freeing all coefficients gives Δ +0.386, t 2.11 (momentum coefficient also shifts, t -2.2) | PASS | Report the full test |
| 57 | §3 | Sub-periods not registered | True. But the registered split (Amend. 6.8: 1999–2008 -0.246, t -1.81; 2009–Mar 2023 -0.376, t -2.58) is not reported in the text | — | MISL by omission |
| 58 | Fig 1 | Windows ending June 2005 to Sep 2026 | `fig2_rolling.csv` starts 2005-12-31. No script in the repo writes this file | FAIL | Fix caption; commit the script |
| 59 | §3 | Placebo weeks +0.17, +0.07, +0.10, none significant | +0.172 (t 1.74), +0.065, +0.095 | PASS | Week 1 is borderline |
| 60 | §3 | Month-end via equity leg | -0.186 (t -2.78) | PASS | |
| 61 | §3 | Cal LP -0.20 at day 1, +0.14 at day 10 | -0.201 / +0.140 | PASS | |
| 62 | §3 | Calendar fails RW and CA same-day | 0.067; -0.071 (t -0.67) | PASS | |
| 63 | §3 | Thr equity leg -0.268 (t -2.77) | Identical. Bond leg +0.053 (t 1.99) | PASS | |
| 64 | §3 | Thr cumulative -0.93 at 10 days, no reversal | -0.945 (t -2.41) / repo -0.927 | PASS | Accumulation is also what a persistent regressor produces mechanically |
| 65 | §3 | Weakens with four more lagged returns | Pooled: coefficient rises to -0.349, t falls from -3.10 to -2.70. Per market (repo): CA t -1.93, AU t -1.67 | PARTLY | MISL: in the pooled test the coefficient is unchanged. Only per-market t-stats drop |
| 66 | §3 | Part may be short-run dynamics, not pressure | 5-day cumulative return alone: -0.002 (t -0.16). Thr survives 5- and 20-day cumulative-return controls (-0.341, t -2.70) | — | The data do not support "it is reversal" |
| 67 | §3/T3 | Global-index signal predicts nothing in UK, DE, AU | Fixed file: UK t -0.11, DE 1.23, AU -1.46 | PASS | OVER/MISL: omits Canada, where the global Calendar has t -3.33 and local Thr becomes insignificant jointly (t -1.87). AU global sample starts only in 2006. T3 says "predicts nothing" without qualification |
| 68 | T3 | Answers mirror the text | As above | — | "Is it local? Yes" overclaims (see 5, 67) |
| 69 | Concl | Similar size, tests fixed before data seen | See 1, 16 | — | MISL as in 1 |
| 70 | Concl | Most of it from 2020–2023 | Full sample to 2026 excluding 2020–23: -0.145 (t -1.81) | PASS | OK, in fact stronger: insignificant without 2020–23 |
| 71 | Concl | "at least in volatile years" | Not tested | UNV | Speculative |
| 72 | Data | Public repository, commit order | Commit order checked (git log). Public status not checkable | UNV | |
| 73 | Appx | Pre-fix run -0.314 (t -3.06) | RESULTS_LOG | PASS (log) | |
| 74 | Notes | About 1,550 words | About 1,630 excluding tables | approx. | |

## 2. Method check

- Formulas match the code exactly (items 26–31): weight drift, 26 bands from 0 to 2.5%, reset after recording, month-end reset, last 5 trading days, par-bond price return with c = y(t-1), and the German zero.
- Timing:
  - The signal at t uses closes up to t, and y = x(t+1).
  - The US signal comes from the last US date strictly before the local date. That is safe for AU/UK/DE, whose closes precede the US close of the same date.
  - For CA (same close), the registered rule throws away the same-day US signal. That is conservative, but it changes the Calendar result (-0.240 → -0.071).
  - Global leg: the first run had look-ahead (MSCI World closes with NY), which was fixed by lagging the global signal for UK/DE/AU. The FX conversion uses Yahoo FX closes, whose timestamps are not the local close, so some timing noise remains.
- Bond yields are forward-filled up to 5 days onto equity dates. On a local bond holiday the bond return is 0 and lands on the next day. This is small but systematic.
- The month-end day is the last date present in each series. The final, partial month (Oct 2026) is mis-flagged, but it lies outside the sample.
- The band-0 component makes Thr partly equal to 0.24·x_t. It is controlled through `ret`.
- Survivorship and selection: markets were chosen by a bond-timing rule, which is not obviously correlated with the outcome. Japan's failure may reflect ETF illiquidity.
- Data snooping: the main risks are the redesign after the UK/DE results (section 4), the choice of the 2019/2020 split, and the averaging of bands (section 3).

## 3. Robustness (pooled CA+AU Threshold unless stated; base -0.321, t -3.10)

| Check | Result | Survives? |
|---|---|---|
| Registered split 1999–2008 / 2009–Mar 2023 | -0.246 (t -1.81) / -0.376 (t -2.58) | Mixed |
| 1999–2019 / 2009–2019 / 2020–Mar 23 / post-Mar 23 | -0.180 (-2.10) / -0.120 (-1.13) / -0.998 (-3.07) / +0.064 (0.43) | Only with 2020–22 or 1999–2008 |
| Full sample to Sep 2026, excluding 2020–2023 | -0.145 (t -1.81) | **No** |
| Excluding Feb–May 2020 | -0.200 (t -2.51) | Yes, 38% smaller |
| Registered restricted change test | +0.032 [-0.098, 0.162] | No change |
| Full-interaction change test | +0.386 (t 2.11) | **Significant decline** |
| Rolling 4-year windows | No window ending before Dec 2019 has \|t\| > 1.7. Windows ending 2020–2024 are significant. From 2025 on, around 0 | Effect concentrated in time |
| By market and period: CA | 1999–08 -0.48 (-2.78); 2009–19 +0.10 (0.64); 2020–23 -1.46 (-2.20); post 0.00 | Unstable |
| By market and period: AU | -0.07 (-0.41); -0.30 (-2.21); -0.63 (-1.40); +0.13 (0.54) | Unstable |
| By market and period: UK | -0.37 (-2.47); -0.14 (-1.07); -0.33 (-1.38); -0.04 (-0.28) | Unstable |
| By market and period: US | -0.53 (-3.12); -0.14 (-1.00); -0.82 (-1.70); +0.28 (0.88) | Unstable |
| Winsorise y at 1%/99% | -0.245 (t -3.31); CA -0.266 (-2.42), AU -0.226 (-2.41) | Yes, 24% smaller |
| Drop 10 / 25 / 50 most influential dates (mostly Mar 2020, Oct–Nov 2008) | -0.284 / -0.194 / -0.210 (t -3.22 / -2.45 / -2.96) | Yes, size falls by up to 40% |
| Single bands (t-stats): 0, 0.5%, 1%, 2%, 2.5% | -2.11, -2.11, -1.50, -1.69, -2.40 | Averaging strengthens the result; 0–2% average gives -0.343 (t -3.09) |
| Plus lags 1–4 / 1–5 of x | -0.349 (-2.70) / -0.326 (-2.51) | Yes |
| Plus equity return t, t-1 | -0.347 (-3.10) | Yes |
| Plus 5- and 20-day cumulative x | -0.341 (-2.70). Cumulative return alone: t -0.16 | Yes, not just reversal |
| Placebo: signal circularly shifted at random (200 draws) | 0 of 200 have \|t\| ≥ 3.10; 95th percentile of \|t\| is 1.98 | Yes |
| HC1 / date cluster / DK(10) / DK(20) | t -3.63 / -3.10 / -2.38 / -2.42 | Yes |
| Without US controls | CA -0.391 (-2.67); AU -0.207 (-1.91) | AU marginal |
| Economic size | 1 SD (0.45 pp) gives about 14 bp next day. Cost-free sign trade: CA Sharpe -0.02, AU 0.29 (AU 0.21 after 1 bp a leg, about 40 flips a year). Post-2023: CA 0.23, AU -0.05 | Small |

**What survives.** In the registered window, a negative pooled Threshold coefficient survives every inference method, outlier treatment, lag control and placebo.

**What does not survive:**
- stability over time (the result disappears without 2020–23);
- per-market sub-period stability;
- equality before and after March 2023 under a full break test;
- meaningful cost-free trading value in Canada.

## 4. Pre-registration integrity

1. **The original pre-registration (5 Oct; commit a3597a3) covered only Germany and the UK.** It specified an error-correction equation with 4 lags, Holm adjustment and the NW+IVX pass rule. Under the corrected analysis, no Threshold result was supported (UK -0.180, t -1.57; DE -0.138).
2. **Amendment 3 (5 Oct, after results).** It changed the equation and the German bond.
3. **Amendment 4 (8 Oct) came after the UK, DE and US results and the US post-2023 reversal (Step 8) had been seen.** It changed:
   - the question;
   - the markets;
   - the return basis. This turned the UK from -0.180 (t -1.57) to -0.247 (t -2.74), and the draft presents that as "once returns are measured on a consistent basis";
   - the main equation;
   - the hold-out test. It replaced separate hold-out regressions with a restricted interaction test, after Step 8 had shown that this design yields an insignificant change in the US.

   The draft's title and abstract present the design as registered "before the data were used". That holds only for the CA/AU data, under rules written after the earlier markets failed.
4. **Amendment 7.1 (alignment fix) was made after the primary results.** It changed -0.314 to -0.321. Table 2 should label these numbers as post-correction.
5. **Bootstrap, Romano-Wolf, IVX-multi, IM and Clark-West (Amend. 8, 12 Oct) were added after the primary results.** The draft cites them as the multiple-testing evidence. The registered Holm adjustment (pooled Thr p = 0.034; Calendar p = 0.085; single new markets fail Holm) is not reported.
6. **The registered stability split (6.8) is omitted from the text.** An unregistered 2019/2020 split and rolling windows are used instead. The draft does label its sub-periods "not registered", but it should report the registered split first.
7. **Commit timing is real but tight.** Amendment 8 was committed at 07:51, the battery script at 07:53 and the results at 07:56 on 12 Oct.

## 5. References

| Reference | Verdict |
|---|---|
| Camanho, Hau, Rey 2022, RFS 35(11) 5228–5274 | VERIFIED (doi 10.1093/rfs/hhac023) |
| Clark, West 2007, JoE 138(1) 291–311 | VERIFIED |
| Da, Larrain, Sialm, Tessada 2018, RFS 31(10) 3720–3755 | VERIFIED |
| Driscoll, Kraay 1998, REStat 80(4) 549–560 | VERIFIED |
| Etula, Rinne, Suominen, Vaittinen 2020, RFS 33(1) 75–111 | VERIFIED (doi 10.1093/rfs/hhz054; add the DOI) |
| Gabaix, Koijen NBER w28967 (2021) | VERIFIED |
| Harvey, Mazzoleni, Melone, NBER w33554 (Mar 2025, rev. Jan 2026); 17 bp; $16bn | VERIFIED. The T1 sample "about 2000" is likely WRONG (≈1998). "One non-US index" is UNVERIFIED |
| Hou, Xue, Zhang 2020, RFS 33(5) 2019–2133 | VERIFIED |
| Ibragimov, Müller 2010, JBES 28(4) 453–468 | VERIFIED |
| Jensen, Kelly, Pedersen 2023, JF 78(5) 2465–2518 | VERIFIED |
| Kayaçetin 2026, JIFMIM 109, 102309 | VERIFIED (30 countries, 1994–2023, 10 bp vs 0) |
| Kostakis, Magdalinos, Stamatogiannis 2015, RFS 28(5) 1506–1553 | VERIFIED |
| McConnell, Xu 2008, FAJ 64(2) 49–64 | Citation VERIFIED. **Table 1 finding WRONG: 31 of 35 countries, not 30** |
| McLean, Pontiff 2016, JF 71(1) 5–32 | VERIFIED |
| Parker, Schoar, Sun 2023, JF 78(5) 2673–2723 | VERIFIED. The "then reversal" detail is plausible but UNVERIFIED in the original |
| Romano, Wolf 2005, Econometrica 73(4) 1237–1282 | VERIFIED |

The draft note says page ranges are still to be checked. All of them are correct as given.

## 6. Verdict

**The headline is defensible in narrow form.** Within the March-2023-ending window, a local Threshold signal predicts next-day equity-minus-bond returns in CA+AU, at about the US magnitude. It is robust to inference method, outliers, lag controls and placebo.

**It is not defensible as an unqualified "pre-registered replication":**
- the effect is concentrated in 2020–22, and is insignificant elsewhere after 2008;
- an unreported full break test rejects stability after March 2023;
- the registered framework was written after the original markets failed.

**Strongest honest headline.** "In two markets selected and tested under rules fixed before their data were used (an amendment written after earlier UK/German tests), local 60/40 Threshold signals predicted next-day equity-minus-bond returns over 1999–March 2023 with a US-sized coefficient (about 14 bp per one-SD deviation). The predictability is concentrated in 2008 and 2020–22 and is absent since 2023."

### Required corrections (most severe first)

1. Disclose the registration history in the abstract, introduction and title area: the original pre-registration (UK/DE) failed for Threshold; Amendments 3–4 were made after the results were seen; the UK basis change came after the UK null.
2. Report the full-interaction break test (Δ = +0.386, t 2.11) next to the registered restricted test, and drop "a formal test cannot separate decline from noise". Also report the full-sample result excluding 2020–23 (-0.145, t -1.81).
3. Report the registered Holm results and the registered 1999–2008 / 2009–2023 split. Label the bootstrap, RW, IVX-multi and IM tests as post-results checks.
4. Fix the size comparison: give about 14 bp per SD, not 32 bp per 1 pp versus HMM's 17 bp.
5. The global-leg claim must include Canada (global Calendar t -3.33; local Thr insignificant jointly) and the 2006 start for AU. Change Table 3's "Is it local? Yes".
6. Note that AU significance depends on the US control (-0.207, t -1.91 without it).
7. "Weakens with lagged returns": pooled it does not (-0.349, t -2.70). Add the cumulative-return controls, which show it is not simple reversal.
8. Fix McConnell and Xu (31 of 35) and the HMM sample start. Soften "one non-US index".
9. Figure 1 caption: the first window ends Dec 2005. Commit the script that writes `fig2_rolling.csv`.
10. Minor items:
    - ex-Feb–May 2020 t is -2.51, not -2.55;
    - state the momentum weighting;
    - report OOS R² (CA negative);
    - report winsorised and influence results;
    - add the Etula DOI;
    - the word count is about 1,630.
