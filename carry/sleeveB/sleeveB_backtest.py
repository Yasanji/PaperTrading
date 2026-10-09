"""Sleeve B backtest, rules of PREREGISTRATION.md s.4 to s.7. Usage: python sleeveB_backtest.py dev | holdout
Implementation choices (recorded in DEV_RESULTS.md): weights are held constant between rebalances (daily rebalanced
to target), a stock with no price that day contributes zero, and month-ends are the last date in the price table."""
import sys, numpy as np, pandas as pd, statsmodels.api as sm
D = 'data'; COST = {'EU': 3e-4, 'US': 2e-4, 'HK': 5e-4}; BORROW = {'EU': .0045, 'US': .0045, 'HK': .01}; HC = 1e-4
u = pd.read_csv(f'{D}/universe.csv').set_index('yahoo'); sec = pd.read_csv(f'{D}/sectors.csv').set_index('yahoo').sector
cl = pd.read_csv(f'{D}/prices_close.csv', index_col=0, parse_dates=True)
ac = pd.read_csv(f'{D}/prices_adj_close.csv', index_col=0, parse_dates=True).reindex_like(cl)
vo = pd.read_csv(f'{D}/prices_volume.csv', index_col=0, parse_dates=True).reindex_like(cl)
dv = pd.read_csv(f'{D}/dividends.csv', parse_dates=['date']).sort_values('date')
def regular(g):
    a = g.dividend.values; keep = [True]
    for k in range(1, len(a)): keep.append(a[k] <= 2 * np.median(a[max(0, k - 4):k]))
    return g[np.array(keep)]
reg_dv = pd.concat([regular(g) for _, g in dv.groupby('yahoo')]); first = dv.groupby('yahoo').date.min()
ret = ac.pct_change(fill_method=None)
have = cl.notna().rolling(252).sum(); tv = (cl * vo).rolling(63, min_periods=40).median()
days = cl.index; me = days.to_series().groupby(days.to_period('M')).max()
REG = {g: [t for t in cl.columns if u.region.get(t) == g] for g in ('EU', 'US', 'HK')}

def weights(m):
    """Target weights per region at month-end m (long +1, short -1), and the region's eligible list."""
    out = {}
    clm = cl.loc[:m].ffill(limit=5).iloc[-1]
    ttm = reg_dv[(reg_dv.date > m - pd.Timedelta(days=365)) & (reg_dv.date <= m)].groupby('yahoo').dividend.sum()
    for g, names in REG.items():
        y = (ttm.reindex(names) / clm.reindex(names)).dropna()
        ok = [t for t in y.index if have.at[m, t] >= 240 and first.get(t, m) <= m - pd.DateOffset(months=24) and 0.001 < y[t] <= 0.15]
        lv = tv.loc[m, ok].dropna(); ok = list(lv[lv > tv.loc[m, names].dropna().quantile(0.2)].index)
        L, S = [], []; nsec = 0
        for s, grp in pd.Series(sec.reindex(ok).values, index=ok).dropna().groupby(lambda x: sec[x]):
            if len(grp) < 5: continue
            nsec += 1; k = max(1, len(grp) // 5)
            o = sorted(grp.index, key=lambda t: (-y[t], t)); L += o[:k]; S += o[-k:]
        if nsec >= 3:
            w = pd.Series(0.0, index=names); w[L] += 1 / len(L); w[S] -= 1 / len(S); out[g] = (w, ok)
    return out

reg_ret = {g: pd.Series(0.0, index=days) for g in REG}; cost = {g: pd.Series(0.0, index=days) for g in REG}
prev = {g: None for g in REG}
for j, m in enumerate(me[me >= '2005-01-01']):
    i0 = days.get_loc(m) + 1
    if i0 >= len(days): break
    nxt = me[me > m]; i1 = days.get_loc(nxt.iloc[0]) + 1 if len(nxt) else len(days)
    W = weights(m)
    for g in REG:
        if g not in W:
            if prev[g] is not None: cost[g].iloc[i0] += prev[g].abs().sum() * COST[g]
            prev[g] = None; continue
        w, elig = W[g]
        hist = ret[REG[g]].iloc[max(0, i0 - 252):i0].fillna(0); ls = hist @ w; ew = ret[elig].iloc[max(0, i0 - 252):i0].mean(axis=1)
        beta = ls.cov(ew) / ew.var() if ew.var() > 0 else 0.0
        seg = ret[REG[g]].iloc[i0:i1].fillna(0)
        reg_ret[g].iloc[i0:i1] = (seg @ w) - beta * ret[elig].iloc[i0:i1].mean(axis=1).fillna(0) \
            - (w[w < 0].abs().sum() * BORROW[g] / 252)
        tw = (w - (prev[g] if prev[g] is not None else 0)).abs().sum()
        cost[g].iloc[i0] += tw * COST[g] + abs(beta) * HC * 2
        prev[g] = w
R = pd.DataFrame({g: reg_ret[g] - cost[g] for g in REG})
# equal risk across traded regions (126-day vol), then scale to 5% a year, monthly; gross cap ignored at this stage
vol = R.rolling(126).std().shift(1); comb = pd.Series(0.0, index=days); scale = pd.Series(np.nan, index=days)
for m in me:
    i = days.get_loc(m) + 1
    if i >= len(days): break
    act = [g for g in REG if R[g].iloc[max(0, i - 21):i].abs().sum() > 0]
    if not act: continue
    v = vol.iloc[i][act]; wr = (1 / v) / (1 / v).sum() if v.notna().all() and (v > 0).all() else pd.Series(1 / len(act), index=act)
    comb_m = (R[act].iloc[i:] * wr).sum(axis=1)
    comb.iloc[i:] = comb_m
    sv = comb.iloc[max(0, i - 126):i].std() * np.sqrt(252)
    scale.iloc[i] = 0.05 / sv if sv > 0 and i > 126 else np.nan
x = (comb * scale.ffill()).dropna()
def stats(s):
    m = sm.OLS(s.values, np.ones(len(s))).fit(cov_type='HAC', cov_kwds={'maxlags': 10})
    return dict(ann_return=s.mean() * 252, ann_vol=s.std() * np.sqrt(252), sharpe=s.mean() / s.std() * np.sqrt(252), t_nw=m.tvalues[0])
P = {'dev': [('2006-01-01', '2015-12-31'), ('2006-01-01', '2010-12-31'), ('2011-01-01', '2015-12-31')],
     'holdout': [('2016-01-01', '2026-09-30'), ('2016-01-01', '2020-12-31'), ('2021-01-01', '2026-09-30')]}[sys.argv[1]]
print(pd.DataFrame({f'{a[:4]}-{b[:4]}': stats(x[a:b]) for a, b in P}).T.round(4))
print('regions, unscaled Sharpe:', {g: round(R[g][P[0][0]:P[0][1]].mean() / R[g][P[0][0]:P[0][1]].std() * np.sqrt(252), 2) for g in REG})
x.to_csv(f'sleeveB_daily_{sys.argv[1]}.csv'); R.to_csv(f'sleeveB_regions_{sys.argv[1]}.csv')
