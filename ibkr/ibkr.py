"""Minimal Client Portal Web API client for an IBKR paper account.

One method per HTTP call, nothing clever. The gateway runs on your Mac and
serves the API at https://localhost:5000/v1/api with a self-signed
certificate, so requests are made with verify=False.

Endpoints used here are the documented Client Portal paths (see README).
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = "https://localhost:5000/v1/api"


class IBKR:
    def __init__(self, base=BASE):
        self.base = base
        self.s = requests.Session()

    def _get(self, path, **params):
        r = self.s.get(self.base + path, params=params or None, verify=False, timeout=15)
        r.raise_for_status()
        return r.json() if r.content else None

    def _post(self, path, body=None):
        r = self.s.post(self.base + path, json=body, verify=False, timeout=15)
        r.raise_for_status()
        return r.json() if r.content else None

    def _delete(self, path):
        r = self.s.delete(self.base + path, verify=False, timeout=15)
        r.raise_for_status()
        return r.json() if r.content else None

    # session
    def tickle(self):
        return self._post("/tickle")                      # keepalive, ~every 60s

    def auth_status(self):
        return self._post("/iserver/auth/status")

    def reinit(self):
        return self._post("/iserver/auth/ssodh/init", {"publish": True, "compete": True})

    # accounts / portfolio
    def accounts(self):
        return self._get("/iserver/accounts")             # call once before market data

    def portfolio_accounts(self):
        return self._get("/portfolio/accounts")           # call before positions

    def positions(self, account, page=0):
        return self._get(f"/portfolio/{account}/positions/{page}")   # 100 per page

    def ledger(self, account):
        return self._get(f"/portfolio/{account}/ledger")

    # orders
    def live_orders(self):
        return self._get("/iserver/account/orders")

    def place(self, account, order):
        return self._post(f"/iserver/account/{account}/orders", {"orders": [order]})

    def confirm(self, reply_id):
        return self._post(f"/iserver/reply/{reply_id}", {"confirmed": True})

    def cancel(self, account, order_id):
        return self._delete(f"/iserver/account/{account}/order/{order_id}")

    # data
    def search(self, symbol):
        return self._get("/iserver/secdef/search", symbol=symbol)

    def market_snapshot(self, conids, fields):
        return self._get(
            "/iserver/marketdata/snapshot",
            conids=",".join(str(c) for c in conids),
            fields=",".join(str(f) for f in fields),
        )

    def history(self, conid, period="6m", bar="1d", outside_rth=False):
        """Historical bars. Each bar has t (unix ms), o, h, l, c, v.
        period examples: 1d, 1w, 1m, 6m, 1y. bar examples: 1min, 1h, 1d, 1w."""
        return self._get(
            "/iserver/marketdata/history",
            conid=conid, period=period, bar=bar,
            outsideRth=str(outside_rth).lower(),
        )
