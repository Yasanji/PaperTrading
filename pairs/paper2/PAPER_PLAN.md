# Paper 2: plan for the Economics Letters version

Written 11 October 2026, after the desk rejection by Finance Research Open (FINR-D-26-00925, "does not meet the required quality standards") and before the Amendment 4 data checks. Target: **Economics Letters**, up to 2,000 words excluding references; it takes short empirical results, not comments. Fallback: Finance Research Letters (under 2,500 words; prefers replications across countries; single-country replications out of scope). Full author guides still to be read: the user to save them from ScienceDirect.

## Issues found in the submitted version (all logged in the repo)

UK
1. **Return basis mismatch.** FTSE 100 price index (no dividends) against gilt returns that include carry: the equity-minus-bond return and the drift of the 60/40 weight are biased against equities by the dividend yield. The UK month-end result is the paper's only positive one, so it must be re-run on one basis (Amendment 4.4: both legs excluding income, total return as a check).
2. **Hold-out claim too strong.** "Absent from the hold-out" rests on a separate regression over about 900 days, with 48% power. The right test is the change in the coefficient after March 2023 (Amendment 4.6), which on the US data is not significant.

Germany
3. **Bond timing.** Bundesbank daily yields are not taken at the close (0.47 same-day and 0.47 previous-day correlation with a Bund ETF); replaced by the ECB euro-area AAA curve, which starts in 2004, so the German sample starts in 2005 and the bond is AAA, not Bunds.
4. **Equity basis.** DAX total return against a bond with carry; under Amendment 4.4 the DAX price index is used with the bond excluding carry.
5. **Pre-registered equation omitted two terms** (Calendar alone and the last-week indicator), which produced false German results; fixed in Amendment 3. This goes to an appendix on deviations, with one sentence in the main text.

Both markets and the US
6. **Local-only assumption.** UK and German investors hold much of their equity abroad, so a local 60/40 portfolio may be a weak proxy; Amendment 4.7 adds a global equity leg as a check.
7. **60% target** untested; 40% and 30% checks pre-registered.
8. **Equation differs from Harvey, Mazzoleni and Melone** (five lagged returns against one); their exact equation becomes the main one.
9. **Standard errors:** Newey-West decides, HC1 reported alongside.
10. **US replication:** Threshold now -0.407 against -0.414 published (after fixing the data start); the Calendar gap (-0.200 against -0.303) remains unexplained.
11. **Only two countries.** Amendment 4 adds France, the Netherlands, Spain, Italy, Sweden, Switzerland, Japan, Canada and Australia, each admitted only if its yield passes the timing test, with a pooled panel as the main test.

## New findings since submission

- Harvey, Mazzoleni and Melone is a working paper (January 2026), revise and resubmit at the Journal of Finance. Their footnote 32 says results become "even stronger" through 2025; on index, futures and ETF data we find positive, insignificant coefficients over March 2023 to December 2025, and the change after March 2023 is not significant either way (Step 8). The paper can say only that footnote 32 is not reproduced.

## Shape of the letter (modelled on Ratnaike 2012, Economics Letters 117, 375-378)

1. Introduction: the gap, three numbered contributions (pre-registered out-of-sample test across many markets; local signals separated from US ones; the US after March 2023), roadmap.
2. Data and method: signals, one equation, inference.
3. Results: one table, every market and the pooled panel, main sample and change after March 2023; a stylised-facts table of signal size by market.
4. Conclusion: what it means for the cost estimates of fixed-allocation investors.
Online appendix: deviations from the pre-registration, data checks, power.

## References (verified 8 October 2026)

Add: Camanho, Hau and Rey (2022, RFS 35(11)); Da, Larrain, Sialm and Tessada (2018, RFS 31(10)); McLean and Pontiff (2016, JF 71(1)); Hou, Xue and Zhang (2020, RFS 33(5)); Harvey, Liu and Zhu (2016, RFS 29(1), pages to confirm); Gabaix and Koijen (2021, NBER 28967); Faff (2023, PBFJ 79); Andonov, Eiling and Xu (working paper, co-authors to confirm). Update Harvey, Mazzoleni and Melone to the January 2026 version. Cut EY (2025), IHS Markit/DIRK (2021), possibly AFME (2025). Kayaçetin (2026): 30 countries, average month-end returns, not a signed signal.

## Order of work

1. Amendment 4 data checks (yields and timing test, bond returns only).
2. Rebuild every market on one basis; run the pooled and change-after-2023 tests once.
3. Write the letter around whatever the panel shows.
