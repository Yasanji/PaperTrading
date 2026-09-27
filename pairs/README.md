# pairs

The reproducible code from Part 1 of the relative value series.

`pairs_trading.py` does the whole pipeline in one script:

- pulls five years of daily prices for the current EURO STOXX 50 constituents with yfinance
- screens every pair on correlation, then tests the survivors for cointegration on the raw prices
- shows that the most correlated pair in the index, the two Spanish banks, fails cointegration
- keeps Safran and Siemens, and checks the half-life and the Hurst exponent
- backtests the pair point-in-time and net of costs, then measures the residual market beta against the index

Run it:

```
pip install -r requirements.txt
python pairs_trading.py
```

The printed numbers match the article. The data is fetched at runtime, so the repo stores nothing proprietary, and the exact figures depend on the data available on the day you run it.
