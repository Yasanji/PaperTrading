"""Back-check on the August and May 2026 reviews: rebuild membership before each review, price at the review's
cut-off window, rank stocks by distance to their thresholds, and compare with MSCI's published changes."""
import sys, pandas as pd, numpy as np
sys.path.insert(0, '.'); import model
u = pd.read_csv('data/universe_2026-10-08.csv'); u['fund'] = u.segment
p = pd.read_pickle('data/prices.pkl').ffill(); now = p.iloc[-1]
REV = {  # MSCI public lists, Europe (Standard index)
  'Aug26': dict(win=('2026-07-17', '2026-07-31'), add=['DIPLOMA'],
                dele=['ROCKWOOL', 'BOLLORE', 'CTS EVENTIM', 'SCOUT24', 'CSG', 'SUNBELT', 'BALDER', 'LATOUR', 'OCTAVE', 'SAGAX']),
  'May26': dict(win=('2026-04-17', '2026-04-30'), add=['ABIVAX', 'VAR ENERGI', 'MILLICOM'],
                dele=['GRIFOLS', 'LEG IMMOBILIEN', 'RANDSTAD', 'AUTO TRADER', 'BARRATT', 'ENTAIN', 'JD SPORTS', 'WHITBREAD', 'HOLMEN'])}
def hit(n, keys): return any(k in str(n).upper() for k in keys)
gm_ref = p['URTH'].loc['2026-07-20']
mem = u.segment.copy()                              # membership after the latest review, walked backwards
out = {}
for r in ['Aug26', 'May26']:
    R = REV[r]; a = u['name'].map(lambda n: hit(n, R['add'])); d = u['name'].map(lambda n: hit(n, R['dele']))
    mem = mem.where(~a, 'SMALL').where(~d, 'STANDARD')
    pre = u.copy(); pre['segment'] = mem
    win = p.loc[R['win'][0]:R['win'][1]]; pre['mcap'] = pre.mcap * pre.symbol.map(win.mean() / now)
    fx = {c: win[c + 'USD=X'].mean() for c in ['EUR', 'GBP', 'CHF', 'SEK', 'DKK', 'NOK']}; fx['USD'] = 1.0
    gmsr = 16.28 * win['URTH'].mean() / gm_ref
    c = model.companies(pre, fx); _, cuts = model.predict(c, gmsr)
    x = c.dropna(subset=['full_usd']).merge(cuts[['market', 'cutoff']], on='market')
    x['ratio'] = np.where(x.segment == 'STANDARD', x.full_usd / (2 / 3 * x.cutoff), x.full_usd / (1.5 * x.cutoff))
    act = set(u.loc[a | d, 'name']); x['actual'] = x['name'].isin(act)
    dl = x[x.segment == 'STANDARD'].sort_values('ratio').reset_index(drop=True)
    ad = x[x.segment == 'SMALL'].sort_values('ratio', ascending=False).reset_index(drop=True)
    print(f'\n== {r}: GMSR {gmsr:.2f}bn; actual changes found in data: {len(act)} of {len(R["add"]) + len(R["dele"])}')
    print('deletion candidates'); print(dl.head(15)[['market', 'name', 'full_usd', 'ratio', 'actual']].round(2).to_string())
    print('addition candidates'); print(ad.head(8)[['market', 'name', 'full_usd', 'ratio', 'actual']].round(2).to_string())
    print('actual, not in data or unranked:', sorted(set(R['add'] + R['dele']) - {k for k in R['add'] + R['dele'] if any(k in n.upper() for n in act)}))
    out[r] = (dl, ad)
pd.to_pickle(out, 'data/backtest.pkl')
