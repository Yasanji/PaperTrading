# Pod 6: volatility

Pre-registration, drafted 6 October 2026, before any trade. Yasanji Ratnaike. Every rule is fixed before the first trade. Any change is a dated amendment, committed before the result it affects is seen.

## 1. The question

Does shorting the front VIX future, only when the futures curve slopes upward and implied volatility is above realised volatility, earn the volatility risk premium after costs, with losses capped by sizing and a stop? VIX futures usually trade above the VIX index and drift down towards it as expiry nears. Shorting them earns that roll, but loses heavily when volatility spikes.

**Status.** The pod launches as a forward test at 25% of its target risk, under the portfolio pre-registration. The backtest runs in parallel.

## 2. Instruments and data

1. **Traded:** Cboe Mini VIX futures, front month.
2. **Data:** Cboe's daily settlement prices for every VIX futures contract, the VIX index, and the S&P 500 index for realised volatility.

## 3. The trade

1. **Entry check.** At the close of the first trading day after each VIX futures expiry, the pod shorts the new front future only if both hold: the front future is at least 5% above the VIX index, and the VIX index is above the S&P 500's realised volatility over the previous 21 trading days, annualised. Otherwise it stays flat until the next expiry.
2. **Exit.** At the close three business days before the front future's expiry.
3. **Size.** The number of contracts is set so that a doubling of the front future would lose no more than 3% of the pod's allocated capital, rounded down to whole contracts.
4. **Stop.** If the front future closes 25% or more above its entry price, the position is closed at the next close. This counts as a risk limit, so it overrides the minimum holding period.
5. **Costs.** $1.50 per contract each way in commission, plus 0.05 volatility points of slippage each way.

## 4. Periods

1. **Development:** 1 January 2006 to 31 December 2015, with halves 2006–2010 and 2011–2015.
2. **Hold-out:** 1 January 2016 to 30 September 2026, run once after the development results are committed.
3. **Forward test:** live from the book's launch, at 25% of the pod's target risk.

## 5. Tests and pass marks

Statistics use the pod's daily returns on its allocated capital, after costs. t-statistics are Newey–West with 10 lags.

1. **Development.** Positive return with a t-statistic of at least 2.0, and positive in both halves.
2. **Diversification.** Over the development period, a book holding trend, Sleeve A and Pod 6 at equal risk must have a higher Sharpe ratio than one without Pod 6.
3. **Hold-out.** Sharpe ratio of at least 0.30, a t-statistic of at least 1.0, and a positive return in both halves (2016–2020 and 2021 to September 2026).

If the pod passes all three, it moves to full risk under the portfolio's incubation rule. If it fails any, it is closed and the result is reported.

## 6. Stress tests

Reported, descriptive only: the 2008 financial crisis, the August 2015 sell-off, February 2018, March 2020 and 5 August 2024, each with the period it falls in. For each, the report states whether Pod 6 lost money at the same time as the carry sleeves.

## 7. Reporting

Every result is committed before the next test. No rule, threshold or period changes after a result is seen.
