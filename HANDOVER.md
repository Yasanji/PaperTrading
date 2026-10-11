# Handover: state of the paper book, 11 October 2026

Read this first on a new machine or in a new session.

## The book (Book Amendment 3)

| Pod | Strategy | Status | Rules |
| --- | --- | --- | --- |
| A. Systematic macro (code: pod 1) | Trend, 80% | Dry run, days 1-2 passed (8 Oct) | pairs/part4, pods/pod1/pod.py |
| | Sleeve C, month-end rebalancing, 20% | Forward test, first window: batch of 23 Oct, trades 26 Oct | rebal/SLEEVE_C_* |
| | Currency carry | Logged only (book/carry_shadow_log.csv) | carry/sleeveA |
| B. Delta One events (pods 3, 4) | Index events (MSCI, STOXX) | Forward test at 25% | pods/POD3_*, pods/pod3* |
| | Pre-dividend | Passed all tests; full size | pods/POD4_PREREGISTRATION.md, pods/pod4 |
| | Dividend futures (EURO STOXX 50) | Pre-registered 11 Oct; no code yet | pods/divfut/PREREGISTRATION.md |
| Research | Paper 2 rebalancing (Amendment 4, more markets), dividend model, implied-financing monitor (idea) | Not traded | pairs/paper2, delta1/dividends |
| Closed | Pod 2 equity carry, Pod 6 VIX (failed development); Pod 5 REITs parked | | BOOK_AMENDMENT_2, 3 |

Risk: two pods, each NAV x 6% / sqrt(2); Pods 3 and 4 keep NAV / 6 capital. Paper account DUT139070 (IB, port 4002). Prices from Yahoo until the live account has market data (Book Amendment 1).

## Dates

- 23 Oct evening: Sleeve C's first window (trades 26 Oct).
- 30 Oct 17:30 UTC: final MSCI November prediction; commit before 2 Nov. MSCI announces 11 Nov, effective 30 Nov.
- 19 Nov: final STOXX December prediction. STOXX announces about 1 Dec, effective 18 Dec.
- December: dividend futures 2026 contract settles; first forecast score.

## To do, in order

1. **New machine.** Clone the repo; apply book_after_f4326ff.mbox if GitHub is still at f4326ff (Pod 4 live code, Book Amendment 3, dividend futures pre-registration); Python venv (pip install pandas numpy yfinance statsmodels requests ib_async lxml openpyxl scipy); restore delta1/delta1.db from iCloud PaperTrading_backup; IB Gateway and IBC (paper login; recreate ~/ibc/config.ini); GitHub token with push; schedule book/evening.sh (23:15) and morning.sh (07:00) on weekdays.
2. **Contract check** at the new pod risk (cd book && python contract_check.py) with IB Gateway running; update book/config.py CONTRACTS and CHECK_SHARES, CHECK_POD_RISK. 30-year Treasuries and gold may come back in.
3. **Dry run days 3 to 10**, then switch execute.py to --send in the paper account.
4. **Dividend futures code**: daily gap from dividend_forecast_summary against a recorded FEXD price, entry at +/-3%, exit inside +/-1%; add FEXD contracts to the contract check; find an automatic Eurex settlement source.
5. **Pod 4**: delta1/pod4/hk_lots.csv with Hong Kong board lots.
6. **Paper 2**: target **Economics Letters** (2,000 words); plan, UK and German issues and verified references in pairs/paper2/PAPER_PLAN.md. Next: Amendment 4 data checks (official daily 10-year yields, timing test), then rebuild all markets on one basis and run the pooled tests once.
7. **Real money (later)**: household compliance allows broad ETFs (more than ten holdings) and mutual funds freely; single stocks only with prior approval and a 30-day minimum hold; no shorts. Needs its own pre-registered long-only version (for example index additions held 30 days or more).

## Working rules

Every rule is committed before the result it affects; changes are dated amendments. Targets are pushed to GitHub before any order. Writing follows the user's style rules (the human skill).
