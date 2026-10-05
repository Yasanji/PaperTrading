# Paper 2: Local rebalancing flows in European and UK equity markets

Design, fixed before any European data is tested, 5 October 2026. Yasanji Ratnaike.

## The question

Do local month-end rebalancing flows by European and UK investors predict their own equity markets, once the US rebalancing signal is taken into account? Harvey, Mazzoleni and Melone show that US rebalancing signals predict US returns and an aggregate index of non-US markets (MSCI ACWI ex US). They do not build signals from European or UK markets, test countries separately, or compare local signals with the US one.

**The contribution is methodological**, given that rebalancing flows are already well studied. It has three parts:

1. A pre-registered, out-of-sample test of a published result in new markets.
2. A separation of local rebalancing flows from US flows spilling over, with the UK as a contrast case, given that UK defined-benefit pensions hold far less equity than the 60/40 benchmark assumes.
3. An error-correction model that separates the long-run correction of deviations from the target weight from the short-run dynamics around month-end, which shows whether the effect is temporary price pressure from flows.

**The credibility argument.** The paper applies the method of the first paper: every test below is written down and committed to GitHub before any European or UK data is run. The US results are already published, so the replication in Step 1 checks the code. The European and UK results are new, and the commit history shows they were specified before they were seen.

## Step 1: replicate the US signals

Before any European data is used, the code must reproduce the published US results, so that any later difference comes from the markets and not from the construction.

**Portfolio.** A simulated 60/40 portfolio of the S&P 500 and the 10-year Treasury note, whose equity weight drifts each day with the two returns. Harvey, Mazzoleni and Melone use S&P 500 and 10-year Treasury note futures; free futures data does not cover their full sample, so the replication uses the S&P 500 index and 10-year Treasury yields, and is expected to be close but not exact.

```latex
w_{t+1} = \frac{w_t (1 + R^{eq}_{t+1})}{w_t (1 + R^{eq}_{t+1}) + (1 - w_t)(1 + R^{bond}_{t+1})}
```

**Signals.** Each signal is the equity weight minus 60% at the end of the previous day.

1. Threshold: the portfolio is reset to 60/40 whenever the weight moves outside a band around the target, and the signal is the average across bands from 0% to 2%, as in Harvey, Mazzoleni and Melone.
2. Calendar: the portfolio is reset on the last business day of each month, with the signal interacted with an indicator for the last week of the month.

**Regression.** The next day's equity return minus the bond return on both signals, with their controls and heteroskedasticity-consistent standard errors, over 10 September 1997 to 17 March 2023.

**Pass mark.** Both signal coefficients negative and close in size to the published estimates. If they are not, the code is corrected until they are, and nothing proceeds to Europe until then.

## Markets and data

Two local 60/40 portfolios are built in exactly the same way as the US one, each from a local equity index and the local 10-year government bond. The DAX includes dividends and the FTSE 100 series does not; at about 3% a year, dividends add roughly 0.25 percentage points a month to the equity drift, against bands of up to 2 points, so the German case is also run on the DAX price index from March 2013 as a check.

| Market | Equity | Bond | Sample |
| --- | --- | --- | --- |
| Germany (core eurozone) | DAX, a total-return index, from 1990; the DAX price index from 2013 and the EURO STOXX 50 from 2007 as checks | 10-year Bund returns computed from Bundesbank daily yields | 1999 to 2026 |
| UK | FTSE 100, from 1990 | 10-year gilt returns computed from Bank of England daily yields | 1999 to 2026 |

**Bond returns from yields.** The daily return is the carry from the previous day's yield, minus duration times the change in yield, plus a convexity term. Returns on government bond ETFs, available from 2008, serve as a check on this construction.

**Time zones.** European markets close before the US market. The local signal at day t uses local closes at t and predicts local returns at t + 1. The US signal for day t is not known until after Europe closes, so it enters with a one-day lag, as Harvey, Mazzoleni and Melone lag their signal for non-US markets.

**Confirmed on 5 October 2026, before any returns were computed.** The Bank of England's daily 10-year gilt par yield runs from November 1993 and the Bundesbank's daily 10-year zero-coupon yield from August 1997, both to October 2026 with no gap longer than six days, so the main sample and the hold-out are fully covered. Bund returns are computed from the zero-coupon yield and gilt returns from the par yield, each with its own duration and convexity.

## The model: long-run adjustment and short-run dynamics

The regression is written as an error-correction model, which separates the long-run pull back to the target weight from the short-run dynamics around it.

```latex
r^{eq}_{t+1} - r^{bond}_{t+1} = \alpha \, d_t + \sum_{k=0}^{K} \beta_k \, (r^{eq}_{t-k} - r^{bond}_{t-k}) + \gamma \, C_t \, L_t + \delta \, US_{t-1} + \varepsilon_{t+1}
```

Here d is the local Threshold deviation of the equity weight from 60%, C the local Calendar signal, L an indicator for the last week of the month, and US the lagged US signal. The lag length K is fixed at 4, one trading week, and the controls listed under the tests are added to the regression.

**Long run.** The coefficient α is the speed at which deviations from the target weight are corrected through rebalancing flows, and its half-life is reported in days. It is compared between local and US signals and between Germany and the UK.

**Short run.** The Calendar term, the lagged returns and the US signal capture the flows around month-end and their spillover. The local projections in hypothesis 5 show whether this short-run pressure reverses while the long-run correction holds.

**The equilibrium.** The equilibrium here is the investors' target weight, and not a long-run relation between equity and bond prices, which are not expected to revert to each other. Returns and the constructed deviation are both stationary, so no cointegration test is needed.

**The threshold.** The primary test uses the signal averaged across bands from 0% to 2%, as in Harvey, Mazzoleni and Melone. A threshold error-correction model with the band estimated from the data, following Balke and Fomby (1997) and Hansen and Seo (2002), is reported only as a secondary result.

**Inference.** The Threshold deviation is persistent, which can overstate significance in a predictive regression (Stambaugh, 1999). Alongside the heteroskedasticity-consistent and Newey–West standard errors, each main coefficient is tested with the IVX method of Kostakis, Magdalinos and Stamatogiannis (2015) and with a bootstrap that preserves the signal's persistence.

## The tests, fixed in advance

Five hypotheses are tested for each market, with the error-correction regression above and the next day's local equity return minus the local bond return as the dependent variable.

1. **Local Threshold.** The local Threshold signal predicts local returns negatively.
2. **Local Calendar.** The local Calendar signal predicts negatively in the last week of the month.
3. **Local against US.** The local signals stay negative and significant with the lagged US signals in the same regression. Because the two are correlated, the local signal is also used after removing the part explained by the US signal, and both versions are reported.
4. **The UK contrast.** The local adjustment coefficient is smaller in the UK than in Germany, tested as the difference between the two coefficients estimated in one stacked regression.
5. **Immediate and dynamic effects.** The effect of each local signal is traced day by day over the following ten trading days, with a local projection at each horizon. The effect counts as reversing if the cumulative effect at day 10 is below half the day-1 effect and not significantly different from zero, using Hodrick (1992) standard errors, as Harvey, Mazzoleni and Melone do for longer horizons; if it does not reverse, something other than flow pressure is at work.

**Controls.** As in Harvey, Mazzoleni and Melone: momentum, measured as the average of medium and slow sign-based signals, and the trailing one-day local excess return, with heteroskedasticity-consistent standard errors as in their paper and Newey–West ones alongside. Their US macroeconomic and sentiment controls are not used in the local regressions.

**Periods.** The main sample runs from January 1999 to 17 March 2023, matching the end of their sample. The period from 20 March 2023 to September 2026 is held back and run once at the end, for both the US replication and the local signals.

**Pass mark and trial count.** A hypothesis is supported only if the coefficient has the predicted sign, its Newey–West t-statistic is beyond 2, and the IVX test rejects at the 5% level, with the bootstrap reported as a check. The design produces about 24 coefficient tests across two markets, including the cumulative effects at days 5 and 10, so the paper also reports p-values adjusted for multiple testing by the Holm method, and every test run is listed, whatever its result.

## What each answer would mean

Every outcome is reportable, which is the point of fixing the tests in advance.

| Result | Interpretation |
| --- | --- |
| Local signals predict returns, and survive the US signal | European and UK investors' own rebalancing moves their markets, independently of US money |
| Local signals predict returns, but not once the US signal is included | The effect in Europe is mainly US rebalancing spilling over |
| Neither local nor US signals predict returns | The published effect does not carry over to these markets, which is itself a useful out-of-sample result |
| Effect present in Germany, weak or absent in the UK | Consistent with the mechanism, given UK pensions' low equity allocations |
| Effect present in the main sample, absent in the hold-out | The effect may have been traded away after publication |

The dynamic test adds a further distinction. An effect that reverses within days indicates temporary price pressure from rebalancing flows, while an effect that persists points to a different cause, such as the flows carrying information.

## Economic significance

The local signals are also tested as an implementable strategy, as in Harvey, Mazzoleni and Melone, to show whether the effect matters economically as well as statistically.

**The trade.** Long equity futures and short bond futures when the signals show equities underweight, and the reverse when they show equities overweight. For Germany that is DAX against Bund futures, and in the UK FTSE 100 against long gilt futures.

**What is reported.** The strategy's return, Sharpe ratio and turnover after costs of 1 basis point a trade, for the main sample and the hold-out.
