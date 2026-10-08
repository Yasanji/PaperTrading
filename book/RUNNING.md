# Running the book

Build step 2: the daily trading job, with Pod 1 (trend and currency carry) and Pod 3 (index events) as its first pods. It follows `DESIGN.md` and the portfolio pre-registration. Nothing is sent to Interactive Brokers until the 10-trading-day dry run has passed and the API is taken out of read-only mode.

## Files

| File | Step |
| --- | --- |
| `config.py` | Every limit and setting, from the portfolio pre-registration |
| `futures_ib.py` | Evening: two years of daily futures closes for each contract-check market, from IB (read-only) into delta1.db |
| `data.py` | Prices for the pods: delta1.db, or Yahoo continuous futures for dry runs away from the Mac |
| `../pods/pod1/pod.py` | Pod 1 targets in whole contracts: trend (12-month return over volatility, ±0.25 band) and carry (OECD rates, SONIA for sterling) |
| `../pods/pod3/pod.py` | Pod 3 targets around each index review |
| `book.py` | Combines the pods, applies the 25% no-trade band and the 15-day minimum hold, writes `targets/<date>.csv`, `targets/<date>.json` and `orders/<date>.csv` |
| `approve.py` | Shows the batch; approve all, none, or all except named symbols |
| `execute.py` | 07:00: checks kill switch, pushed targets, approval checksum, duplicate batch, paper account, price and size limits; resolves and rolls futures; places MOC orders for shares and timed market orders for futures. Dry run unless `--send` |
| `reconcile.py` | After the US close: positions and NAV from IB against targets; trips the kill switch on any difference |
| `kill.py`, `clear_kill.py` | Kill switch status and trip; clearing needs a written reason and a clean reconciliation |
| `evening.sh`, `morning.sh` | The evening chain (prices, book, commit and push targets, notification) and the 07:00 send |

## Dry run (10 trading days, DESIGN.md s.12.10)

```
cd ~/Documents/PaperTrading && source delta1/.venv/bin/activate
pip install ib_async
python book/futures_ib.py
python book/book.py $(date +%F) --source db
python book/approve.py $(date +%F) all
python book/execute.py $(date +%F)        # connects read-only, builds and checks every order, sends nothing
python book/reconcile.py $(date +%F)
```

Tested in the cloud on 8 October 2026 without IB: the book, approval, offline execution, reconciliation, the kill switch (trip, refusal to clear while reconciliation fails, clear), the tampered-orders check and the next-day band and holding rules. Not yet tested against IB Gateway: `futures_ib.py`, the IB parts of `execute.py` and `reconcile.py`.

## Size during incubation

At 25% of target risk (portfolio pre-registration s.6.4), Pod 1 rounds most markets to zero contracts: on 8 October 2026 only five currency futures had a position, and no equity, bond, energy or metal market did. Pod 3's positions are about $4,200 each. Changing either needs a dated amendment.
