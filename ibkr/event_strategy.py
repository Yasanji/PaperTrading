"""Event-contract macro strategy logic for ForecastEx style contracts.

Contract mechanics this is built on (verified against IBKR / ForecastEx docs):
a contract trades between 0.02 and 0.99, a winning contract settles at 1.00,
and the price is the market's implied probability. Commission is 0.00 with a
0.01 per-contract exchange fee.

The edge is the gap between your own probability estimate and the price.
For a Yes contract bought at price c:
    expected value per contract = p_hat - c - fee
For the No side (bought at 1 - c):
    expected value per contract = c - p_hat - fee
You trade only when the expected value clears a threshold you set.

Your probability estimates come from outside this module (a file, a model, or
a later machine-learning engine). Nothing here invents a probability or a
price. Every limit is yours to set; a limit left as None is not applied.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


PAYOUT = 1.0            # a winning contract settles at 1.00
MIN_PRICE = 0.02        # ForecastEx contract price floor
MAX_PRICE = 0.99        # ForecastEx contract price ceiling


@dataclass
class Contract:
    event_id: str
    category: str          # e.g. "economic_indicator", "fed_funds"
    yes_price: float       # current market price of the Yes side, 0.02..0.99
    p_hat: float           # YOUR probability estimate for the Yes outcome, 0..1


@dataclass
class Decision:
    event_id: str
    category: str
    side: str | None       # "YES", "NO", or None (no trade)
    entry_price: float | None
    ev_per_contract: float
    kelly_full: float      # full-Kelly fraction for the chosen side (0 if no trade)


def _validate(price: float, p_hat: float) -> None:
    if not (MIN_PRICE <= price <= MAX_PRICE):
        raise ValueError(f"price {price} outside ForecastEx range {MIN_PRICE}..{MAX_PRICE}")
    if not (0.0 <= p_hat <= 1.0):
        raise ValueError(f"p_hat {p_hat} outside 0..1")


def kelly_fraction(p_win: float, cost: float) -> float:
    """Full-Kelly fraction of bankroll for a binary contract that costs `cost`
    and pays 1.00. Returns 0 when the bet has no positive edge.
    f* = (p_win - cost) / (1 - cost)."""
    if cost >= 1.0:
        return 0.0
    f = (p_win - cost) / (1.0 - cost)
    return max(0.0, f)


def decide(contract: Contract, min_edge_ev: float, fee: float = 0.01) -> Decision:
    """Pick the side with positive expected value above the threshold, if any."""
    _validate(contract.yes_price, contract.p_hat)
    c = contract.yes_price
    p = contract.p_hat

    ev_yes = p - c - fee
    ev_no = (c - p) - fee   # buying No at (1 - c), pays 1 if outcome is No

    if ev_yes >= ev_no and ev_yes > min_edge_ev:
        return Decision(contract.event_id, contract.category, "YES", c, ev_yes,
                        kelly_fraction(p, c))
    if ev_no > min_edge_ev:
        no_cost = 1.0 - c
        return Decision(contract.event_id, contract.category, "NO", no_cost, ev_no,
                        kelly_fraction(1.0 - p, no_cost))
    return Decision(contract.event_id, contract.category, None, None,
                    max(ev_yes, ev_no), 0.0)


@dataclass
class Position:
    event_id: str
    category: str
    side: str
    entry_price: float
    contracts: int
    stake: float           # capital at risk = entry_price * contracts (max loss)
    ev_per_contract: float


def size_position(decision: Decision, bankroll: float, *,
                  max_stake_per_event: float | None,
                  kelly_cap: float | None) -> Position | None:
    """Turn a decision into a sized position under your caps.

    Sizing is the smaller of: a capped fraction of Kelly applied to bankroll,
    and max_stake_per_event. A binary long loses at most its premium, so the
    stake is the capital at risk. Returns None if nothing clears or no cap set."""
    if decision.side is None or decision.entry_price is None:
        return None

    stake_options = []
    if kelly_cap is not None:
        stake_options.append(kelly_cap * decision.kelly_full * bankroll)
    if max_stake_per_event is not None:
        stake_options.append(max_stake_per_event)
    if not stake_options:
        raise ValueError("Set at least one of kelly_cap or max_stake_per_event; "
                         "no default sizing is assumed.")
    stake = min(stake_options)
    contracts = int(math.floor(stake / decision.entry_price))
    if contracts <= 0:
        return None
    real_stake = contracts * decision.entry_price
    return Position(decision.event_id, decision.category, decision.side,
                    decision.entry_price, contracts, real_stake,
                    decision.ev_per_contract)


def build_book(contracts: list[Contract], bankroll: float, *,
               min_edge_ev: float,
               max_stake_per_event: float | None = None,
               kelly_cap: float | None = None,
               max_positions: int | None = None,
               max_book_risk: float | None = None,
               max_category_pct: float | None = None,
               fee: float = 0.01) -> dict:
    """Build the recommended event book under capital-conservation caps.

    Positions are ranked by expected value per contract and admitted while they
    respect the caps. Every cap is yours; a cap left as None is not applied.
    Returns the admitted positions, the ones the caps rejected, and book totals.
    """
    ranked = sorted(
        (decide(c, min_edge_ev, fee) for c in contracts),
        key=lambda d: d.ev_per_contract, reverse=True,
    )

    admitted: list[Position] = []
    rejected: list[dict] = []
    book_risk = 0.0
    by_category: dict[str, float] = {}

    for d in ranked:
        if d.side is None:
            continue
        pos = size_position(d, bankroll,
                            max_stake_per_event=max_stake_per_event,
                            kelly_cap=kelly_cap)
        if pos is None:
            rejected.append({"event_id": d.event_id, "reason": "no size after caps"})
            continue
        if max_positions is not None and len(admitted) >= max_positions:
            rejected.append({"event_id": d.event_id, "reason": "max_positions reached"})
            continue
        if max_book_risk is not None and book_risk + pos.stake > max_book_risk:
            rejected.append({"event_id": d.event_id, "reason": "would exceed max_book_risk"})
            continue
        if max_category_pct is not None and max_book_risk:
            cat_after = by_category.get(pos.category, 0.0) + pos.stake
            if 100.0 * cat_after / max_book_risk > max_category_pct:
                rejected.append({"event_id": d.event_id,
                                 "reason": f"would exceed max_category_pct in {pos.category}"})
                continue
        admitted.append(pos)
        book_risk += pos.stake
        by_category[pos.category] = by_category.get(pos.category, 0.0) + pos.stake

    return {
        "positions": admitted,
        "rejected": rejected,
        "book_risk": book_risk,
        "risk_by_category": by_category,
        "expected_value": sum(p.contracts * p.ev_per_contract for p in admitted),
    }
