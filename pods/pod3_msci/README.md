# Pod 3: MSCI Europe review predictions

Predicts additions to and deletions from the MSCI Europe (Standard) index at each quarterly review, under the rules in `../POD3_PREREGISTRATION.md` and `../POD3_AMENDMENT_1.md`.

| File | What it does |
| --- | --- |
| `fetch.py` | Downloads MSCI Europe and MSCI Europe Small Cap holdings (Xtrackers) and market values from Yahoo by ISIN |
| `fill.py`, `fill_symbols.py` | Retries names Yahoo rate-limits or cannot find by ISIN |
| `prices.py` | Daily closes, currency rates and URTH since a start date |
| `model.py` | Market assignment, company grouping, cut-offs and the MSCI rules |
| `backtest.py` | Rebuilds membership before the May and August 2026 reviews and ranks the actual changes |
| `predict_nov.py` | November 2026 prediction, with the decision rule fixed in Amendment 1 |
| `score.py` | Scores a committed prediction against MSCI's published list |

Run order:

```
python fetch.py data
python fill.py data/universe_YYYY-MM-DD.csv
python fill_symbols.py data/universe_YYYY-MM-DD.csv
python prices.py data/universe_YYYY-MM-DD.csv data/prices.pkl 2026-04-01
python predict_nov.py data/universe_YYYY-MM-DD.csv data/prices.pkl data 2026-10-19 2026-10-30
```
