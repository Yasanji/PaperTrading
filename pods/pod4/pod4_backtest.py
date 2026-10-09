"""Pod 4 backtest, rules of POD4_PREREGISTRATION.md, on the Sleeve B data (carry/sleeveB/data, manifest in
carry/sleeveB/MANIFEST.md). Usage: python pod4_backtest.py dev | holdout
Returns are daily, on the pod's allocated capital: each open position is 10% of capital, at most 20 positions,
cash earns nothing. Prices: Close (split-adjusted, not dividend-adjusted); dividends credited net of 15% on the ex-date."""
import sys, os, numpy as np, pandas as pd, statsmodels.api as sm, yfinance as yf
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'carry', 'sleeveB', 'data')
COST = {'EU': 3e-4, 'US': 2e-4, 'HK': 5e-4}; HCOST = 1e-4; IDX = {'EU': '^STOXX', 'US': '^GSPC', 'HK': '^HSI'}
u = pd.read_csv(f'{D}/universe.csv').set_index('yahoo')
px = pd.read_csv(f'{D}/prices_close.csv', index_col=0, parse_dates=True)
vol = pd.read_csv(f'{D}/prices_volume.csv', index_col=0, parse_dates=True).reindex_like(px)
dv = pd.read_csv(f'{D}/dividends.csv', parse_dates=['date'])
ixf = f'{D}/indices.csv'
if not os.path.exists(ixf):
    yf.download(list(IDX.values()), start='2004-01-01', end='2026-10-01', progress=False, auto_adjust=True)['Close'].to_csv(ixf)
ix = pd.read_csv(ixf, index_col=0, parse_dates=True)

def regular(g):
    """Sleeve B s.5.1: special if more than twice the median of the previous four dividends."""
    a = g.dividend.values; keep = [True]
    for k in range(1, len(a)): keep.append(a[k] <= 2 * np.median(a[max(0, k - 4):k]))
    return g[np.array(keep)]
R = pd.concat([regular(g) for _, g in dv.sort_values('date').groupby('yahoo')])
ALL = dv.groupby('yahoo')

# liquidity at each month-end: median traded value over 63 days above the region's 20th percentile (Sleeve B s.4.4)
tv = (px * vol).rolling(63, min_periods=40).median(); me = px.index.to_series().groupby(px.index.to_period('M')).max()
liq = {}
for d in me:
    row = tv.loc[d]
    for reg in ('EU', 'US', 'HK'):
        s = row[[c for c in row.index if u.region.get(c) == reg]].dropna()
        liq[(d, reg)] = set(s[s > s.quantile(0.2)].index)
have = px.notna().rolling(252).sum()
r = px.pct_change(fill_method=None); ir = ix.reindex(px.index.union(ix.index)).ffill().reindex(px.index).pct_change(fill_method=None)

cands = []                                             # (entry_day, yahoo, expected yield)
days = px.index
for t, g in R.groupby('yahoo'):
    if t not in px or t not in u.index: continue
    p = px[t].dropna(); first = ALL.get_group(t).date.min()
    for e in g.date:
        exp = e + pd.DateOffset(years=1)
        k = days.searchsorted(exp) - 15
        if k < 252 or k >= len(days): continue
        ent = days[k]
        prev = g[g.date <= ent]
        if prev.empty or first > ent - pd.DateOffset(years=2) or not np.isfinite(px.at[ent, t]): continue
        y = prev.dividend.iloc[-1] / px.at[ent, t]
        if not (0.005 <= y <= 0.15) or have.at[ent, t] < 240: continue
        m = me[me < ent]
        if m.empty or t not in liq.get((m.iloc[-1], u.region[t]), set()): continue
        cands.append((ent, t, y))
C = pd.DataFrame(cands, columns=['entry', 'yahoo', 'y']).drop_duplicates(['entry', 'yahoo']).sort_values(['entry', 'y', 'yahoo'], ascending=[True, False, True])

pnl = pd.Series(0.0, index=days); open_ = {}; trades = []
byday = dict(tuple(C.groupby('entry')))
for i, d in enumerate(days):
    for t, pos in list(open_.items()):                 # accrue the day's return, close on exit
        reg = u.region[t]; rs = r.at[d, t] if np.isfinite(r.at[d, t]) else 0.0
        dvd = ALL.get_group(t); ex = dvd[dvd.date == d].dividend.sum()
        day = rs + (0.85 * ex / px[t].loc[:d].dropna().iloc[-2] if ex else 0) - pos['beta'] * (ir.at[d, IDX[reg]] if np.isfinite(ir.at[d, IDX[reg]]) else 0)
        pnl[d] += 0.10 * day; pos['ret'] += day; pos['n'] += 1
        if ex or pos['n'] >= 30:
            c = COST[reg] + HCOST * abs(pos['beta']); pnl[d] -= 0.10 * c; pos['ret'] -= c
            trades.append(dict(yahoo=t, entry=pos['entry'], exit=d, ret=pos['ret'], ex=bool(ex))); del open_[t]
    if d in byday:
        for row in byday[d].itertuples():
            if len(open_) >= 20: break
            if row.yahoo in open_: continue
            reg = u.region[row.yahoo]; w = slice(max(0, i - 252), i + 1)
            a = pd.concat([r[row.yahoo].iloc[w], ir[IDX[reg]].iloc[w]], axis=1).dropna()
            beta = float(a.iloc[:, 0].cov(a.iloc[:, 1]) / a.iloc[:, 1].var()) if len(a) > 120 else 1.0
            c = COST[reg] + HCOST * abs(beta); pnl[d] -= 0.10 * c
            open_[row.yahoo] = dict(entry=d, beta=beta, ret=-c, n=0)

def stats(x):
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type='HAC', cov_kwds={'maxlags': 10})
    return dict(ann_return=x.mean() * 252, ann_vol=x.std() * np.sqrt(252), sharpe=x.mean() / x.std() * np.sqrt(252), t_nw=m.tvalues[0])
P = {'dev': [('2006-01-01', '2015-12-31'), ('2006-01-01', '2010-12-31'), ('2011-01-01', '2015-12-31')],
     'holdout': [('2016-01-01', '2026-09-30'), ('2016-01-01', '2020-12-31'), ('2021-01-01', '2026-09-30')]}[sys.argv[1]]
print(pd.DataFrame({f'{a[:4]}-{b[:4]}': stats(pnl[a:b]) for a, b in P}).T.round(4))
T = pd.DataFrame(trades); T = T[(T.entry >= P[0][0]) & (T.entry <= P[0][1])]
print(f'trades {len(T)}, mean {T.ret.mean():.4f}, hit {(T.ret > 0).mean():.2f}, closed at ex-date {T.ex.mean():.2f}')
pnl.to_csv(f'pod4_daily_{sys.argv[1]}.csv'); T.to_csv(f'pod4_trades_{sys.argv[1]}.csv', index=False)
