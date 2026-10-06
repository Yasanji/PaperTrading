# Pod 3: index events (prediction)

Pre-registration, drafted 6 October 2026, before any prediction is made. Yasanji Ratnaike. Every rule is fixed before the first trade. Any change is a dated amendment, committed before the result it affects is seen.

## 1. The question

Can index additions and deletions be predicted from the index providers' published rules before they are announced, and does trading the predictions earn a return? Index funds must buy added stocks and sell deleted ones on the effective date, so prices tend to move in the weeks before. Predicting changes from the rules is core Delta One work.

**Status.** The pod launches as a forward test at 25% of its target risk, under the portfolio pre-registration. A backtest runs in parallel once past announcements are collected.

## 2. Reviews covered

| Index | Reviews | Effective date | Prediction data |
| --- | --- | --- | --- |
| MSCI Europe (World and Emerging Markets need paid data and are left out for now) | February, May, August, November | After the close on the last business day of the month | MSCI's published methodology and size cut-offs |
| STOXX Europe 600 | March, June, September, December | After the close on the third Friday of the month | STOXX's monthly selection lists, which rank stocks by free-float size |

## 3. Predictions

1. **Method.** Each prediction applies the index provider's published rules, as they stand on the prediction date, to the latest available data. For MSCI, the rules come from the MSCI Global Investable Market Indexes Methodology (August 2023 version, the latest found): an existing constituent stays in its size segment while its full market value is between two-thirds of and 1.5 times the size cut-off, or one-half and 1.8 times at a light rebalancing. Prices are taken from the last 10 business days of the month before the review month (October for November). MSCI's cut-offs are not published in full, so each cut-off is inferred from the smallest current constituents of MSCI Europe, and the inference is recorded with each prediction.
2. **Output.** For each review, a list of predicted additions and deletions, each with the rule that triggers it.
3. **Commitment.** The list is committed to GitHub at least 20 trading days before the effective date, and before the official announcement.
4. **Scoring.** After each announcement, the list is scored: the share of predictions that were right, and the share of actual changes that were predicted.

## 4. The trade

1. **Entry.** At the close 15 trading days before the effective date, buy each predicted addition and short each predicted deletion.
2. **Exit.** At the close on the effective date, when index funds trade.
3. **Wrong predictions.** If the official announcement does not include a predicted change, that position is closed at the next close. This is the only exception to the minimum holding period apart from risk limits and errors.
4. **Hedge.** Each position is hedged with the index future of its region, using the stock's beta over the previous 252 trading days.
5. **Size.** Each position is 10% of the pod's allocated capital, at most 20 positions at once. If more changes are predicted, those whose rule margin is largest are taken first, with ties broken by ticker in alphabetical order.
6. **Costs.** As in Sleeve B: 3 basis points a trade in Europe, 2 in the US, 5 in Asia, and 1 on hedges. Borrowing on shorts at 0.45% a year, 1% in Asia.

## 5. Tests and pass marks

Once past announcements are collected, the backtest runs on development and hold-out periods fixed in a dated amendment before the data is collected. The pod passes only if its hold-out Sharpe ratio is at least 0.30, its t-statistic is at least 1.0, and its return is positive in both halves of the hold-out. Until then, it stays at 25% risk. Prediction accuracy is reported for every review, whatever it shows.

## 6. Reporting

Every prediction list, score and result is committed before the next review. No rule, threshold or universe changes after a result is seen.
