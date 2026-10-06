"""Read-only: find Interactive Brokers symbols for instruments the contract check could not find."""
from ib_async import IB, Contract
QUERIES = ['silver', 'SIL', 'natural gas', 'Henry Hub', 'MNG', 'STOXX 600', 'SXXP', 'FXXP']
CANDIDATES = [('SIL', 'COMEX'), ('QI', 'COMEX'), ('SILVER', 'COMEX'), ('MNG', 'NYMEX'), ('QG', 'NYMEX'), ('SXXP', 'EUREX'), ('FXXP', 'EUREX')]
ib = IB(); ib.connect('127.0.0.1', 4002, clientId=3, readonly=True)
print('== Symbol search (futures only)')
for q in QUERIES:
    for d in ib.reqMatchingSymbols(q) or []:
        c = d.contract
        if 'FUT' in (d.derivativeSecTypes or []):
            print(f'  {q:12s} -> {c.symbol:8s} {c.primaryExchange:8s} {c.currency:4s} {c.description[:50] if hasattr(c, "description") else ""}')
print('\n== Futures contracts for each candidate (first 3)')
for sym, exch in CANDIDATES:
    det = ib.reqContractDetails(Contract(secType='FUT', symbol=sym, exchange=exch))
    if not det: print(f'  {sym:6s} {exch:6s} none'); continue
    for d in det[:3]:
        c = d.contract
        print(f'  {sym:6s} {exch:6s} {c.localSymbol:12s} class {c.tradingClass:6s} mult {c.multiplier:>8s} ccy {c.currency} expiry {c.lastTradeDateOrContractMonth} | {d.longName[:40]}')
ib.disconnect()
