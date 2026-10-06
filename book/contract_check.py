"""Build step 1: contract check. Read-only. Run on the Mac with IB Gateway running:  python contract_check.py
For each instrument: find it at Interactive Brokers, read its specification, measure its volatility, and test whether it can be
sized within 25% of its target risk under the portfolio rules. Writes contract_check_<date>.csv. Sends no orders."""
import math, datetime as dt, pandas as pd, yfinance as yf
from ib_async import IB, Contract

# ---- Assumptions (from the portfolio pre-registration; edit here, nothing is hidden) ----
NAV = 1_000_000           # paper book, US dollars
BOOK_VOL = 0.06           # book volatility target
N_PODS = 6                # pods at equal target risk; roughly uncorrelated, so each pod's risk = book risk / sqrt(6)
TREND_SHARE, CARRY_SHARE = 0.75, 0.25      # Pod 1 split
TREND_MARKETS, TREND_DIVERSIFICATION = 15, 2.7   # 2.7 = undiversified / actual volatility, trend over 2013-2022 (Ratnaike, 2026)
CARRY_POSITIONS = 6       # 3 long, 3 short; treated as uncorrelated
VIX_LOSS_LIMIT = 0.03     # Pod 6: a doubling of the VIX future may lose at most 3% of pod capital
TOLERANCE = 0.25          # a market is sizeable if whole contracts land within 25% of target

pod_risk = NAV * BOOK_VOL / math.sqrt(N_PODS)
trend_target = pod_risk * TREND_SHARE * TREND_DIVERSIFICATION / TREND_MARKETS
carry_target = pod_risk * CARRY_SHARE * math.sqrt(CARRY_POSITIONS) / CARRY_POSITIONS

# ---- Instruments: (market, use, candidates tried in order as (symbol, exchange, currency)) ----
F = 'FUT'
INSTRUMENTS = [
 ('S&P 500', 'trend', [('MES', 'CME', 'USD')]), ('Nasdaq-100', 'trend', [('MNQ', 'CME', 'USD')]),
 ('2y Treasury', 'trend', [('ZT', 'CBOT', 'USD')]), ('10y Treasury', 'trend', [('ZN', 'CBOT', 'USD')]),
 ('30y Treasury', 'trend', [('ZB', 'CBOT', 'USD')]),
 ('WTI crude', 'trend', [('MCL', 'NYMEX', 'USD'), ('CL', 'NYMEX', 'USD')]),
 ('Natural gas', 'trend', [('MHNG', 'NYMEX', 'USD'), ('QG', 'NYMEX', 'USD'), ('NG', 'NYMEX', 'USD')]),
 ('Gold', 'trend', [('MGC', 'COMEX', 'USD'), ('GC', 'COMEX', 'USD')]),
 ('Silver', 'trend', [('SIC', 'COMEX', 'USD'), ('QI', 'COMEX', 'USD'), ('SI', 'COMEX', 'USD')]),
 ('Copper', 'trend', [('MHG', 'COMEX', 'USD'), ('HG', 'COMEX', 'USD')]),
 ('Euro', 'trend+carry', [('M6E', 'CME', 'USD'), ('EUR', 'CME', 'USD')]),
 ('Yen', 'trend+carry', [('MJY', 'CME', 'USD'), ('JPY', 'CME', 'USD')]),
 ('Pound', 'trend+carry', [('M6B', 'CME', 'USD'), ('GBP', 'CME', 'USD')]),
 ('Australian dollar', 'trend+carry', [('M6A', 'CME', 'USD'), ('AUD', 'CME', 'USD')]),
 ('Canadian dollar', 'trend+carry', [('MCD', 'CME', 'USD'), ('CAD', 'CME', 'USD')]),
 ('Swiss franc', 'carry', [('MSF', 'CME', 'USD'), ('CHF', 'CME', 'USD')]),
 ('New Zealand dollar', 'carry', [('NZD', 'CME', 'USD')]),
 ('Mini VIX', 'volatility', [('VXM', 'CFE', 'USD')]),
 ('STOXX Europe 600', 'hedge', [('DJ600', 'EUREX', 'EUR')]),
 ('Hang Seng (mini)', 'hedge', [('MHI', 'HKFE', 'HKD'), ('HSI', 'HKFE', 'HKD')]),
]

def fx_to_usd(ccy):
    if ccy == 'USD': return 1.0
    s = yf.download(f'{ccy}USD=X', period='5d', progress=False, auto_adjust=False)['Close'].squeeze().dropna()
    return float(s.iloc[-1])

ib = IB(); ib.connect('127.0.0.1', 4002, clientId=2, readonly=True)
acct = ib.managedAccounts()[0]
assert acct == open(__import__('os').path.expanduser('~/.delta1/paper_account')).read().strip(), 'Not the paper account: stopping.'
ib.reqMarketDataType(3)   # delayed data is enough
rows = []
for market, use, cands in INSTRUMENTS:
    row = dict(market=market, use=use, found=None, tried=', '.join(c[0] for c in cands))
    for sym, exch, ccy in cands:
        det = ib.reqContractDetails(Contract(secType='CONTFUT', symbol=sym, exchange=exch, currency=ccy))
        if det:
            d = det[0]; c = d.contract
            row.update(found=sym, exchange=exch, currency=ccy, multiplier=float(c.multiplier or 1), min_tick=d.minTick,
                       local_symbol=c.localSymbol, expiry=c.lastTradeDateOrContractMonth, order_types=d.orderTypes[:120])
            fut = Contract(secType='FUT', conId=c.conId, exchange=exch)
            bars = ib.reqHistoricalData(fut, endDateTime='', durationStr='6 M', barSizeSetting='1 day', whatToShow='TRADES', useRTH=True)
            if bars:
                px = pd.Series([b.close for b in bars]); r = px.pct_change().dropna()
                fx = fx_to_usd(ccy); notional = px.iloc[-1] * row['multiplier'] * fx
                row.update(price=px.iloc[-1], notional_usd=round(notional), ann_vol=round(r.std() * math.sqrt(252), 4),
                           risk_per_contract=round(notional * r.std() * math.sqrt(252)))
            else: row['note'] = 'no price history (market data permission?)'
            break
    if row['found'] is None: row['note'] = 'not found at Interactive Brokers'
    # target and verdict
    if 'risk_per_contract' in row:
        if use.startswith('trend'): target = trend_target
        elif use == 'carry': target = carry_target
        elif use == 'volatility':
            target = None; n = math.floor(NAV / N_PODS * VIX_LOSS_LIMIT / (row['price'] * row['multiplier']))
            row.update(contracts=n, verdict='OK' if n >= 1 else 'TOO LARGE')
        else: target = None; row['verdict'] = 'hedge: size set by the equity pods'
        if target:
            exact = target / row['risk_per_contract']; n = max(1, round(exact)) if exact >= 0.5 else 0
            err = abs(n - exact) / exact
            row.update(target_risk=round(target), exact_contracts=round(exact, 2), contracts=n, sizing_error=f'{err:.0%}',
                       verdict='TRADED' if n >= 1 else 'LEFT OUT (under half a contract)')
    rows.append(row)
ib.disconnect()

out = pd.DataFrame(rows)
fn = f'contract_check_{dt.date.today().isoformat()}.csv'; out.to_csv(fn, index=False)
cols = [c for c in ['market', 'found', 'multiplier', 'currency', 'notional_usd', 'ann_vol', 'risk_per_contract', 'target_risk', 'exact_contracts', 'contracts', 'verdict', 'note'] if c in out]
print(f'pod risk ${pod_risk:,.0f} | trend target per market ${trend_target:,.0f} | carry target per position ${carry_target:,.0f}\n')
print(out[cols].to_string(index=False)); print(f'\nsaved {fn}')

# Sleeve check (Amendment 4): each sleeve's total risk within 25% of its target
for use, target, n_slots in (('trend', trend_target, TREND_MARKETS),):
    t = out[out.use.str.startswith(use) & (out.contracts > 0)]
    actual = (t.contracts * t.risk_per_contract).sum(); full = target * n_slots
    print(f"\n{use} sleeve: {len(t)} of {n_slots} markets traded, risk {actual:,.0f} = {actual / full:.0%} of target {full:,.0f}: {'PASS' if abs(actual / full - 1) <= TOLERANCE else 'FAIL'}")
