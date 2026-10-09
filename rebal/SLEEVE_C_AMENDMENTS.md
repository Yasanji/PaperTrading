# Sleeve C: amendments

## 1. Execution timing and implementation

Made on 9 October 2026, before the sleeve trades.

1. **One-day lag.** The book writes targets after the US close on day D and trades them at settlement on the next trading day E. The position held at E's close therefore uses the signal at D's close, not E's. On the first day of the window the direction comes from the signal on the trading day before the window. The pre-registered window (closes of the last five trading days of the month, flat at the close of the first trading day of the next month) is unchanged. The log also records each day's signal, so the regression in s.7 is run both on the traded timing and on same-day signals.
2. **Netting with trend.** Sleeve contracts are added to the trend and carry total after it is rounded. The book's no-trade band and minimum holding apply to the trend and carry part only, which is the current position minus the sleeve's previous target. A position's opening date is still recorded for the whole position, so a sleeve trade that changes the sign of the total can restart the holding clock for trend. This is accepted and logged.
3. **Calendar.** Trading days follow the NYSE holiday calendar, written into sleeve_c.py for 2026 and 2027. The run warns from 1 December 2027 until it is extended.
4. **Data.** S&P 500 closes from Yahoo Finance and 10-year par yields from the US Treasury, cached; if a download fails, the cache is used and the run says so. If no close exists for day D, the run stops and the kill switch applies.
