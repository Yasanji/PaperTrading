# Paper 2: audit of set-up, assumptions and approach

8 October 2026, after Step 8 and before Amendment 4. Read from local_data.py, step2_main.py, step6_corrected.py and step8_us_through_2025.py. Each item: what the code does, whether it is right, and what Amendment 4 should fix. Nothing here has been re-run on European data.

## A. Problems that change results or claims

1. **Hold-out tested on its own.** Hold-out coefficients come from a separate regression on about 700 to 900 days, which re-estimates every control. Step 8 follow-up showed the change in the US coefficients after March 2023 is not significant (t 0.2 to 0.5). The claims "absent from the hold-out" for the US and UK are not supported by this test. Fix: test the change in each rebalancing coefficient after the hold-out date, with the other coefficients held at full-sample values, and pool markets for power.
2. **UK legs are on different bases.** The FTSE 100 series (^FTSE) is a price index, while the gilt return includes carry, so the UK equity-minus-bond return and the drift of the 60/40 weight are both biased against equities by the dividend yield (roughly 3 to 4% a year). Germany (DAX total return against bond with carry) and the US (price index against bond price change, no carry) are each internally consistent, but on different bases from each other. Fix: one basis for every market, either both legs total return or both excess of cash, fixed before any new data is used.
3. **The signal assumes local investors hold local equity and local bonds only.** UK and German pension funds hold much of their equity abroad, so a 60/40 portfolio of the FTSE 100 and gilts may be a weak proxy for the flows the paper tests. This is the paper's main economic assumption and it is untested. Fix: state it, and add a pre-registered variant with a global equity leg (for example MSCI World in local currency) against the local bond. Ownership figures need sources before they are quoted.

## B. Departures from Harvey, Mazzoleni and Melone to state or align

4. **Lagged returns.** Their equation has the current day's return only; ours has the current and four previous days (the error-correction form in the pre-registration). Results are therefore not the same equation as theirs. Fix: report their exact equation as the main specification and ours as a check, or the reverse, decided in Amendment 4.
5. **Standard errors.** They report heteroskedasticity-robust errors; we use Newey-West with the lag rule floor(4(T/100)^(2/9)). Keep Newey-West but report HC1 alongside for comparability.
6. **60% target.** UK defined-benefit schemes hold far less than 60% in equities. The signal is a deviation from target, so the target level matters less than the drift, but it is untested. Fix: pre-register 40% and 30% targets as checks.

## C. Checked and correct

7. **Timing.** The local signal at day t uses closes up to t and predicts the return from t to t + 1. The US signal enters from the last US close strictly before local day t (merge_asof, backward, exact matches excluded), so no US information after the local close is used.
8. **Month-end and last week.** Month-end is the last trading day present in each market's data; the last week is that day and the four before it, matching their definition.
9. **Threshold signal.** Average over bands 0% to 2.5% in 0.1-point steps (Amendment 1), reset to target when the band is breached. Matches their equation (2).
10. **Momentum.** Signs of cumulative equity-minus-bond returns over 11 to 20 days and over 21, 42, 63, 126 and 252 days, averaged, as in their paper. Needs a year of data before the sample starts (the Step 1 gap).
11. **Multiple testing.** Holm adjustment across all 21 main-sample tests.

## D. Approximations to state

12. **IVX** is applied to one regressor at a time after removing the others (Frisch-Waugh), with a heteroskedasticity-robust variance and no finite-sample correction. This approximates Kostakis, Magdalinos and Stamatogiannis (2015), whose test instruments all persistent regressors jointly.
13. **Hodrick errors** use the demeaned one-day return in place of the residual under the null.
14. **Bootstrap** imposes the null by dropping the tested regressor and resamples residuals in blocks with mean length 21 days; 499 draws.
15. **Bond returns from yields.** Constant 10-year maturity: par-bond repricing for the US and UK, continuously compounded spot for Germany. Each market's series must pass the same check against a traded bond series that found the Bundesbank timing problem.
