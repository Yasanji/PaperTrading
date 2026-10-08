# Sleeve C: month-end rebalancing (US)

Pre-registration, drafted 8 October 2026, before the sleeve trades and before any forward data. Yasanji Ratnaike. Every rule is fixed before the first trade. Any change is a dated amendment, committed before the result it affects is seen.

## 1. The question

Does the month-end rebalancing signal of Harvey, Mazzoleni and Melone (working paper, 14 January 2026) predict US equity returns against Treasuries after costs, when traded forward from a record fixed in advance? Investors with fixed equity and bond weights sell equities at month-end after equities have outperformed, and buy them after equities have underperformed. The sleeve takes the other side of that pressure.

**What is already known.** Paper 2 (pairs/paper2) found, on index, futures and ETF data, a Calendar-in-the-last-week coefficient of -0.20 to -0.26 (t -2.4 to -2.9) over 1997 or later to March 2023, and no significant change in it after March 2023 (t 0.2 to 0.5), with too few days since then to tell whether the effect remains. The forward record is the test.

**Relation to the book.** A third sleeve of Pod 1 (systematic macro). It trades the same contracts as the trend sleeve but in the opposite direction to recent performance, so it is expected to offset trend in part.

## 2. Signal

The Calendar signal of Paper 2 Step 1, on the return basis of Paper 2 amendment 4.4: a simulated portfolio of 60% S&P 500 and 40% 10-year Treasury, rebalanced to 60/40 at each month-end close, whose equity weight drifts with the S&P 500 price index and the price change of a constant-maturity 10-year Treasury at the Treasury's daily par yield. The signal on a day is the equity weight minus 60% at that day's close.

Inputs are Yahoo Finance index closes and US Treasury daily par yields, taken after the US close and committed with the targets, as for the rest of the book.

## 3. Trade

1. **When.** Only in the last week of the month: from the close of the fifth-last trading day of the month to the close of the first trading day of the next month. This mirrors the regression, in which the signal on each of the last five days predicts the next day's return.
2. **Direction.** Signal above zero (equities overweight): short equity, long bonds. Signal below zero: long equity, short bonds. The direction is set from the signal at each close in the window and changes only if the signal changes sign.
3. **Instruments.** One Micro E-mini S&P 500 future (MES) against one 10-year Treasury note future (ZN), front contracts on the book's roll rules. At the 6 October 2026 contract check the two have similar annual dollar volatility (about 4,700 dollars each), so one of each is roughly risk-balanced.
4. **Size.** One contract on each leg. The sleeve does not scale with the signal's size.
5. **Execution.** Market orders 10 minutes before settlement, as for Pod 1, through the evening and morning chain with the same approval, checksum and kill-switch rules.

## 4. Book rules this sleeve needs (amendments to the portfolio pre-registration, committed with this file)

1. **Holding period.** The book's 15-trading-day minimum holding does not apply to this sleeve, whose positions last about six trading days. All other limits apply.
2. **Risk share.** Pod 1's risk is split 60% trend, 20% currency carry and 20% this sleeve (from 75% and 25%). Before the first trade, the contract check is re-run at the new shares and any trend market that falls below half a contract is reported.
3. **Size in paper.** At 25% of its share the sleeve would round to zero contracts, so it trades at its full share in the paper account, as Pod 1 does under book amendment 1.
4. **Netting.** Sleeve targets are added to the trend sleeve's targets in the same contracts before orders are generated. P&L is attributed to each sleeve as its target position times the price change.

## 5. Costs

One tick on each leg each time a position is opened, changed or closed, plus Interactive Brokers commissions as charged. Recorded per trade.

## 6. Record

For each month: the signal on each day of the window, positions, fills, costs and P&L in dollars. The Threshold signal of Paper 2 is computed and logged every day but not traded, so its forward record exists for later comparison.

## 7. Evaluation

The forward test runs for at least 24 months, which is 24 trades and too few to show significance on its own. It is evaluated with the research evidence.

1. **Close the sleeve** if any of the following holds:
   - Its cumulative net loss exceeds 2.5 times its target annual volatility (about 12,000 dollars at 4,900 dollars a year).
   - After 24 months, the Calendar-in-last-week coefficient estimated over the forward period is positive with a t-statistic above 2.
   - Paper 2's pre-registered pooled test (amendment 4.6) finds a significant positive change after March 2023.
2. **Continue** otherwise, reported monthly with the cumulative coefficient, P&L and costs.
3. **No promotion** to live capital is decided before 24 months and a further amendment.
