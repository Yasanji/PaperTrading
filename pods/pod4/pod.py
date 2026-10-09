"""Pod 4: pre-dividend trade. Daily targets under POD4_PREREGISTRATION.md (passed all three tests, 9 October 2026).

  Entry:  buy at the close 15 trading days before the expected ex-date (anniversary of last year's matching ex-date),
          if the expected dividend (previous regular dividend) is 0.5% to 15% of the price, the stock has two years of
          dividends, a price on 240 of 252 days, and liquidity above its region's 20th percentile.
  Exit:   sell at the close on the actual ex-date (the announced date from Yahoo's calendar), or on the 30th trading day.
  Size:   10% of allocated capital each, at most 20, highest expected yield first, ties by ticker.
  Hedge:  each region's beta-weighted long exposure, short in its index future (DJ600, MES, MHI), whole contracts.

Timing in the book's chain: targets written on the evening of day D trade at the close of the next trading day E.
So a stock enters if E is its entry day, and exits if E is its announced ex-date or its 30th trading day.
Data: refresh.py, run before the evening chain. Interface (DESIGN.md s.3): targets(as_of, held), status(), checks()."""
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
DATA = os.path.join(ROOT, 'delta1', 'pod4'); UNIVERSE = os.path.join(ROOT, 'carry', 'sleeveB', 'universe_frozen.csv')
sys.path.insert(0, os.path.join(ROOT, 'book')); import config as C
NAV = C.NAV; N_PODS = C.N_PODS; SCALE = C.SCALE[4]; POS_SHARE = 0.10; MAX_POS = 20; LEAD = 15; MAX_HOLD = 30
IDX = {'EU': '^STOXX', 'US': '^GSPC', 'HK': '^HSI'}
HEDGE = {'EU': dict(symbol='DJ600', exchange='EUREX', currency='EUR', mult=50, fx='EURUSD=X'),
         'US': dict(symbol='MES', exchange='CME', currency='USD', mult=5, fx=None),
         'HK': dict(symbol='MHI', exchange='HKFE', currency='HKD', mult=10, fx='HKDUSD=X')}


def load():
    rd = lambda f, **k: pd.read_csv(os.path.join(DATA, f), **k)
    px = rd('prices.csv', index_col=0, parse_dates=True); vol = rd('volume.csv', index_col=0, parse_dates=True).reindex_like(px)
    dv = rd('dividends.csv', parse_dates=['date']).sort_values('date'); ix = rd('indices.csv', index_col=0, parse_dates=True)
    ex = rd('exdates.csv', parse_dates=['exdate']).set_index('yahoo').exdate if os.path.exists(os.path.join(DATA, 'exdates.csv')) else pd.Series(dtype='datetime64[ns]')
    return px, vol, dv, ix, ex


def regular(g):
    a = g.dividend.values; keep = [True]
    for k in range(1, len(a)): keep.append(a[k] <= 2 * np.median(a[max(0, k - 4):k]))
    return g[np.array(keep)]


def next_day(d):
    return pd.Timestamp(d) + pd.offsets.BDay(1)


def candidates(as_of, px, vol, dv, u):
    """Stocks whose entry day is the next trading day, with expected yield; ranked."""
    as_of = pd.Timestamp(as_of); E = next_day(as_of); px = px.loc[:as_of]; vol = vol.loc[:as_of]
    tv = (px * vol).iloc[-63:].median(); have = px.iloc[-252:].notna().sum()
    first = dv.groupby('yahoo').date.min(); out = []
    reg = pd.concat([regular(g) for _, g in dv.groupby('yahoo')]) if len(dv) else dv
    cut = {g: tv[[t for t in tv.index if u.get(t) == g]].dropna().quantile(0.2) for g in IDX}
    for t, g in reg.groupby('yahoo'):
        if t not in px or t not in u.index: continue
        exp = [e + pd.DateOffset(years=1) for e in g.date]
        if not any(E == e - pd.offsets.BDay(LEAD) for e in exp): continue      # E is 15 trading days before an expected ex-date
        prev = g[g.date <= as_of]; p = px[t].dropna()
        if prev.empty or p.empty or first[t] > as_of - pd.DateOffset(years=2): continue
        y = prev.dividend.iloc[-1] / p.iloc[-1]
        if 0.005 <= y <= 0.15 and have[t] >= 240 and tv.get(t, 0) > cut[u[t]]:
            out.append(dict(yahoo=t, region=u[t], y=float(y), price=float(p.iloc[-1])))
    c = pd.DataFrame(out, columns=['yahoo', 'region', 'y', 'price'])
    return c.sort_values(['y', 'yahoo'], ascending=[False, True])


def targets(as_of, held=None, nav=NAV):
    """held: DataFrame of this pod's current stock positions (symbol=yahoo, qty, opened). Returns stock rows and hedge rows:
    columns yahoo, region, notional_usd (target, after the next close), reason."""
    as_of = pd.Timestamp(as_of); E = next_day(as_of)
    px, vol, dv, ix, exd = load(); u = pd.read_csv(UNIVERSE).set_index('yahoo').region
    held = held if held is not None else pd.DataFrame(columns=['symbol', 'qty', 'opened'])
    cap = nav / N_PODS * SCALE; size = POS_SHARE * cap; rows = []
    live = [s for s, q in zip(held.symbol, held.qty) if q]
    if live:                                                    # announced ex-dates for held stocks, read now (at most 20 calls)
        try:
            import refresh; exd = refresh.exdates(live).set_index('yahoo').exdate.pipe(pd.to_datetime)
        except Exception as e:
            print(f'pod 4: ex-date lookup failed ({type(e).__name__}); held stocks exit on day {MAX_HOLD}')
    for r in held.itertuples():
        if r.qty == 0: continue
        days_held = len(pd.bdate_range(r.opened, E)) - 1
        ex = exd.get(r.symbol)
        if pd.notna(ex) and pd.Timestamp(r.opened) < pd.Timestamp(ex) <= E: reason = f'exit: ex-date {pd.Timestamp(ex).date()}'; n = 0
        elif days_held >= MAX_HOLD: reason = f'exit after {MAX_HOLD} trading days'; n = 0
        else: reason = f'hold (expected ex-date {pd.Timestamp(ex).date() if pd.notna(ex) else "not announced"})'; n = size
        rows.append(dict(yahoo=r.symbol, region=u.get(r.symbol), notional_usd=n, reason=reason))
    room = MAX_POS - sum(1 for x in rows if x['notional_usd'] > 0)
    have = {x['yahoo'] for x in rows}
    for c in candidates(as_of, px, vol, dv, u).itertuples():
        if room <= 0: break
        if c.yahoo in have: continue
        rows.append(dict(yahoo=c.yahoo, region=c.region, notional_usd=size, reason=f'enter: expected yield {c.y:.2%}')); room -= 1
    t = pd.DataFrame(rows, columns=['yahoo', 'region', 'notional_usd', 'reason'])
    return t, hedge(t, px, ix)


def hedge(t, px, ix):
    """Short each region's index future against its beta-weighted long notional (252-day betas), whole contracts."""
    out = []; r = px.pct_change(fill_method=None).iloc[-253:]; ir = ix.pct_change(fill_method=None).reindex(r.index)
    for g, h in HEDGE.items():
        s = t[(t.region == g) & (t.notional_usd > 0)]
        if s.empty: out.append(dict(region=g, **h, contracts=0, beta_notional=0.0)); continue
        bn = 0.0
        for x in s.itertuples():
            a = pd.concat([r[x.yahoo], ir[IDX[g]]], axis=1).dropna()
            b = float(a.iloc[:, 0].cov(a.iloc[:, 1]) / a.iloc[:, 1].var()) if len(a) > 120 else 1.0
            bn += b * x.notional_usd
        level = float(ix[IDX[g]].dropna().iloc[-1]); fx = float(ix[h['fx']].dropna().iloc[-1]) if h['fx'] else 1.0
        out.append(dict(region=g, **h, contracts=-int(round(bn / (level * h['mult'] * fx))), beta_notional=bn))
    return pd.DataFrame(out)


IB = {'.SW': ('EBS', 'CHF'), '.BR': ('ENEXT.BE', 'EUR'), '.ST': ('SFB', 'SEK'), '.DE': ('IBIS', 'EUR'), '.L': ('LSE', 'GBP'),
      '.AS': ('AEB', 'EUR'), '.PA': ('SBF', 'EUR'), '.MI': ('BVME', 'EUR'), '.MC': ('BM', 'EUR'), '.HE': ('HEX', 'EUR'),
      '.CO': ('CPH', 'DKK'), '.OL': ('OSE', 'NOK'), '.VI': ('VSE', 'EUR'), '.IR': ('ISED', 'EUR'), '.LS': ('BVL', 'EUR'),
      '.WA': ('WSE', 'PLN'), '.AT': ('ATH', 'EUR'), '.HK': ('SEHK', 'HKD')}


HK_LOTS = pd.read_csv(os.path.join(DATA, 'hk_lots.csv')).set_index('yahoo').lot.to_dict() if os.path.exists(os.path.join(DATA, 'hk_lots.csv')) else {}


def ib_contract(y):
    """Yahoo ticker -> Interactive Brokers stock fields (as Pod 3, plus Hong Kong)."""
    if '.' not in y: return dict(ib_symbol=y.replace('-', ' '), primary_exchange='', currency='USD')
    suf = '.' + y.split('.')[-1]; root = y[: -len(suf)]; exch, ccy = IB.get(suf, ('SMART', 'USD'))
    if suf == '.HK': root = str(int(root))
    elif suf in ('.ST', '.CO', '.OL', '.HE'): root = root.replace('-', ' ')
    return dict(ib_symbol=root, primary_exchange=exch, currency=ccy)


def yahoo_for(ib_symbol, currency):
    u = pd.read_csv(UNIVERSE).yahoo
    return next((y for y in u if ib_contract(y)['ib_symbol'] == ib_symbol and (not currency or ib_contract(y)['currency'] == currency)), None)


def book_rows(as_of, positions, nav=NAV):
    """Rows for book.py: stocks in whole shares at the last close and FX, then the hedge futures."""
    import yfinance as yf
    held = positions[positions.pod == 4] if len(positions) else positions
    hs = held[held.symbol.isin(['DJ600', 'MES', 'MHI']) == False] if len(held) else held
    hd = pd.DataFrame(dict(symbol=[yahoo_for(s, c) for s, c in zip(hs.symbol, hs.get('currency', ['']*len(hs)))] if len(hs) else [],
                           qty=list(hs.qty) if len(hs) else [], opened=list(hs.opened) if len(hs) else []))
    t, h = targets(as_of, hd.dropna(subset=['symbol']), nav)
    px = load()[0].ffill().iloc[-1]; rows = []
    ccys = sorted({ib_contract(y)['currency'] for y in t.yahoo} - {'USD'})
    fx = yf.download([f'{c}USD=X' for c in ccys], period='10d', progress=False, auto_adjust=True)['Close'].ffill().iloc[-1] if ccys else pd.Series(dtype=float)
    if len(ccys) == 1: fx = pd.Series({f'{ccys[0]}USD=X': float(fx.iloc[0] if hasattr(fx, 'iloc') else fx)})
    for r in t.itertuples():
        c = ib_contract(r.yahoo); p = float(px[r.yahoo]); f = 1.0 if c['currency'] == 'USD' else float(fx[f"{c['currency']}USD=X"])
        if r.yahoo.endswith('.L'): p /= 100                                   # Yahoo quotes London in pence
        q = int(r.notional_usd / (p * f)) if r.notional_usd else 0
        if c['currency'] == 'HKD':                                          # Hong Kong trades in board lots
            lot = int(HK_LOTS.get(r.yahoo, 500)); q = q // lot * lot
        rows.append(dict(pod=4, symbol=c['ib_symbol'], sec_type='STK', exchange='SMART', primary_exchange=c['primary_exchange'],
                         currency=c['currency'], multiplier=1, target_qty=q, ref_price=p, notional_usd=q * p * f, reason=f'{r.yahoo}: {r.reason}'))
    for r in h.itertuples():
        if r.contracts == 0 and not (len(held) and (held.symbol == r.symbol).any()): continue
        rows.append(dict(pod=4, symbol=r.symbol, sec_type='FUT', exchange=r.exchange, primary_exchange=r.exchange, currency=r.currency,
                         multiplier=r.mult, target_qty=r.contracts, ref_price=None, notional_usd=None,
                         reason=f'hedge {r.region}: beta-weighted long {r.beta_notional:,.0f} USD'))
    return rows


def status():
    return dict(pod=4, stage='incubation (passed development, diversification and hold-out, 9 October 2026)', scale=SCALE)


def checks(as_of):
    f = os.path.join(DATA, 'prices.csv'); out = []
    if not os.path.exists(f): return ['pod 4: no data; run pods/pod4/refresh.py']
    last = pd.read_csv(f, index_col=0, usecols=[0], parse_dates=True).index[-1]
    if last < pd.Timestamp(as_of) - pd.offsets.BDay(1): out.append(f'pod 4: prices end {last.date()}, before {pd.Timestamp(as_of).date()}; run refresh.py')
    if not HK_LOTS: print('pod 4: no hk_lots.csv; Hong Kong orders use lots of 500 shares')
    return out


if __name__ == '__main__':
    import sys
    t, h = targets(sys.argv[1] if len(sys.argv) > 1 else pd.Timestamp.today().date())
    pd.set_option('display.width', 200); print(t.to_string(index=False)); print(h[['region', 'symbol', 'contracts', 'beta_notional']].to_string(index=False))
