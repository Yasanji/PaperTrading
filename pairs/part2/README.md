# Part 2: testing the book

Code for *Pairs Trading in Python, Part 2*. Every rule was fixed before the frozen run.

| File | What it does |
| --- | --- |
| `part2_moving_anchor.py` | Part 2 module: screen, walk-forward, cash leg, portable alpha, decision report |
| `get_data.py` | Downloads the EURO STOXX 50 names, ^GSPC and ^STOXX50E (27 Sep 2021 to 25 Sep 2026) |
| `get600.py` | Downloads the STOXX 600 constituents with Yahoo industry and currency |
| `model_sx5e.py` | Frozen design on the EURO STOXX 50: sector-linked pairs, 90-day rolling anchor, stop latch, evidence floor, ERC sizing on in-trade risk, 3.5% vol target, 70/30 idle risk, -3.5% backstop |
| `model_stoxx600.py` | The same rules on the STOXX 600 (same industry and currency pairs) |
| `run_part2.py` | Runs both, with the best pair removed as a robustness check |
| `results/` | Outputs quoted in the article |

Fixes to the module as written, applied in the models: formation legs aligned on exchange holidays before the fit, and a stop latch so a stopped pair cannot re-enter until |z| is back inside the exit band.

Limitations: current constituents (survivorship bias), 353 of 600 STOXX 600 names matched on Yahoo, same-currency pairs only, daily returns clipped at ±50% as a data-error guard.

## Correction (29 Sep 2026)

The equal-risk sizing in the first version used a fixed-point iteration that could return negative weights when two selected pairs were negatively correlated, which flipped the trade on those pairs (10 of 34 picks on the EURO STOXX 50, 53 of 126 in the 10-pair STOXX 600 run). `erc()` in both models now uses a long-only multiplicative update that keeps every weight positive and equalises risk contributions. No other rule changed. Corrected results are in `results/summary.csv`; run `run_part2.py` to regenerate the pair logs.
