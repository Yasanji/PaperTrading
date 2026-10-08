# Pod 3: index events

Trades predicted MSCI Europe and STOXX Europe 600 changes, under `../POD3_PREREGISTRATION.md` and amendments 1 and 2. Predictions come from `../pod3_msci` and `../pod3_stoxx`.

| File | What it does |
| --- | --- |
| `reviews.csv` | Each review: announcement and effective dates, the committed prediction file, the official list once published |
| `pod.py` | Pod interface: `targets(as_of)`, `status()`, `checks()`; entry 15 trading days before the effective date, exit on it, beta hedge in whole STOXX 600 futures |
| `orders.py` | Turns targets into whole shares and an order file (MOC for shares); writes `book/targets/` and `book/orders/`. Sends nothing |
| `score.py` | Scores a prediction against the official list |
| `backtest_trades.py` | Trade back-check on the May and August 2026 MSCI and September 2026 STOXX reviews |
| `dryrun/` | Example targets and orders for 27 November 2026, from the preliminary STOXX list |

Dry run with preliminary lists: `POD3_PRELIMINARY=1 python orders.py 2026-11-27`.

## Trade back-check (in-sample)

40 trades over three reviews, hedged and after costs: mean +1.42% a trade, median +1.85%, 62% positive. MSCI May and August: about zero. STOXX September: +2.4% a trade, helped by Greece's move to developed-market status. Correct calls averaged +1.82%, wrong calls +0.06%. Three reviews, with thresholds set on the same reviews, so this is not a test of the strategy.

## Size

At the forward-test scale each position is about $4,200 (10% of $166,667 allocated capital, at 25%). A STOXX 600 future is about $36,000, so the hedge rounds to zero contracts unless the net beta exposure passes about $18,000.

## Official lists

After each announcement save the official changes as `actual_<review>.csv` with columns `change` (ADD or DELETE) and `name`, then run `python score.py <prediction> <actual>`. From the next close, `pod.py` closes any predicted change not on the list.
