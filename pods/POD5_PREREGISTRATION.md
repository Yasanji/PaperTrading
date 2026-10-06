# Pod 5: special situations

Pre-registration, drafted 6 October 2026, before any trade. Yasanji Ratnaike. Every rule is fixed before the first trade. Any change is a dated amendment, committed before the result it affects is seen.

## 1. The question

Do UK real estate investment trusts (REITs) trading at the widest discounts to their net asset value (NAV) outperform those at the narrowest? A wide discount can close through a recovery, a bid, a merger or buybacks.

**Status.** The pod launches as a forward test at 25% of its target risk, under the portfolio pre-registration. Rights issues and stocks in transition are logged at launch, not traded: each will get its own rules in a dated amendment before it trades.

## 2. Universe and data

1. **Stocks.** UK-listed REITs in the FTSE 350 on 6 October 2026, frozen as a list committed with this pre-registration. Changes to the list are dated amendments, applied from the next rebalance.
2. **NAV.** The latest reported EPRA net tangible assets (NTA) per share, read from each company's half-year and annual results, with the publication date recorded. A NAV is used only from the day after it is published.
3. **Prices.** Yahoo Finance daily closes.

## 3. The signal

1. **Discount.** Price divided by the latest published NAV per share, minus 1.
2. **Eligibility.** A REIT is eligible if its NAV is no more than 7 months old and its median daily traded value over 63 trading days is above £1 million.
3. **Ranking.** At each month-end, eligible REITs are ranked by discount, widest first, with ties broken by ticker in alphabetical order.

## 4. The trade

1. **Positions.** Buy the widest-discount third and short the narrowest-discount third, equal-weighted, with each side summing to the pod's allocated capital.
2. **Timing.** Rebalance at the close of the first trading day after each month-end. Positions are held at least 15 trading days and adjusted only when a target changes by more than 25%.
3. **Hedge.** The long–short structure is close to neutral to the property market, and no separate hedge is used.
4. **Bids.** If a held REIT receives a firm takeover offer, its position is kept until the offer completes or lapses.
5. **Costs.** 5 basis points a trade, plus UK stamp duty of 0.5% on purchases. Shorts are charged 1% a year to borrow.

## 5. Logged, not traded

For each rights issue by a STOXX Europe 600 company, and each UK company moving its main listing or leaving an index, the pod records the announcement date, the terms, and the share price from announcement to completion. These records are the basis for their future rules.

## 6. Tests and pass marks

Once a NAV history is collected, the backtest runs on development and hold-out periods fixed in a dated amendment before the data is collected. The pod passes only if its hold-out Sharpe ratio is at least 0.30, its t-statistic is at least 1.0, and its return is positive in both halves of the hold-out. Until then, it stays at 25% risk.

## 7. Reporting

Every result is committed before the next test. No rule, threshold or universe changes after a result is seen.
