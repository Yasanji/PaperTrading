# delta1: dividend, index and market data

A private, point-in-time store for the Delta One work: EURO STOXX 50 dividends, implied dividends, index reviews and, later, the paper book.

## How it works

- **delta1.db** is a SQLite file on this machine. It is listed in .gitignore and never committed. Back it up.
- Rows are only ever added, never updated. Every row records when it was collected, so the database shows what was known on any date.
- **collect.py** runs one job per command and logs each run in the runs table. Errors go to the events table.

## Commands

    pip install yfinance pandas requests openpyxl lxml
    python collect.py init          # create the tables (safe to rerun)
    python collect.py all           # run every job
    python collect.py sx5e          # EURO STOXX 50 members and free-float weights (10% cap)
    python collect.py divs          # dividend history and forward dividends for those members
    python collect.py msci_europe   # MSCI Europe members and weights (Xtrackers fund holdings)
    python collect.py estr          # euro short-term rate (ECB)
    python collect.py levels        # EURO STOXX 50 index level

## Rules the forecasts follow

STOXX DVP Calculation Guide (September 2026) and STOXX Calculation Guide (Section 8.1):

- The dividend points count ordinary gross cash dividends on their ex-date, plus withholding tax on special dividends and capital returns.
- The period runs from the day after the third Friday of December to the third Friday of the following December.
- A company's contribution in points is its dividend divided by its price, times its index weight, times the index level, all from the day before the ex-date.
- Stock dividends in new shares do not count. Stock dividends from treasury shares count as cash dividends.
- Scrip dividends are treated as cash until STOXX's treatment is confirmed.

## Known limits

- Weights are approximate: Yahoo's free-float counts differ from STOXX's free-float factors.
- Yahoo data is not redistributed; only the code that collects it is committed.
- Dividend futures (FEXD) and index futures (FESX) prices are not yet collected: next sources are Interactive Brokers and Eurex settlements.
