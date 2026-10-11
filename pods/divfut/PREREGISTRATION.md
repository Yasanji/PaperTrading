# Dividend futures: EURO STOXX 50

Pre-registration, drafted 11 October 2026, before any trade and before the next futures price is recorded. Yasanji Ratnaike. A strategy of the Delta One events pod (Book Amendment 3). Every rule is fixed before the first trade. Any change is a dated amendment, committed before the result it affects is seen.

## 1. The question

Does a bottom-up forecast of EURO STOXX 50 dividends, built from company-level estimates and declared payments, predict the final settlement of the index dividend futures better than the futures price does, and does trading the difference earn money? Pricing dividends is core Delta One work: the desk is long or short dividend exposure through every future, swap and structured product it holds.

**Disclosure.** The model (delta1/dividends/model.py) was built on 8 October 2026 and checked once against 2025 (162.5 points against a final settlement of 164.99, 1.5% low). On 8 October it gave 174.2 for 2026 against a future of 172.30 (+1.1%) and 185.1 for 2027 against 189.10 (-2.1%). The thresholds below were set after seeing those numbers. They are set from the model's measured error, not to make a trade happen; at these numbers neither contract trades. There is no backtest: free history of company-level forecasts does not exist, so the test is the forward record.

## 2. Instruments and data

1. **Traded:** Eurex EURO STOXX 50 Index Dividend Futures (FEXD), the December contracts of the current and the next year (December 2026 and December 2027 at the start), 10 euros per index point, cash-settled to the dividends paid in each year. The contracts are added to the contract check before the first trade.
2. **Forecast:** model.py, run by the nightly divfcst job and stored in dividend_forecast_summary. Current year: realised points plus declared and forecast interims. Next year: the bottom-up forecast (company inputs in dps_inputs.csv, all others growing 5%), with the range from 3% to 7% growth recorded alongside.
3. **Prices:** the Eurex daily settlement price. Until it can be collected automatically, it is recorded by hand (collect.py fexd) with its source and time, and a day without a recorded price is a day without a decision.
4. **Company inputs** in dps_inputs.csv are revised only from published sources (company declarations, consensus pages), each change committed with its source and date before it is used.

## 3. Signal and trade

1. **Gap.** For each contract, gap = (forecast minus future) / future, using the forecast and the future of the same evening.
2. **Entry.** Long if the gap is above +3%, short if below -3%. The 3% is twice the model's only measured error (1.5% in 2025).
3. **Exit.** Close when the gap is back inside +/-1%, when the gap changes sign, or at the close of the contract's last trading day, whichever comes first. A closed position re-enters only through rule 2.
4. **Size.** Notional of 10% of the strategy's allocated capital (NAV / 6, as for Pods 3 and 4) per contract year, in whole contracts, at most two positions (one per year). No hedge: the trade is a view on dividends against the market's price of them.
5. **Stop.** If a position loses 25% of its notional, it is closed at the next close. A stop is a risk limit and overrides the minimum holding period.
6. **Costs.** One tick (0.1 points) of slippage and 1 euro commission per contract each way.
7. **Timing.** Decisions after the evening divfcst run; orders through the book's chain, executed at the next Eurex settlement.

## 4. Record

Every evening, whether or not a position is held: the forecast for each contract year (with its range), the future, the gap and the decision. Each December the final settlement is recorded against the forecast and the future at fixed horizons before expiry (3, 6 and 12 months).

## 5. Evaluation

The strategy is scored at each December settlement, starting December 2026.

1. **Forecast test (the main test).** Over all settled contracts, the mean absolute error of the forecast at 3, 6 and 12 months before expiry, against the mean absolute error of the future at the same dates. The strategy passes if the forecast's error is lower at the 3-month and 6-month horizons.
2. **Trading record.** P&L after costs, reported per contract.
3. **Decision.** After the December 2027 settlement (two contract years): continue if the forecast test passes; close if the forecast is worse than the future at both horizons, or if cumulative losses exceed 25% of the strategy's allocated capital at any time. No promotion to real money is considered before then, and only by amendment.
