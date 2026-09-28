"""Print contract-id candidates for the two names so you can fill live_config.py.

Run the Client Portal gateway and log in first (see README), then:

    python find_conids.py

Read the list, pick the row for the EUR listing you want, and copy its conid
into conid_y (Safran) and conid_x (Siemens) in live_config.py.
"""
from ibkr import IBKR

SYMBOLS = ["SAF", "SIE"]  # Safran, Siemens


def main():
    ib = IBKR()
    # Prime the brokerage session before any iserver data call.
    try:
        ib.tickle()
        ib.reinit()
        ib.accounts()
    except Exception as e:
        print(f'session init warning: {e}')
    for sym in SYMBOLS:
        print(f"\n=== search: {sym} ===")
        results = ib.search(sym) or []
        if not results:
            print("no results")
            continue
        for r in results[:10]:
            conid = r.get("conid")
            header = r.get("companyHeader") or r.get("companyName") or ""
            desc = r.get("description") or ""
            sec = r.get("secType") or ""
            print(f"conid={conid}  {sec}  {header}  {desc}")


if __name__ == "__main__":
    main()
