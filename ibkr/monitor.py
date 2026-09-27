"""Drawdown and relative-value monitor for an IBKR paper account.

Set the limits below. Any limit left as None is skipped, so you turn checks on
by giving them a number. Nothing here assumes a threshold or an instrument.

Run the gateway first (see README), then:  python monitor.py
"""

import json
import time
from pathlib import Path

from ibkr import IBKR

# ---------------------------------------------------------------------------
# CONFIG. Fill these in. A limit of None means "do not check this".
# ---------------------------------------------------------------------------
ACCOUNT = None            # your paper account id, e.g. "DU1234567"
BASE_CCY = "USD"          # currency for the exposure and cash checks
INTERVAL = 60             # seconds between checks

MAX_DRAWDOWN_PCT = None   # percent off the equity high-water mark, e.g. 5
MAX_GROSS_EXPOSURE = None # sum of |market value| in BASE_CCY
MAX_NET_EXPOSURE = None   # |sum of market value| in BASE_CCY
MAX_CONCENTRATION = None  # largest position as percent of gross, 0-100
MIN_CASH = None           # cash floor in BASE_CCY
MAX_OPEN_ORDERS = None    # number of live orders

# Relative-value pair on futures / indices. Fill the two contract ids once you
# choose the instruments; leave them None to skip the pair checks.
RV_LONG_CONID = None
RV_SHORT_CONID = None
RV_MAX_IMBALANCE_PCT = None   # allowed notional imbalance between the legs, percent
RV_RATIO_MIN = None           # lower bound on long price / short price
RV_RATIO_MAX = None           # upper bound on long price / short price

PEAK_FILE = "peak.json"       # where the equity high-water mark is stored
# ---------------------------------------------------------------------------


def get_state(ib, account):
    """Pull positions, ledger and live orders. Returns only gateway values."""
    ib.portfolio_accounts()                       # required before positions
    positions, page = [], 0
    while True:
        batch = ib.positions(account, page) or []
        positions += batch
        if len(batch) < 100:
            break
        page += 1
    ledger = ib.ledger(account) or {}
    orders = ib.live_orders()
    if isinstance(orders, dict):
        orders = orders.get("orders", [])
    return {"positions": positions, "ledger": ledger, "orders": orders or []}


def gross_exposure(state, ccy):
    return sum(abs(p["mktValue"]) for p in state["positions"]
               if p.get("currency") == ccy and p.get("mktValue") is not None)


def net_exposure(state, ccy):
    return sum(p["mktValue"] for p in state["positions"]
               if p.get("currency") == ccy and p.get("mktValue") is not None)


def largest_position(state, ccy):
    vals = [abs(p["mktValue"]) for p in state["positions"]
            if p.get("currency") == ccy and p.get("mktValue") is not None]
    return max(vals) if vals else 0.0


def cash_balance(state, ccy):
    entry = state["ledger"].get(ccy)
    if isinstance(entry, dict) and entry.get("cashbalance") is not None:
        return float(entry["cashbalance"])
    return None


def net_liquidation(state, ccy):
    entry = state["ledger"].get(ccy)
    if isinstance(entry, dict) and entry.get("netliquidationvalue") is not None:
        return float(entry["netliquidationvalue"])
    return None


def position_by_conid(state, conid):
    for p in state["positions"]:
        if str(p.get("conid")) == str(conid):
            return p
    return None


def load_peak():
    try:
        return json.loads(Path(PEAK_FILE).read_text())
    except (OSError, ValueError):
        return {}


def save_peak(peak):
    Path(PEAK_FILE).write_text(json.dumps(peak))


def evaluate(state, peak):
    """Return a list of breach messages. Each check is skipped if its limit
    is None or the gateway did not report the value it needs."""
    breaches = []

    if MAX_GROSS_EXPOSURE is not None:
        g = gross_exposure(state, BASE_CCY)
        if g > MAX_GROSS_EXPOSURE:
            breaches.append(f"gross exposure {g:.0f} {BASE_CCY} > {MAX_GROSS_EXPOSURE}")

    if MAX_NET_EXPOSURE is not None:
        n = abs(net_exposure(state, BASE_CCY))
        if n > MAX_NET_EXPOSURE:
            breaches.append(f"abs net exposure {n:.0f} {BASE_CCY} > {MAX_NET_EXPOSURE}")

    if MAX_CONCENTRATION is not None:
        g = gross_exposure(state, BASE_CCY)
        if g > 0:
            c = 100.0 * largest_position(state, BASE_CCY) / g
            if c > MAX_CONCENTRATION:
                breaches.append(f"concentration {c:.1f}% > {MAX_CONCENTRATION}%")

    if MIN_CASH is not None:
        cash = cash_balance(state, BASE_CCY)
        if cash is not None and cash < MIN_CASH:
            breaches.append(f"cash {cash:.0f} {BASE_CCY} < floor {MIN_CASH}")

    if MAX_OPEN_ORDERS is not None:
        if len(state["orders"]) > MAX_OPEN_ORDERS:
            breaches.append(f"open orders {len(state['orders'])} > {MAX_OPEN_ORDERS}")

    if MAX_DRAWDOWN_PCT is not None:
        now = net_liquidation(state, BASE_CCY)
        top = peak.get(BASE_CCY)
        if now is not None and top:
            dd = 100.0 * (top - now) / top
            if dd > MAX_DRAWDOWN_PCT:
                breaches.append(f"drawdown {dd:.1f}% (peak {top:.0f}, now {now:.0f}) > {MAX_DRAWDOWN_PCT}%")

    if RV_LONG_CONID is not None and RV_SHORT_CONID is not None:
        lp = position_by_conid(state, RV_LONG_CONID)
        sp = position_by_conid(state, RV_SHORT_CONID)
        if lp and sp:
            if (RV_MAX_IMBALANCE_PCT is not None
                    and lp.get("mktValue") is not None and sp.get("mktValue") is not None):
                a, b = abs(lp["mktValue"]), abs(sp["mktValue"])
                base = max(a, b)
                if base > 0:
                    imb = 100.0 * abs(a - b) / base
                    if imb > RV_MAX_IMBALANCE_PCT:
                        breaches.append(f"RV leg imbalance {imb:.1f}% > {RV_MAX_IMBALANCE_PCT}%")
            if (RV_RATIO_MIN is not None and RV_RATIO_MAX is not None
                    and lp.get("mktPrice") and sp.get("mktPrice")):
                ratio = float(lp["mktPrice"]) / float(sp["mktPrice"])
                if ratio < RV_RATIO_MIN or ratio > RV_RATIO_MAX:
                    breaches.append(f"RV price ratio {ratio:.4f} outside [{RV_RATIO_MIN}, {RV_RATIO_MAX}]")

    return breaches


def main():
    if not ACCOUNT:
        raise SystemExit("Set ACCOUNT to your paper account id (starts with DU).")

    ib = IBKR()
    peak = load_peak()
    print(f"Monitoring {ACCOUNT}, every {INTERVAL}s. Ctrl-C to stop.")

    while True:
        try:
            tick = ib.tickle()
            auth = (tick or {}).get("iserver", {}).get("authStatus", {})
            if auth.get("authenticated") is False:
                print("  session dropped, re-initialising ...")
                ib.reinit()

            state = get_state(ib, ACCOUNT)

            now = net_liquidation(state, BASE_CCY)
            if now is not None:
                peak[BASE_CCY] = max(peak.get(BASE_CCY, now), now)
                save_peak(peak)

            breaches = evaluate(state, peak)
            stamp = time.strftime("%Y-%m-%d %H:%M:%S")
            if breaches:
                for b in breaches:
                    print(f"[{stamp}] BREACH: {b}")
            else:
                print(f"[{stamp}] ok, {len(state['positions'])} positions, {len(state['orders'])} orders")

        except Exception as exc:                 # keep the loop alive on a transient error
            print(f"[{time.strftime('%H:%M:%S')}] cycle error: {exc}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
