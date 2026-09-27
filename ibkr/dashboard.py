"""A tiny local dashboard for the IBKR paper book.

It reuses ibkr.py and monitor.py, so the account id and the limits come from
the CONFIG block in monitor.py. The Python server talks to the gateway and
serves the numbers as JSON, so the browser never has to deal with the
gateway's self-signed certificate or cross origin rules.

Run the gateway first (see README), then:

    python dashboard.py

and open  http://localhost:8765  in a browser.
"""

import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from ibkr import IBKR
import monitor as M

PORT = 8765
ib = IBKR()

HERE = Path(__file__).resolve().parent
INDEX = HERE / "web" / "index.html"


def build_payload():
    """Pull the book once and return everything the page shows. Values come
    only from the gateway; a field the gateway did not return stays null."""
    tick = ib.tickle()
    auth = (tick or {}).get("iserver", {}).get("authStatus", {}) if isinstance(tick, dict) else {}
    authenticated = auth.get("authenticated")
    if authenticated is False:
        ib.reinit()

    state = M.get_state(ib, M.ACCOUNT)

    peak = M.load_peak()
    now = M.net_liquidation(state, M.BASE_CCY)
    if now is not None:
        peak[M.BASE_CCY] = max(peak.get(M.BASE_CCY, now), now)
        M.save_peak(peak)
    top = peak.get(M.BASE_CCY)

    gross = M.gross_exposure(state, M.BASE_CCY)
    net = M.net_exposure(state, M.BASE_CCY)
    concentration = (100.0 * M.largest_position(state, M.BASE_CCY) / gross) if gross else None
    drawdown = (100.0 * (top - now) / top) if (now is not None and top) else None

    positions = [
        {
            "desc": p.get("contractDesc"),
            "conid": p.get("conid"),
            "assetClass": p.get("assetClass"),
            "currency": p.get("currency"),
            "position": p.get("position"),
            "mktPrice": p.get("mktPrice"),
            "mktValue": p.get("mktValue"),
            "unrealizedPnl": p.get("unrealizedPnl"),
        }
        for p in state["positions"]
    ]

    return {
        "ok": True,
        "error": None,
        "authenticated": authenticated,
        "account": M.ACCOUNT,
        "base_ccy": M.BASE_CCY,
        "equity": now,
        "peak": top,
        "drawdown_pct": drawdown,
        "gross": gross,
        "net": net,
        "concentration_pct": concentration,
        "cash": M.cash_balance(state, M.BASE_CCY),
        "open_orders": len(state["orders"]),
        "positions": positions,
        "breaches": M.evaluate(state, peak),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # keep the console quiet

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/api/state"):
            try:
                payload = build_payload()
            except Exception as exc:
                payload = {"ok": False, "error": str(exc)}
            self._send(200, json.dumps(payload).encode(), "application/json")
            return
        try:
            html = INDEX.read_bytes()
        except OSError:
            html = b"<h1>web/index.html is missing</h1>"
        self._send(200, html, "text/html; charset=utf-8")


def main():
    if not M.ACCOUNT:
        raise SystemExit("Set ACCOUNT in monitor.py to your paper account id (starts with DU).")
    print(f"Dashboard on http://localhost:{PORT}  (account {M.ACCOUNT}). Ctrl-C to stop.")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
