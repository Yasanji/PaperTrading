"""Signal test 1 (fixed 1 Oct 2026): industry-neutral momentum, STOXX 600, development period 2013-2022 only."""
import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
D = pickle.load(open('msb/long_data.pkl', 'rb')); meta = D['meta'].set_index('yf')
px, cl, vol, FX = D['px'], D['close'], D['volume'], D['fx']; names = list(meta.index); days = px.index
ccy = meta.currency.replace({'GBp': 'GBP'}); scale = meta.currency.map(lambda c: 0.01 if c == 'GBp' else 1.0)
fxlvl = pd.DataFrame({n: (FX[ccy[n]].reindex(days.union(FX[ccy[n]].index)).ffill().reindex(days) if ccy[n] != 'EUR' else pd.Series(1.0, index=days)) for n in names})
avail = px.ffill().notna()
r_eur = ((1 + px.ffill().pct_change(fill_method=None)) * (1 + fxlvl.pct_change(fill_method=None).fillna(0)) - 1).clip(-0.5, 0.5).where(avail)
tri = (1 + r_eur.fillna(0)).cumprod().where(avail)                        # EUR total-return index
tv = (cl.ffill() * vol * scale.values * fxlvl).rolling(63, min_periods=40).median()   # EUR traded value
mkt = r_eur.mean(axis=1)                                                   # equal-weight universe return
beta = r_eur.rolling(252, min_periods=200).cov(mkt).div(mkt.rolling(252, min_periods=200).var(), axis=0)
IND = meta.industry
LIQ, TOP, COST, BORROW, HEDGE_COST, TV, WIN = 5e6, 0.2, 9e-4, 0.0045, 1e-4, 0.05, 126
fridays = [d for d in days if d.weekday() == 4 and pd.Timestamp('2012-06-01') <= d <= pd.Timestamp('2022-12-31')]
W = {}
for d in fridays:
    i = days.get_loc(d)
    if i < 252: continue
    mom = tri.iloc[i - 21] / tri.iloc[i - 252] - 1
    ok = mom.notna() & (tv.iloc[i] >= LIQ) & avail.iloc[i]
    w = pd.Series(0.0, index=names); groups = [g for g in IND[ok[ok].index].groupby(IND[ok[ok].index]).groups.values() if len(g) >= 5]
    if not groups: continue
    for g in groups:
        s = mom[list(g)].sort_values(); k = max(1, int(round(TOP * len(s))))
        w[s.index[-k:]] += 0.5 / len(groups) / k; w[s.index[:k]] -= 0.5 / len(groups) / k
    exec_day = days[i + 1] if i + 1 < len(days) else None
    if exec_day is not None: W[exec_day] = w
Wd = pd.DataFrame(W).T.reindex(days).ffill().fillna(0.0)
Wd = Wd[Wd.index >= min(W)]
B = beta.reindex(Wd.index).fillna(1.0)
hedge = -(Wd * B).sum(axis=1)                                              # market position to zero beta
R = r_eur.reindex(Wd.index).fillna(0.0); M = mkt.reindex(Wd.index).fillna(0.0)
def pnl(scale_series):
    w = Wd.mul(scale_series, axis=0); h = hedge * scale_series
    gross = (w.shift(1) * R).sum(axis=1) + h.shift(1) * M
    turn = w.diff().abs().sum(axis=1); hturn = h.diff().abs()
    cost = turn * COST + hturn * HEDGE_COST + (-w.clip(upper=0)).sum(axis=1).shift(1) * BORROW / 252
    return (gross - cost).fillna(0), gross.fillna(0), turn.fillna(0)
un, un_g, un_t = pnl(pd.Series(1.0, index=Wd.index))
# vol scaling: decided at each signal Friday from the unscaled sleeve's previous six months, applied from execution day
sv = un.rolling(WIN).std() * np.sqrt(252)
sc = pd.Series(np.nan, index=Wd.index)
for e in W:
    if e in sc.index:
        prior = days[days.get_loc(e) - 1]
        if prior in sv.index and np.isfinite(sv.loc[prior]) and sv.loc[prior] > 0: sc.loc[e] = TV / sv.loc[prior]
sc = sc.ffill()
vs, vs_g, vs_t = pnl(sc.fillna(0))
def stats(x, g, t, a='2013-01-01', b='2022-12-31'):
    x, g, t = x[a:b], g[a:b], t[a:b]; yrs = len(x) / 252
    cum = (1 + x).cumprod(); dd = (cum / cum.cummax() - 1).min()
    return dict(ret_pct=x.mean() * 252 * 100, vol_pct=x.std() * np.sqrt(252) * 100, sharpe=x.mean() / x.std() * np.sqrt(252),
                t=x.mean() / x.std() * np.sqrt(len(x)), max_dd_pct=dd * 100, worst_month_pct=x.resample('ME').sum().min() * 100,
                turnover_x_yr=t.sum() / yrs, breakeven_bps=g.sum() / t.sum() * 1e4 if t.sum() > 0 else np.nan)
out = {}
for lab, (x, g, t) in [('Vol-scaled (main)', (vs, vs_g, vs_t)), ('Unscaled', (un, un_g, un_t))]:
    for per, a, b in [('2013-2022', '2013-01-01', '2022-12-31'), ('2013-2017', '2013-01-01', '2017-12-31'), ('2018-2022', '2018-01-01', '2022-12-31')]:
        out[f'{lab} | {per}'] = stats(x, g, t, a, b)
T = pd.DataFrame(out).T; pd.set_option('display.width', 220); print(T.round(2).to_string())
m, h1, h2 = out['Vol-scaled (main) | 2013-2022'], out['Vol-scaled (main) | 2013-2017'], out['Vol-scaled (main) | 2018-2022']
print('\nscale factor: median', round(sc['2013':'2022'].median(), 2), 'max', round(sc['2013':'2022'].max(), 2), '| avg names per side', round(((Wd > 0).sum(axis=1)['2013':'2022']).mean()), '| industries', len(groups))
print('PRE-REGISTERED PASS MARK (positive, t > 2, positive both halves):', 'PASS' if (m['ret_pct'] > 0 and m['t'] > 2 and h1['ret_pct'] > 0 and h2['ret_pct'] > 0) else 'FAIL')
pickle.dump(dict(T=T, vs=vs, un=un, sc=sc, Wd=Wd), open('msb/sens_mom_cost3.pkl', 'wb'))
