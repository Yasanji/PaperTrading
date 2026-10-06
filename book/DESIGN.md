# Daily trading job: design

Drafted 6 October 2026. The job turns the pre-registered rules into orders in the Interactive Brokers paper account, and records everything in delta1.db and on GitHub.

## 1. Principles

1. **The rules decide; the job only executes.** Every number comes from a committed pre-registration.
2. **Decide, then commit, then trade.** Targets are committed to GitHub before any order is sent.
3. **Fail safe.** Any doubt (missing data, a mismatch, a breached limit) means no orders and an alert.
4. **Dry run first.** Every stage runs without sending orders until its output has been checked.
5. **One record.** Every step writes to delta1.db: data, signals, targets, orders, fills, positions, risk and events.

## 2. Components

| Component | Job |
| --- | --- |
| Collector | Collects the day's data: delta1's existing jobs, plus futures prices from Interactive Brokers |
| Pods | Six modules, one per pod, each turning data into target weights under its own rules |
| Book | Applies the portfolio rules: risk shares, the 6% volatility target, caps, the no-trade band and minimum holding periods |
| Risk | Checks drawdown limits, margin, the cash buffer, gross exposure and the stress check |
| Targets | Writes target positions to a file and commits it to GitHub |
| Orders | Compares targets with the account's actual positions and writes the orders needed |
| Execution | Sends orders through Interactive Brokers' API (ib\_async, the maintained successor to ib\_insync, via IB Gateway) |
| Reconciliation | Matches fills and positions against targets, using the broker's Flex Query |
| Report | Writes a daily summary and the monthly report |

## 3. The pod interface

Every pod is a module with the same three functions, so the book treats them alike.

1. **targets(as\_of):** returns each instrument's target weight on the pod's capital, using only data available on that date.
2. **status():** returns the pod's stage (forward test or full risk) and its last rebalance date.
3. **checks():** returns any problem with its inputs, such as stale or missing data, which stops the pod trading that day.

## 4. The daily timeline (London time)

| When | Step |
| --- | --- |
| 22:30 | Collector starts |
| When the collector finishes | Pods compute targets; the book sizes them; risk checks run |
| When the checks pass | Targets are committed to GitHub; orders are written to a file; a summary is logged and sent as a notification |
| Evening, before 07:00 | During incubation, you review and approve the orders (approve.py). Unapproved orders are never sent |
| 06:45 next day | IB Gateway connection checked |
| 07:00 | One batch of orders is sent: close orders for shares, which Interactive Brokers holds until each market's close, and time-conditioned market orders for futures, timed shortly before each settlement |
| After the US close | Fills are reconciled; positions, NAV and risk are stored |

Each evening step starts when the previous one finishes, not at a fixed time, and any failure stops the chain. Steps tied to the US close follow its actual time, since UK and US clocks change on different dates. The Mac must be on or asleep (not shut down) in the evening and at 07:00. A missed run sends no orders: the next run starts again from the account's actual positions.

## 5. Instruments

1. **Contract map.** A table maps each instrument to its Interactive Brokers contract: micro futures for trend, CME currency futures for carry, shares and index futures for the equity pods, Mini VIX futures for volatility. No instrument outside the map can be traded.
2. **Rolls.** Futures roll five business days before the first notice day or the last trading day, whichever comes first, so that no physically delivered contract (such as micro gold or micro silver) is held into delivery. VIX futures roll at the pod's own exit date.
3. **Sizing check.** Before launch, every target position is checked against its contract size, under the portfolio rules.
4. **Holidays.** Each exchange's holiday calendar is applied, so no order goes to a closed market.
5. **Borrow.** Before each short, borrow availability is checked. A short that cannot be borrowed is skipped and recorded.
6. **Currency.** The account is in US dollars. Each day the job converts currency so that no foreign-currency balance is negative, and records the conversions and any financing cost.
7. **Corporate actions.** Splits, ticker changes and dividends are applied in reconciliation before differences are flagged.

**Instrument check (6 October 2026).** Verified against CME and Cboe product information:

| Instrument | Status |
| --- | --- |
| Micro futures for crude oil, natural gas, gold, silver, copper, S&P 500 and Nasdaq-100 | Exist |
| Micro currency futures | Exist only for the euro, Australian dollar, sterling, Swiss franc and yen. No micro Canadian or New Zealand dollar |
| Micro Treasury futures | Exist only for the Ultra 10-Year and Ultra T-Bond. No micro 2-year or standard 10-year; micro yield futures trade in yield, not price |
| Mini VIX futures | Exist: $100 times the VIX, tick $1. Market orders accepted only in regular trading hours |

Not yet verified: STOXX Europe 600 and Hang Seng index futures; close-of-day order types on each European exchange; the paper account's trading permissions and whether its market data is live or delayed; Interactive Brokers' commissions; borrow availability. Build step 1 requests Interactive Brokers' contract details for every instrument in the map, and the contract-size check then decides which markets stay in. Treasury, Canadian dollar and New Zealand dollar futures, which have no suitable micro size, are either left out or replaced by amendment, once the check shows which fail.

## 6. Safeguards

1. **Paper account only, enforced.** Before sending anything, the job checks that the connected account matches your paper account number, stored privately on the Mac, and that it is connected through the paper Gateway's port. Any other account or port stops the job.
2. **Orders match the commit.** Orders are generated only from the committed targets file, and the file's checksum is checked against the GitHub commit before sending. If the commit failed or the file differs, no orders are sent.
3. **No duplicates.** Each day's orders carry a unique batch ID. A batch that has already been sent cannot be sent again, even if the job reruns.
4. **Order limits.** No single order above 10% of NAV in notional value. Total orders in a day above 50% of NAV, except risk-limit closes, stop the batch for review.
5. **Sanity checks.** An order is held back if its reference price differs by more than 10% from the last close, or its size is more than twice the size of its target position, which allows a full reversal but catches errors.
6. **Kill switch.** Any of the following stops all new orders and records an event: data more than one business day old for any targeted instrument; a position that does not match the record by more than one contract or 1% of its value; a breached limit; IB Gateway not connected; a NAV move over 5% in a day that differs by more than 1% of NAV from the profit and loss calculated from positions and prices.
7. **Approval during incubation.** Orders wait for your approval. Without it by 07:00, nothing is sent.
8. **Read-only first.** Until the execution stage is tested, the Interactive Brokers API runs in read-only mode, so the job cannot send orders even by mistake.
9. **Credentials.** No password, key or account number is stored in the code or on GitHub.

## 7. Build order

1. Contract map and IB Gateway connection in read-only mode: read positions, request Interactive Brokers' contract details for every instrument, and run the contract-size check.
2. Pod 1 (trend and carry) targets and the book's sizing, in dry run.
3. Targets committed to GitHub; orders written to a file.
4. Reconciliation against the broker's records.
5. Execution of approved orders in the paper account.
6. Pods 2–6 added one at a time, each in dry run first.
7. Scheduling, then the daily and monthly reports.

## 8. Operations

1. **IB Gateway.** Kept logged in with IBC, the standard tool for this. A check at 06:45 confirms the connection before the order batch.
2. **GitHub.** Commits use an SSH key, so they run without a password prompt.
3. **Manual inputs.** Pods 3 and 5 read set-format files from an inputs folder (MSCI predictions, REIT NAVs). See Section 10.
4. **Alerts.** Every run ends with a notification: what was done, or why it stopped. Every alert is first written to delta1.db with its time, severity (information, warning or critical) and the time it was acknowledged. An unacknowledged critical alert blocks the next order batch.
5. **Backups.** delta1.db is copied weekly to a second location.

## 9. Checks before building

1. Whether Interactive Brokers' Flex Queries work for paper accounts. If not, reconciliation uses the API's own trade records.
2. Whether the Mac's management profile (Microsoft Intune) allows IB Gateway and IBC to run.

## 10. Manual inputs

1. **Path.** File, then validation, then a GitHub commit, then the database, then the pod. A pod reads inputs only from the database.
2. **Formats.** MSCI predictions: review, index, ISIN, ticker, action (add or delete), rule, margin and the date of the data used. REIT NAVs: ticker, period end, NAV per share, currency, publication date and the source URL.
3. **Validation.** Required fields present; no date in the future; values in range (NAV above zero, discount within ±80%); no duplicates. A file that fails is rejected whole, with an alert.
4. **Point in time.** A pod uses an input only if it was committed before the signal date. Pod 3 trades a prediction only if it was committed at least 20 trading days before the effective date. Pod 5 ignores any NAV more than 7 months old.
5. **Corrections.** A correction is a new row with a later commit. Earlier rows are never edited.

## 11. Reconciliation

1. **Before trading (07:00).** The account's positions are compared with the expected positions in delta1.db before any order is sent.
2. **After the US close.** The day's fills from the API are matched against the orders sent.
3. **Next morning.** Interactive Brokers' Flex Query statement, the official record, is matched against both. If it is not available, the API's trade records are used.

| Gap | Examples | Action |
| --- | --- | --- |
| Explained | Corporate action, futures roll, partial fill, rejected order (for example, no borrow), currency rounding | Recorded with its reason and resolved automatically |
| Unfilled order | An order not executed | Not chased during the day; the next run starts from actual positions |
| Unexplained | Any difference beyond one contract or 1% of a position's value | Kill switch: no new orders and a critical alert. Any corrective trade needs your approval |
| Missing records | Neither the Flex Query nor the API's records available | Kill switch until the records are found |

## 12. Specifications

### How the job works

1. **Weights to orders.** Target quantity is the target weight times the pod's allocated capital, divided by price times contract multiplier times the exchange rate to dollars. Futures round to the nearest whole contract, and a target below half a contract becomes zero. Shares round down to whole shares. Positions under $500 are dropped. The no-trade band applies after rounding.
2. **Targets file.** book/targets/YYYY-MM-DD.csv, one per signal date, with date, pod, instrument, Interactive Brokers contract ID, target quantity, target weight, reference price and exchange rate. Committed with the message "targets YYYY-MM-DD", and its SHA-256 checksum stored in delta1.db.
3. **Contract map.** book/contract\_map.csv, with instrument, pod, symbol, exchange, currency, security type, multiplier, contract ID, settlement time, and first notice and last trading dates for each contract held. Changed only by commit. Checked against Interactive Brokers' contract details at each run; any mismatch blocks that instrument and raises an alert.
4. **Futures prices.** Taken in the evening run from Interactive Brokers' daily bars. In build step 1, five days of these are compared with the exchanges' published settlement prices. If they differ by more than 0.1%, the exchanges' settlement files are used instead.
5. **Order types.** Shares: close orders where Interactive Brokers' contract details list them for that exchange; otherwise limit-on-close orders, with the limit 5% beyond the last close. Futures: market orders activated 10 minutes before each product's settlement time. Mini VIX futures only within regular trading hours.

### Safety processes

6. **Clearing the kill switch.** Only you can clear it, with clear\_kill.py, the event's ID and a written reason, all recorded. It can be cleared only once the cause is recorded and reconciliation shows no unexplained gap. Trading then resumes at the next scheduled run, never immediately.
7. **Approval.** approve.py shows each order (pod, instrument, side, quantity, value, share of NAV and reason: signal, roll or risk), the day's total turnover and the check results. You can approve all, reject all, or reject single orders; every decision is recorded. Approval is required for the first 8 weeks after launch, and for 4 weeks after any pod is added or the execution code changes.
8. **The 50% daily cap.** A batch over the cap is held. You review it in approve.py and either approve it with a recorded reason or reject it.
9. **Alerts.** Sent as Mac notifications and written to delta1.db. Acknowledged with ack.py and the alert's ID. Email can be added later.
10. **Dry run.** Each stage runs dry for at least 10 trading days. It passes if a hand recalculation of three instruments a day matches the targets, simulated fills reconcile with no unexplained gap, and no code error triggers the kill switch.
11. **Adding pods.** The next pod is added only after the previous one has passed its 10-day dry run and traded live for 5 trading days with no unexplained gap.

### Data sources

12. **Holidays.** An order is sent only if Interactive Brokers' contract details show the market trading that day. The exchange\_calendars library is a second check; any disagreement holds the order and raises an alert.
13. **Borrow.** Checked at 07:00 from Interactive Brokers' shortable-shares data. A short is sent only if the shares available cover the order; otherwise it is skipped and recorded.
14. **Corporate actions.** Detected from three sources: position changes not explained by fills, the dividend and split records in delta1.db, and the Flex Query's corporate-actions section. Matched in reconciliation.
15. **Roll dates.** First notice and last trading dates are taken from the CME and Cboe calendars, stored in the contract map for each contract held, and checked against Interactive Brokers' contract details.
16. **Currency.** At 07:00, after orders are set, any currency whose balance would fall below the equivalent of minus $1,000 is bought with dollars. Foreign balances above the equivalent of $50,000 are converted back to dollars each Friday. Every conversion and its cost is recorded.

### Operations

17. **IB Gateway logins.** IBC logs in to the paper account each day. If a login needs two-factor authentication, IBC cannot complete it: the 06:45 check fails, a critical alert is sent, you log in by hand, and no orders go out until the connection is restored.
18. **Backups.** Each Sunday, a consistent copy of delta1.db (SQLite's backup command) is saved to a private iCloud Drive folder, keeping the last 8. Once a month, a copy goes to an external drive.
19. **The stress check.** The last three years of daily returns for every instrument held are applied to current positions. The 1-in-100 weekly loss is the first percentile of overlapping five-day results. The buffer must cover that loss plus a doubling of current margin.
