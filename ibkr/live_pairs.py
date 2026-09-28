"""Live paper runner for the SAF and SIE pair on the Client Portal Web API.

It reuses the existing modules: ibkr.py for the client, statarb.py for the
point-in-time engine, and data.py for parsing the gateway's history. One pass
pulls history for both legs, computes the latest signal, sizes beta-neutral
legs, runs pre-trade checks, reconciles against the account, and then places
or, in a dry run, logs the orders.

It defaults to a dry run and refuses a non-paper account. Run the gateway and
log in first, set live_config.py, then:

    python live_pairs.py
"""
import json
import logging
import os

from ibkr import IBKR
from statarb import latest_signal, target_legs
from data import align, closes_from_history
from live_config import LiveConfig

log = logging.getLogger("live_pairs")


def setup_logging(cfg: LiveConfig) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(cfg.log_file)],
    )


def load_state(cfg: LiveConfig) -> dict:
    if os.path.exists(cfg.state_file):
        with open(cfg.state_file) as f:
            return json.load(f)
    return {"prev_target": 0}


def save_state(cfg: LiveConfig, state: dict) -> None:
    with open(cfg.state_file, "w") as f:
        json.dump(state, f, indent=2)


def ensure_session(ib: IBKR) -> None:
    ib.tickle()
    status = ib.auth_status() or {}
    if not status.get("authenticated"):
        ib.reinit()
        status = ib.auth_status() or {}
    if not status.get("authenticated"):
        raise SystemExit(
            "Gateway is not authenticated. Log in at https://localhost:5000 first."
        )
    ib.accounts()  # required before market data


def get_closes(ib: IBKR, conid: int, cfg: LiveConfig):
    hist = ib.history(conid, period=cfg.period, bar=cfg.bar)
    rows = closes_from_history(hist)
    if not rows:
        raise SystemExit(f"No history returned for conid {conid}")
    return rows


def current_position(ib: IBKR, account: str, conid: int) -> int:
    page = 0
    while True:
        rows = ib.positions(account, page) or []
        for p in rows:
            if int(p.get("conid", -1)) == conid:
                return int(p.get("position", 0))
        if len(rows) < 100:
            return 0
        page += 1


def place_order(ib: IBKR, account: str, conid: int, side: str, qty: int):
    order = {"conid": conid, "orderType": "MKT", "side": side, "quantity": qty, "tif": "DAY"}
    resp = ib.place(account, order)
    # Clear any confirmation prompts the gateway returns before the order is live.
    for _ in range(5):
        if isinstance(resp, list) and resp and resp[0].get("id") and not resp[0].get("order_id"):
            resp = ib.confirm(resp[0]["id"])
        else:
            break
    return resp


def run_once(cfg: LiveConfig) -> None:
    if not cfg.account or not cfg.conid_y or not cfg.conid_x:
        raise SystemExit(
            "Set account, conid_y and conid_x in live_config.py first (see find_conids.py)."
        )
    if cfg.paper_only and not cfg.account.startswith("DU"):
        raise SystemExit(
            f"paper_only is set and account {cfg.account} is not a paper (DU) account. Refusing."
        )

    state = load_state(cfg)
    ib = IBKR()
    ensure_session(ib)

    y_rows = get_closes(ib, cfg.conid_y, cfg)
    x_rows = get_closes(ib, cfg.conid_x, cfg)
    dates, y, x = align(y_rows, x_rows)
    if len(dates) < cfg.lookback + 1:
        raise SystemExit(f"Only {len(dates)} aligned bars; need more than {cfg.lookback}.")

    sig = latest_signal(y, x, cfg.lookback, cfg.entry_z, cfg.exit_z, state.get("prev_target", 0))
    y_price, x_price = y[-1], x[-1]
    legs = target_legs(sig.target, sig.beta, y_price, x_price, cfg.gross_per_leg)
    qty_y = round(legs["y_notional"] / y_price) if y_price else 0
    qty_x = round(legs["x_notional"] / x_price) if x_price else 0
    log.info(
        "z=%s beta=%.4f target=%d qty_y=%d qty_x=%d",
        None if sig.z is None else round(sig.z, 2), sig.beta, sig.target, qty_y, qty_x,
    )

    gross = abs(qty_y) * y_price + abs(qty_x) * x_price
    breaches = []
    if gross > cfg.max_gross:
        breaches.append(f"gross {gross:.0f} over cap {cfg.max_gross:.0f}")
    if abs(qty_y) * y_price > cfg.per_name_cap:
        breaches.append(f"leg y {abs(qty_y) * y_price:.0f} over per-name cap {cfg.per_name_cap:.0f}")
    if abs(qty_x) * x_price > cfg.per_name_cap:
        breaches.append(f"leg x {abs(qty_x) * x_price:.0f} over per-name cap {cfg.per_name_cap:.0f}")
    if breaches:
        log.warning("Pre-trade checks failed, no orders: %s", breaches)
        save_state(cfg, state)
        return

    legs_plan = ((cfg.conid_y, qty_y, "SAF"), (cfg.conid_x, qty_x, "SIE"))
    for conid, target, name in legs_plan:
        current = current_position(ib, cfg.account, conid)
        delta = target - current
        if delta == 0:
            continue
        side = "BUY" if delta > 0 else "SELL"
        qty = abs(delta)
        if cfg.dry_run:
            log.info(
                "[DRY RUN] would %s %d %s (conid %d, current %d, target %d)",
                side, qty, name, conid, current, target,
            )
            continue
        resp = place_order(ib, cfg.account, conid, side, qty)
        log.info("Placed %s %d %s -> %s", side, qty, name, resp)

    state["prev_target"] = sig.target
    save_state(cfg, state)


if __name__ == "__main__":
    cfg = LiveConfig()
    setup_logging(cfg)
    run_once(cfg)
