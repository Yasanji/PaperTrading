import json
from ibkr import IBKR

ib = IBKR()

def show(name, fn):
    print(f"\n--- {name} ---")
    try:
        print(json.dumps(fn(), indent=2, default=str))
    except Exception as e:
        print(f"{name} error: {e}")

show("tickle", ib.tickle)
show("auth_status", ib.auth_status)
show("accounts", ib.accounts)
show("portfolio_accounts", ib.portfolio_accounts)
