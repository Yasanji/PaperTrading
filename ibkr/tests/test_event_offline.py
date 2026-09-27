"""Offline test of the event-contract strategy logic.

The prices and probabilities here are a hand-built fixture to check the maths,
not real market data or real estimates. They are labelled as mock and are
never presented as anything else.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from event_strategy import Contract, decide, kelly_fraction, build_book


def approx(a, b, tol=1e-9):
    return abs(a - b) < tol


def run():
    # Yes edge: p_hat 0.55 vs price 0.40, fee 0.01 -> ev_yes = 0.14
    d = decide(Contract("cpi_hot", "economic_indicator", 0.40, 0.55), min_edge_ev=0.02)
    assert d.side == "YES", d
    assert approx(d.ev_per_contract, 0.14), d.ev_per_contract
    assert approx(d.kelly_full, (0.55 - 0.40) / (1 - 0.40)), d.kelly_full

    # No edge: p_hat 0.50 vs price 0.70 -> ev_no = 0.19, entry 0.30
    d = decide(Contract("hike", "fed_funds", 0.70, 0.50), min_edge_ev=0.02)
    assert d.side == "NO" and approx(d.entry_price, 0.30) and approx(d.ev_per_contract, 0.19), d

    # No trade: edge below threshold
    d = decide(Contract("flat", "economic_indicator", 0.50, 0.51), min_edge_ev=0.02)
    assert d.side is None, d

    # kelly formula sanity
    assert approx(kelly_fraction(0.55, 0.40), 0.25)

    # book with caps: bankroll 10000, cap stake 500/event, quarter Kelly
    contracts = [
        Contract("cpi_hot", "economic_indicator", 0.40, 0.55),   # ev 0.14
        Contract("hike", "fed_funds", 0.70, 0.50),               # ev 0.19 (No)
        Contract("gdp_beat", "economic_indicator", 0.30, 0.45),  # ev 0.14
        Contract("flat", "economic_indicator", 0.50, 0.51),      # no trade
    ]
    book = build_book(
        contracts, bankroll=10000,
        min_edge_ev=0.02,
        max_stake_per_event=500,
        kelly_cap=0.25,
        max_positions=10,
        max_book_risk=100000,
        max_category_pct=100,
    )
    ids = [p.event_id for p in book["positions"]]
    assert "flat" not in ids, ids
    assert set(ids) == {"cpi_hot", "hike", "gdp_beat"}, ids
    # each stake capped at 500
    for p in book["positions"]:
        assert p.stake <= 500 + 1e-9, (p.event_id, p.stake)
    print("positions:", [(p.event_id, p.side, p.contracts, round(p.stake,2)) for p in book["positions"]])
    print("book_risk:", round(book["book_risk"], 2))

    # tighten max_book_risk so only the top-EV position fits
    tight = build_book(contracts, bankroll=10000, min_edge_ev=0.02,
                       max_stake_per_event=500, kelly_cap=0.25,
                       max_book_risk=500)
    assert len(tight["positions"]) == 1 and tight["positions"][0].event_id == "hike", tight["positions"]
    print("tight book keeps only:", tight["positions"][0].event_id)

    # category concentration cap: cap economic_indicator at 40% of a 1000 book
    cat = build_book(contracts, bankroll=10000, min_edge_ev=0.02,
                     max_stake_per_event=500, kelly_cap=0.25,
                     max_book_risk=1000, max_category_pct=40)
    econ = sum(p.stake for p in cat["positions"] if p.category == "economic_indicator")
    assert econ <= 400 + 1e-9, econ
    print("category-capped econ stake:", round(econ, 2))

    print("\nAll event-strategy assertions passed.")


if __name__ == "__main__":
    run()
