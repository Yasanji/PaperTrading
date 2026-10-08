"""Pod 3: targets file and order file for one evening run. Sends nothing.

  1. Target notionals from pod.targets(as_of), converted to whole shares at the day's close and FX rate.
  2. Hedge contracts from pod.hedge().
  3. Orders = targets minus current positions (positions file from reconciliation; empty before launch).
  4. Writes book/targets/<date>_pod3.csv (committed to GitHub before any order) and book/orders/<date>_pod3.csv
     (for approve.py). Shares trade on the close (MOC); the hedge future at settlement (DESIGN.md s.4, s.12).

Usage: python orders.py AS_OF [NAV] [positions.csv]"""
import os, sys, hashlib, datetime as dt, pandas as pd, yfinance as yf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import pod

# Yahoo suffix -> Interactive Brokers primary exchange and currency
IB = {'.SW': ('EBS', 'CHF'), '.BR': ('ENEXT.BE', 'EUR'), '.ST': ('SFB', 'SEK'), '.DE': ('IBIS', 'EUR'), '.F': ('FWB', 'EUR'),
      '.L': ('LSE', 'GBP'), '.AS': ('AEB', 'EUR'), '.PA': ('SBF', 'EUR'), '.MI': ('BVME', 'EUR'), '.MC': ('BM', 'EUR'),
      '.HE': ('HEX', 'EUR'), '.CO': ('CPH', 'DKK'), '.OL': ('OSE', 'NOK'), '.VI': ('VSE', 'EUR'), '.IR': ('ISED', 'EUR'),
      '.LS': ('BVL', 'EUR'), '.WA': ('WSE', 'PLN'), '.AT': ('ATH', 'EUR')}
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def ib_contract(y):
    suf = '.' + y.split('.')[-1]; root = y[: -len(suf)]
    exch, ccy = IB.get(suf, ('SMART', 'USD'))
    sym = root.replace('-', ' ') if suf in ('.ST', '.CO', '.OL', '.HE') else root   # IB uses "ATCO A" for ATCO-A.ST
    return dict(ib_symbol=sym, sec_type='STK', exchange='SMART', primary_exchange=exch, currency=ccy)


def build(as_of, nav=pod.NAV, positions=None):
    t = pod.targets(as_of, nav)
    cols = ['date', 'pod', 'review', 'yahoo', 'ib_symbol', 'sec_type', 'exchange', 'primary_exchange', 'currency',
            'target_qty', 'target_notional_usd', 'price', 'reason']
    rows = []
    if not t.empty:
        ccys = {ib_contract(s)['currency'] for s in t.symbol} - {'USD'}
        px = yf.download(list(t.symbol) + [f'{c}USD=X' for c in ccys], period='10d', progress=False, auto_adjust=False)['Close'].ffill()
        px = px.loc[:pd.Timestamp(as_of)].iloc[-1] if pd.Timestamp(as_of) <= px.index[-1] else px.iloc[-1]
        for _, x in t.iterrows():
            c = ib_contract(x.symbol); p = float(px[x.symbol]); fx = 1.0 if c['currency'] == 'USD' else float(px[f"{c['currency']}USD=X"])
            if x.symbol.endswith('.L'): p /= 100                       # Yahoo quotes London in pence
            qty = int(abs(x.notional_usd) / (p * fx)) * (1 if x.notional_usd > 0 else -1)
            rows.append(dict(date=as_of, pod=3, review=x.review, yahoo=x.symbol, **c, target_qty=qty,
                             target_notional_usd=round(qty * p * fx, 2), price=p, reason=('ADD' if x.side > 0 else 'DELETE') + f' margin {x.margin:.2f}'))
        n, net, _ = pod.hedge(t)
        rows.append(dict(date=as_of, pod=3, review='hedge', yahoo=pod.HEDGE['yahoo'], ib_symbol=pod.HEDGE['symbol'], sec_type='FUT',
                         exchange='EUREX', primary_exchange='EUREX', currency='EUR', target_qty=n, target_notional_usd=None, price=None,
                         reason=f'net beta notional {net:,.0f} USD'))
    tg = pd.DataFrame(rows, columns=cols)
    pos = pd.read_csv(positions) if positions and os.path.exists(positions) else pd.DataFrame(columns=['ib_symbol', 'qty'])
    cur = dict(zip(pos.ib_symbol, pos.qty))
    od = tg[['ib_symbol', 'sec_type', 'exchange', 'primary_exchange', 'currency', 'target_qty', 'reason']].copy()
    od['current_qty'] = od.ib_symbol.map(cur).fillna(0)
    gone = [s for s in cur if s not in set(od.ib_symbol) and cur[s] != 0]   # positions no longer targeted are closed
    for s in gone: od.loc[len(od)] = dict(ib_symbol=s, sec_type='STK', exchange='SMART', primary_exchange='', currency='', target_qty=0, reason='exit', current_qty=cur[s])
    od['order_qty'] = od.target_qty - od.current_qty
    od = od[od.order_qty != 0]
    od['order_type'] = od.sec_type.map({'STK': 'MOC', 'FUT': 'MKT at settlement'})
    return tg, od


if __name__ == '__main__':
    as_of = sys.argv[1]; nav = float(sys.argv[2]) if len(sys.argv) > 2 else pod.NAV
    tg, od = build(as_of, nav, sys.argv[3] if len(sys.argv) > 3 else None)
    for sub, df in [('targets', tg), ('orders', od)]:
        d = os.path.join(ROOT, 'book', sub); os.makedirs(d, exist_ok=True)
        f = os.path.join(d, f'{as_of}_pod3.csv'); df.to_csv(f, index=False)
        print(f'{sub}: {f} ({len(df)} rows, sha256 {hashlib.sha256(open(f, "rb").read()).hexdigest()[:12]})')
    print(tg[['review', 'ib_symbol', 'primary_exchange', 'currency', 'target_qty', 'target_notional_usd']].to_string(index=False))
    print('\nORDERS (dry run, nothing sent):'); print(od[['ib_symbol', 'order_qty', 'order_type', 'reason']].to_string(index=False))
