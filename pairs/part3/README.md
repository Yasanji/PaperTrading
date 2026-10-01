# Part 3: adding to the book

Three tests on the same period as Part 2 (Sep 2023 to Sep 2026), each with rules fixed before the run.

| File | What it does |
| --- | --- |
| `model_residual.py`, `run_residual.py` | Residual mean reversion (Avellaneda and Lee thresholds) on the STOXX 600 |
| `get250.py`, `model_small.py`, `run_part3.py` | Test 1: 70% large-cap pairs, 30% FTSE 250 pairs; idle risk 65% equity, 20% euro govt bonds, 15% cash |
| `get_ez.py`, `model_ezsmall.py`, `run_part3b.py` | Test 2: 65% large-cap pairs, 15% Eurozone small-cap pairs, 20% managed-futures ETFs (DBMF, KMLM, WTMF); idle risk in cash |
| `model_600.py` | The Part 2 STOXX 600 pairs model used as the large-cap sleeve (same as `../part2/model_stoxx600.py`, with carry and liquidity settings as named constants) |

Run order: Part 2's `get_data.py` and `get600.py` (copy `data.pkl` and `data600.pkl` here, plus `part2_moving_anchor.py`), then `get250.py` / `get_ez.py`, then the `run_*.py` scripts.

Small-cap sleeves: 10bp per trade, 1.5% a year borrow on shorts, median daily traded value of at least 1 million (GBP or EUR), listed funds excluded, and no names shared with the large-cap universe. The managed-futures sleeve sizes the three ETFs for equal risk on trailing-year covariance (history from 2021), rebalances monthly with a one-day lag, and hedges to EUR.
