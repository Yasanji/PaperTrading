# PaperTrading

Code for a systematic, market-neutral relative value paper book, and the research behind it.

There are two parts.

## pairs

The research behind the Medium series on relative value. `pairs/pairs_trading.py` is the full, reproducible script from Part 1. It pulls five years of daily prices for the current EURO STOXX 50 constituents with yfinance, screens every pair on correlation, tests the survivors for cointegration on the raw prices, checks the half-life and the Hurst exponent, and backtests the chosen pair (Safran and Siemens) point-in-time and net of costs. It also measures the residual market beta against the index.

Run it:

```
pip install -r pairs/requirements.txt
python pairs/pairs_trading.py
```

The data is fetched at runtime, so nothing proprietary is stored in the repo. Results depend on the data available from the source on the day you run it.

## ibkr

A small paper trading book that connects to an Interactive Brokers paper account through the Client Portal gateway. It tracks drawdown and exposure, checks a relative value pair, and has a local dashboard. See `ibkr/README.md` for setup. This trades simulated money, and order calls still send live instructions to the paper account, so check account id, side, quantity and price before sending.

## Write-up

The Part 1 article is on Medium: https://medium.com/@yasanji

## Licence

MIT. See `LICENSE`.
