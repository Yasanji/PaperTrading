"""A simple risk screen for the paper book, printed as one table.

Reuses ibkr.py, statarb.py, data.py and monitor.py. Every value comes from the
gateway or the price history; nothing is assumed. Limits come from
live_config.py.

    python status.py          one snapshot
    python status.py --loop   refresh every 30 seconds
"""
import json
import os
import sys
import time

from ibkr import IBKR
from statarb import latest_signal
from data import align, closes_from_history
from live_config import LiveConfig
import monitor as M

cfg = LiveConfig()
STATE_WORD = {1: "LONG spread", -1: "SHORT spread", 0: "FLAT"}


def ensure_session(ib):
    tick = ib.tickle() or {}
    auth = tick.get("iserver", {}).get("authStatus", {}) if isinstance(tick, dict) else {}
    if auth.get("authenticated") is False:
        try:
            ib.reinit()
        except Exception:
            pass
        auth = ib.auth_status() or {}
    return auth


def first_ccy(fn):
    for ccy in ("BASE", "USD", cfg.base_ccy):
        v = fn(ccy)
        if v is not None:
            return v
    return None


def fmt(v, dp=2):
    return "" if v is None else f"{v:,.{dp}f}"


def rows():
    ib = IBKR()
    auth = ensure_session(ib)
    r = []
    r.append(("Session authenticated", str(auth.get("authenticated")), ""))
    r.append(("Account", cfg.account, "paper" ))

    state = M.get_state(ib, cfg.account)

    # signal
    z = beta = None
    target = 0
    asof = ""
    try:
        def closes(c):
            return closes_from_history(ib.history(c, period=cfg.period, bar=cfg.bar))
        dates, y, x = align(closes(cfg.conid_y), closes(cfg.conid_x))
        prev = 0
        if os.path.exists(cfg.state_file):
            try:
                prev = json.load(open(cfg.state_file)).get("prev_target", 0)
            except Exception:
                prev = 0
        sig = latest_signal(y, x, cfg.lookback, cfg.entry_z, cfg.exit_z, prev)
        z, beta, target, asof = sig.z, sig.beta, sig.target, dates[-1]
    except Exception as exc:
        r.append(("Signal", f"unavailable: {exc}", ""))

    if z is not None:
        r.append(("Spread z-score", f"{z:+.2f}", f"entry +/-{cfg.entry_z:.1f}, exit {cfg.exit_z:.1f}"))
        r.append(("Distance to entry", f"{max(0.0, cfg.entry_z - abs(z)):.2f}", ""))
        r.append(("Hedge ratio (beta)", f"{beta:.3f}", ""))
        r.append(("Spread state", STATE_WORD.get(target, str(target)), f"as of {asof}"))

    # account
    eq = first_ccy(lambda c: M.net_liquidation(state, c))
    cash = first_ccy(lambda c: M.cash_balance(state, c))
    peak = M.load_peak()
    key = "BASE"
    if eq is not None:
        peak[key] = max(peak.get(key, eq), eq)
        M.save_peak(peak)
    top = peak.get(key)
    dd = (100.0 * (top - eq) / top) if (eq is not None and top) else None
    r.append(("Equity", fmt(eq), "base ccy"))
    r.append(("Cash", fmt(cash), "base ccy"))
    r.append(("Drawdown %", fmt(dd), f"limit {M.MAX_DRAWDOWN_PCT}%"))

    # risk in EUR (the legs)
    gross = M.gross_exposure(state, cfg.base_ccy)
    net = M.net_exposure(state, cfg.base_ccy)
    conc = (100.0 * M.largest_position(state, cfg.base_ccy) / gross) if gross else None
    r.append(("Gross exposure", f"{gross:,.0f} {cfg.base_ccy}", f"cap {cfg.max_gross:,.0f}"))
    r.append(("Net exposure", f"{net:,.0f} {cfg.base_ccy}", "target ~0"))
    r.append(("Concentration %", fmt(conc), "max 70"))
    r.append(("Per-name cap", f"{cfg.per_name_cap:,.0f} {cfg.base_ccy}", "each leg"))
    r.append(("Open orders", str(len(state["orders"])), ""))

    # positions
    if state["positions"]:
        for p in state["positions"]:
            name = str(p.get("contractDesc"))[:24]
            val = f"{p.get('position', 0)} @ {fmt(p.get('mktPrice'))}"
            note = f"uPnL {fmt(p.get('unrealizedPnl'), 0)}"
            r.append((f"Position {name}", val, note))
    else:
        r.append(("Positions", "none (flat)", ""))

    breaches = M.evaluate(state, peak)
    r.append(("Breaches", "none" if not breaches else "; ".join(breaches), ""))
    return r


def render(r):
    w0 = max(len(a) for a, _, _ in r)
    w1 = max(len(str(b)) for _, b, _ in r)
    head = f" {'METRIC'.ljust(w0)}  {'VALUE'.ljust(w1)}  LIMIT / NOTE"
    line = " " + "-" * (len(head) + 8)
    out = [f" PAPER BOOK RISK SCREEN   {cfg.account}   {time.strftime('%Y-%m-%d %H:%M:%S')}",
           line, head, line]
    for a, b, c in r:
        out.append(f" {a.ljust(w0)}  {str(b).ljust(w1)}  {c}")
    out.append(line)
    return "\n".join(out)


def main():
    loop = "--loop" in sys.argv
    if not loop:
        print(render(rows()))
        return
    while True:
        os.system("clear")
        print(render(rows()))
        print("\n refreshing every 30s, Ctrl-C to stop")
        time.sleep(30)


if __name__ == "__main__":
    main()
