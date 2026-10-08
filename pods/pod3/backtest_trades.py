"""Pod 3 trade back-check on past reviews, using the predictions the models made for them (in-sample: the models'
thresholds were set on these reviews). Trade rules as POD3_PREREGISTRATION.md s.4: entry at the close 15 trading
days before the effective date, exit at the effective-date close, wrong predictions closed at the close after the
announcement, beta hedge with the STOXX Europe 600 (as a return, not whole contracts), 3bp a trade on shares,
1bp on the hedge, 0.45% a year borrow on shorts.
Usage: python backtest_trades.py   (reads bt_pred_*.csv from DATA)"""
import os, sys, numpy as np, pandas as pd, yfinance as yf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import pod
DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
REV = {  # review: (prediction file, announcement date, effective date)
    'MSCI May 2026': ('bt_pred_May26.csv', '2026-05-12', '2026-05-29'),
    'MSCI Aug 2026': ('bt_pred_Aug26.csv', '2026-08-12', '2026-08-31'),
    'STOXX Sep 2026': ('bt_pred_Sep26.csv', '2026-09-01', '2026-09-18')}
COST, HCOST, BORROW = 0.0003, 0.0001, 0.0045

rows = []
for rev, (f, ann, eff) in REV.items():
    p = pd.read_csv(os.path.join(DATA, f))
    for i in p.index[p.symbol.isna()]:
        q = yf.Search(str(p.at[i, 'isin']) if 'isin' in p and pd.notna(p.at[i, 'isin']) else p.at[i, 'name'], max_results=1).quotes
        p.at[i, 'symbol'] = q[0]['symbol'] if q else None
    p = p.dropna(subset=['symbol'])
    ent = pod.entry_date(eff); eff = pd.Timestamp(eff); ann = pd.Timestamp(ann)
    px = yf.download(list(p.symbol) + [pod.HEDGE['yahoo']], start=ent - pd.Timedelta(days=400), end=eff + pd.Timedelta(days=5),
                     progress=False, auto_adjust=True)['Close'].ffill()
    r = px.pct_change(); h = pod.HEDGE['yahoo']
    for _, x in p.iterrows():
        s = x.symbol
        if s not in px or px[s].loc[:ent].dropna().empty: continue
        side = 1 if x.call == 'ADD' else -1
        out = eff if x.actual else px.index[px.index > ann][0]                 # wrong calls closed after the announcement
        hist = r.loc[:ent].iloc[-252:][[s, h]].dropna()
        beta = float(np.clip(hist[s].cov(hist[h]) / hist[h].var(), 0, 3)) if len(hist) >= 120 else 1.0   # short history: beta 1
        ps, pe = px[s].asof(ent), px[s].asof(out); hs, he = px[h].asof(ent), px[h].asof(out)
        days = (out - ent).days
        gross = side * (pe / ps - 1) - side * beta * (he / hs - 1)
        net = gross - 2 * COST - 2 * HCOST * abs(beta) - (BORROW * days / 365 if side < 0 else 0)
        rows.append(dict(review=rev, call=x.call, name=x['name'], correct=bool(x.actual), entry=ent.date(), exit=out.date(),
                         beta=round(beta, 2), stock=round(side * (pe / ps - 1), 4), hedged_net=round(net, 4)))
t = pd.DataFrame(rows); t.to_csv(os.path.join(DATA, 'backtest_trades.csv'), index=False)
pd.set_option("display.width", 200)

g = t.groupby(['review', 'call']).hedged_net.agg(['count', 'mean']).round(4); print(g)
print('\nby review: n, mean, hit rate'); print(t.groupby('review').hedged_net.agg(['count', 'mean', lambda x: (x > 0).mean()]).round(3))
print('\nall trades: n', len(t), 'mean net %.2f%%' % (100 * t.hedged_net.mean()), 'median %.2f%%' % (100 * t.hedged_net.median()),
      'hit rate %.0f%%' % (100 * (t.hedged_net > 0).mean()))
print('correct calls: mean %.2f%%; wrong calls: mean %.2f%%' % (100 * t[t.correct].hedged_net.mean(), 100 * t[~t.correct].hedged_net.mean()))
size = pod.POS_SHARE * pod.allocated_capital() * pod.FORWARD_SCALE
print(f'P&L at forward-test size (${size:,.0f} a position): ${(t.hedged_net * size).sum():,.0f} over {len(t)} trades')
