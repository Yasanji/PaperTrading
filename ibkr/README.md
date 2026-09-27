# IBKR Paper Book (simple)

Two files. A small client and a monitor script whose limits are plain
constants at the top. It connects to an IBKR **paper** account through the
Client Portal gateway, tracks drawdown and exposure, and checks a
relative-value futures/index pair. No config framework, no invented numbers:
a limit left as `None` is skipped.

## Files

- `ibkr.py` — the client. One method per API call.
- `monitor.py` — the limits (edit these), the metric functions, and the loop.
- `peak.json` — written at runtime; stores the equity high-water mark for the
  drawdown check.

## Setup

1. Enable your paper account in the IBKR Client Portal: Settings →
   Account Configuration → Paper Trading Account → create a username and
   password. Your paper account id starts with `DU`.
2. Install Java (`java -version` to check; `brew install openjdk` if missing).
3. Download and run the gateway:
   ```bash
   curl -fL https://download2.interactivebrokers.com/portal/clientportal.gw.zip -o gw.zip
   unzip gw.zip -d clientportal.gw
   cd clientportal.gw && bin/run.sh root/conf.yaml
   ```
   Then open https://localhost:5000, accept the certificate warning, and log
   in with your paper username and password. You should see
   `Client login succeeds`.
4. Install the one dependency:
   ```bash
   pip install requests
   ```

## Run

Edit the CONFIG block at the top of `monitor.py`: set `ACCOUNT`, `BASE_CCY`,
and the limits you want to enforce. Leave any limit as `None` to skip it. For
the relative-value pair, set `RV_LONG_CONID` and `RV_SHORT_CONID` to the two
contract ids once you have chosen the instruments (find a contract id with
`ib.search("ES")`).

```bash
python monitor.py
```

Each cycle it pings the gateway, re-initialises the session if it dropped,
pulls positions, ledger and live orders, updates the equity high-water mark,
and prints any breach.

## What each check means

- `MAX_GROSS_EXPOSURE` sum of absolute market values in `BASE_CCY`.
- `MAX_NET_EXPOSURE` absolute net market value; keep it small for a
  market-neutral book.
- `MAX_CONCENTRATION` largest single position as a percent of gross.
- `MIN_CASH` cash floor from the ledger `cashbalance`.
- `MAX_OPEN_ORDERS` number of live orders.
- `MAX_DRAWDOWN_PCT` fall from the equity high-water mark, using the ledger
  `netliquidationvalue`. The mark is only as long as the run history, so keep
  the monitor running.
- Relative value: `RV_MAX_IMBALANCE_PCT` keeps the two legs close in notional;
  `RV_RATIO_MIN`/`RV_RATIO_MAX` flag when the price ratio leaves your band.

## Endpoints

The paths in `ibkr.py` are the documented Client Portal Web API paths:
`/tickle`, `/iserver/auth/status`, `/iserver/auth/ssodh/init`,
`/iserver/accounts`, `/portfolio/accounts`,
`/portfolio/{account}/positions/{page}`, `/portfolio/{account}/ledger`,
`/iserver/account/orders`, `/iserver/account/{account}/orders`,
`/iserver/reply/{id}`, `/iserver/account/{account}/order/{id}`,
`/iserver/secdef/search`, `/iserver/marketdata/snapshot`. The gateway's local
`/doc` page at https://localhost:5000 is authoritative for your build.

## Note

This trades simulated money, but order calls send live instructions to the
paper account. Check account id, side, quantity and price before sending.

## Dashboard

A small local dashboard is included. It reuses `ibkr.py` and `monitor.py`, so
it reads the same account id and limits from the CONFIG block in `monitor.py`.
The Python server talks to the gateway and hands the browser plain JSON, so the
browser never deals with the gateway's self-signed certificate.

    python dashboard.py

Then open `http://localhost:8765`. It shows connection status, equity,
drawdown, gross and net exposure, concentration, cash and open orders, the
positions table, and any rule breaches, refreshing every few seconds. Until
the gateway is running it shows a plain "gateway not reachable" banner and
recovers on its own once you log in at `https://localhost:5000`.

The page loads React from a CDN, so the browser needs internet access.

## Open source

Released under the MIT License (see `LICENSE`).

## Author

Yasanji Ratnaike. Writing on strategy and quantitative methods, including a
pairs-trading walkthrough in Python, is on Medium: https://medium.com/@yasanji

## Event-contract macro strategy

An event-contract strategy is included for ForecastEx style prediction markets
(economic indicators, Fed funds decisions). It is standalone, so it does not
need the gateway and works whatever way you connect.

Mechanics it is built on: a contract trades between 0.02 and 0.99, a winning
contract settles at 1.00, and price is the market's implied probability.
Commission is 0.00 with a 0.01 per-contract exchange fee. Election contracts
are restricted to eligible US residents, so keep the universe to economic and
rates contracts.

The edge is the gap between your probability estimate and the price. For a Yes
contract at price c, expected value per contract is `p_hat - c - fee`; for the
No side, `c - p_hat - fee`. You trade only when that clears a threshold you set,
and size with capital-conservation caps (per-event stake, total book risk,
position count, category concentration, and a capped fraction of Kelly).

`event_strategy.py` holds the logic; `event_book.py` reads a CSV and prints the
recommended book. Your probability estimates stay external, so nothing is
invented. A later machine-learning or model-based engine simply becomes the
source of `p_hat`.

```bash
python event_book.py contracts.csv
```

CSV columns: `event_id,category,yes_price,p_hat`. See `contracts.example.csv`
for the shape; its values are illustrative inputs, not real market data or
estimates.

Note on executability: ForecastEx access through the Client Portal API and the
paper environment is not guaranteed the way listed futures are. Confirm API and
paper support before wiring this to live orders.

## Systematic market-neutral relative value (stat-arb)

`statarb.py` is the core signal engine for a systematic, short-horizon,
market-neutral spread strategy. It is asset-agnostic: point it at two index
futures, a calendar spread, or any two aligned price series you choose.

Method. It estimates a hedge ratio by regression, forms the spread (long one
leg, short the hedge ratio of the other, so the position is market-neutral),
and takes a rolling z-score of that spread. It enters when the z-score is
stretched and exits when it reverts. Everything is point-in-time: at each step
the hedge ratio and the z statistics use only prices strictly before that step,
so there is no lookahead. This is the property that makes a backtest defensible.

`backtest()` runs the strategy over two price series and reports trades, hit
rate, total PnL, and maximum drawdown, all computed from the series you pass.
`latest_signal()` gives the current target for live use, and `target_legs()`
turns a target into beta-neutral notionals that map onto the pair and risk
rules in `monitor.py`.

The offline test builds a synthetic mean-reverting pair, confirms the engine
trades and profits on it, and verifies that removing future data does not change
past PnL. Run it with:

```bash
python tests/test_statarb_offline.py
```

The macro element is in which instruments you select, not in a forecast. This
is relative-value mean reversion, so it does not require a macro view to run;
the neutrality and the risk overlay are what carry it.

## Price data

`data.py` wires prices into the backtest. The default source is a CSV you
control, so a run is reproducible with no network and no extra dependency.

CSV format: a header with a date column and a close column (default `date`,
`close`). Two files are inner-joined on date, so they must share a date format.

```bash
python statarb_backtest.py y.csv x.csv
```

Two optional sources are included. `fetch_stooq(symbol)` downloads daily closes
with no API key (for example `spy.us`, `qqq.us`); save the result with
`save_csv` for a reproducible run. `ibkr.history(conid, period, bar)` pulls bars
from the gateway (`GET /iserver/marketdata/history`); `closes_from_history`
turns the response into a (date, close) series. Note that some contracts scale
prices by a priceFactor, so check that before relying on absolute levels.
