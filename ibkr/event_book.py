"""Build a recommended event-contract book from a CSV of contracts.

Edit the CONFIG block, put your contracts and probability estimates in a CSV,
then run:

    python event_book.py contracts.csv

CSV columns (header row required):
    event_id,category,yes_price,p_hat

    event_id   your label for the contract
    category   e.g. economic_indicator, fed_funds
    yes_price  current market price of the Yes side, 0.02..0.99
    p_hat      YOUR probability estimate for the Yes outcome, 0..1

Nothing is invented: yes_price is the market's, p_hat is yours. Every limit
below is yours to set; a limit left as None is not applied.
"""

import csv
import sys

from event_strategy import Contract, build_book

# --- CONFIG ---------------------------------------------------------------
BANKROLL = None              # capital the book sizes against, e.g. 100000
MIN_EDGE_EV = None           # minimum expected value per contract to trade, e.g. 0.03
MAX_STAKE_PER_EVENT = None   # cap on capital at risk per event, e.g. 2000
KELLY_CAP = None             # fraction of full Kelly to use, e.g. 0.25 (quarter Kelly)
MAX_POSITIONS = None         # cap on number of open positions, e.g. 10
MAX_BOOK_RISK = None         # cap on total capital at risk, e.g. 15000
MAX_CATEGORY_PCT = None      # cap on one category as percent of book risk, e.g. 40
FEE = 0.01                   # per-contract exchange fee
# --------------------------------------------------------------------------


def load_contracts(path):
    out = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            out.append(Contract(
                event_id=row["event_id"].strip(),
                category=row["category"].strip(),
                yes_price=float(row["yes_price"]),
                p_hat=float(row["p_hat"]),
            ))
    return out


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python event_book.py contracts.csv")
    if BANKROLL is None or MIN_EDGE_EV is None:
        raise SystemExit("Set BANKROLL and MIN_EDGE_EV in the CONFIG block first.")

    contracts = load_contracts(sys.argv[1])
    book = build_book(
        contracts, bankroll=BANKROLL,
        min_edge_ev=MIN_EDGE_EV,
        max_stake_per_event=MAX_STAKE_PER_EVENT,
        kelly_cap=KELLY_CAP,
        max_positions=MAX_POSITIONS,
        max_book_risk=MAX_BOOK_RISK,
        max_category_pct=MAX_CATEGORY_PCT,
        fee=FEE,
    )

    print(f"{len(book['positions'])} positions, capital at risk {book['book_risk']:.2f}, "
          f"expected value {book['expected_value']:.2f}\n")
    print(f"{'event':16} {'cat':20} {'side':4} {'price':>6} {'contracts':>10} {'stake':>10} {'ev/ct':>7}")
    for p in book["positions"]:
        print(f"{p.event_id:16} {p.category:20} {p.side:4} {p.entry_price:6.2f} "
              f"{p.contracts:10d} {p.stake:10.2f} {p.ev_per_contract:7.3f}")
    if book["rejected"]:
        print("\nrejected:")
        for r in book["rejected"]:
            print(f"  {r['event_id']}: {r['reason']}")


if __name__ == "__main__":
    main()
