# Paper book: portfolio pre-registration

Drafted 6 October 2026, before the book trades. Yasanji Ratnaike. Every rule is fixed before the book goes live. Any change is a dated amendment, committed before it applies.

## 1. Purpose and capital

1. **Purpose.** Run a multi-strategy book the way a multi-strategy fund does: independent pods, a centre that manages risk and capital, and a record anyone can check.
2. **Capital.** $1,000,000 in the Interactive Brokers paper account. All limits below are measured against the book's net asset value (NAV) at the previous close.

## 2. Pods

| Pod | Strategy | Status at launch |
| --- | --- | --- |
| 1. Systematic macro | Trend (15 futures) and currency carry (Sleeve A) | Tested; full incubation rules |
| 2. Equity market-neutral | Equity carry (Sleeve B) | Forward test at 25% of target risk |
| 3. Index events | MSCI and STOXX reviews | Forward test at 25% of target risk |
| 4. Dividends | Pre-dividend trade | Forward test at 25% of target risk |
| 5. Special situations | Rights issues, REIT discounts, stocks in transition | Forward test at 25% of target risk |
| 6. Volatility | VIX futures term-structure carry, with a tail hedge | Forward test at 25% of target risk |

All six pods launch together. Each must have written, pre-registered rules committed to GitHub before it trades. Pods 2–6 trade as forward tests: their live record is their test, and their backtests run in parallel where data allows. A pod in a forward test moves to its full risk share only after passing its own pre-registered tests, and is closed if it fails them. Within Pod 1, trend receives 75% of the pod's risk and currency carry 25%, given carry's flat hold-out. The monthly report labels every pod's status.

## 3. Risk and sizing

1. **Volatility target.** The book is scaled to 6% annual volatility, measured on the previous 126 trading days, reset weekly.
2. **Risk shares.** Each pod has an equal target share of the book's risk. Pods in a forward test trade at 25% of that share, so the book runs below its 6% target until they pass their tests. This is the conservative choice and is reported each month.
3. **Gross exposure.** Total gross notional is capped at 4 times NAV. Equity pods are capped at 2 times their allocated capital.
4. **Order limit.** No single order may exceed 10% of NAV in notional value.

5) **Allocated capital.** Each pod's allocated capital is NAV times its risk share. Drawdown limits and gross caps are measured against it.
6) **Minimum holding.** Every position is held for at least 15 trading days, unless a risk limit or an error forces it closed.
7) **No-trade band.** A position is adjusted only when its target changes by more than 25% of its current size.
8) **Contract sizes.** Before launch, each futures market's smallest contract is checked against its target risk, using Interactive Brokers' contract details. A market is traded if its target is at least half a contract, rounded to whole contracts; below half a contract it is left out and reported. Each sleeve's total risk must then be within 25% of its target.

## 4. Capital charges and liquidity

1. **Capital charge.** Each pod is charged the larger of its margin requirement and its stress loss, defined as its worst five-day loss in its development period scaled to its current size. Until a pod's backtest exists, its stress loss is 10% of its gross exposure.
2. **Cash buffer.** At least 50% of NAV is held in cash and never used as margin.
3. **Margin cap.** Total margin may not exceed 40% of NAV.
4. **Stress check.** Each week the buffer must cover the book's 1-in-100 weekly loss and a doubling of margin at the same time. If it does not, every pod is reduced in proportion until it does.

## 5. Drawdown limits

1. **Pod.** A pod that falls 4% from its peak, measured against its allocated capital, halves its risk. At 6% it closes all positions and stops for review.
2. **Book.** If the book falls 8% from its peak, every pod halves its risk.
3. **Re-entry.** A stopped pod restarts at half risk one month after stopping, only if the review finds no implementation error, and returns to full risk once its drawdown recovers to 2%.
4. **Errors.** A position that should not exist is closed at the next close, and no new orders are sent until the cause is found and recorded.

## 6. The centre

1. **Factor exposure.** Each day, the centre measures the book's exposure to equity markets, size, value and momentum by region, and to rates, commodities and currencies. If the book's beta to world equities moves outside ±0.1, it is hedged back with index futures at the next close.
2. **Crowding between pods.** If the 126-day correlation between two pods' returns exceeds 0.5, both are cut to 75% of their risk until it falls below 0.4.
3. **Capital allocation.** Risk shares stay fixed for the first 12 months. After that, at each quarter-end, a pod with a trailing 12-month Sharpe ratio below 0 has its risk share multiplied by 0.75, and one above 1.0 by 1.25. Shares are then rescaled to sum to 100%, with no pod below 10% or above 40% of the book's risk.
4. **Incubation.** A pod whose strategy has passed its tests trades at 25% of its target risk for six months, then receives its full share if its trades reconcile with the broker's records with no unexplained difference in the last two months. A pod in a forward test stays at 25% until it passes its own tests, however long that takes.

## 7. Execution

1. **Timing.** Signals use each market's close. Orders are market-on-close orders at the next close.
2. **Instruments.** Futures pods use micro contracts where available, so that positions can be sized accurately. Equity pods trade shares and hedge with index futures.
3. **Rolls.** Futures are rolled to the next contract five business days before expiry.
4. **Kill switch.** If data is missing, positions do not match the record, or a limit is breached, no orders are sent until the cause is found.

## 8. Stress tests

Each month the report shows the book's estimated loss, at current positions, in six episodes: the 2008 financial crisis, the 2011 euro crisis, the 2015 Swiss franc shock, the 2020 Covid crash, the 2022 rate shock and the April 2025 tariff shock. It states whether any two pods would lose in the same episode. The tests are descriptive and do not change positions.

## 9. Validation and records

1. **Targets.** Before each trading day, target positions are committed to GitHub, which timestamps the decision.
2. **Broker records.** Trades, positions and NAV are exported daily from Interactive Brokers (Flex Query) and committed.
3. **Reconciliation.** Targets and fills are compared each day, and every difference is reported.
4. **Database.** All data, signals, targets, orders, fills, positions, risk and events are stored in a private SQLite database, linked to the GitHub commits.
5. **Report.** A monthly report shows returns, drawdowns and risk by pod, capital use, factor exposure, stress results and every deviation, including losses.

## 10. Amendments to tested strategies

Made on 6 October 2026, after the results of trend (Ratnaike, 2026) and Sleeve A were seen. They change implementation, not signals, and each is backtested again and reported as a post-result version alongside the original.

1. **Trend.** A position changes direction only when the 12-month return, divided by its 12-month volatility, moves beyond ±0.25. Inside that band the existing position is kept. The minimum holding period and no-trade band apply.
2. **Currency carry.** Traded through CME currency futures, which price in the interest-rate gap. The Swedish krona and Norwegian krone are left out live, given thin futures markets, and this is reported.
3. **Currency carry timing.** The OECD's release dates for three-month rates are checked. If a month's rate was published after the month-end on which the backtest used it, the sleeve is re-run with central banks' daily rates, as a dated amendment.
4. **Contract sizing (6 October 2026, before any trade).** The contract check (book/contract\_check\_2026-10-06.csv) found that three trend markets need less than half a contract at their target risk: Nasdaq-100 (0.25), the 30-year Treasury (0.39) and gold (0.35). They are left out. Each asset class stays covered: equities by the S&P 500, bonds by the 2-year and 10-year Treasuries, and metals by silver and copper. The S&P 500 (0.70), the 10-year Treasury (0.71) and the New Zealand dollar (0.55) are traded at one contract. The 12-market trend sleeve carries about 84% of the 15-market target risk, within 25%. A post-result backtest of the 12-market version is reported alongside the original.
