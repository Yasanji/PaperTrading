"""Signal test 7 (fixed 1 Oct 2026): 12-month trend on 15 futures, 2013-2022, sleeve scaled to 5% vol."""
import pickle, numpy as np, pandas as pd
D = pickle.load(open('tsmom_data.pkl', 'rb')); px = D['px'].ffill(); days = px.index
r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252)
fr = [d for d in days if d.weekday() == 4 and pd.Timestamp('2011-01-01') <= d <= pd.Timestamp('2022-12-31')]
W = {}
for d in fr:
    i = days.get_loc(d)
    if i + 1 >= len(days) or i < 252: continue
    sig = np.sign(px.iloc[i] / px.iloc[i - 252] - 1); w = (0.10 / vol.iloc[i] * sig / px.shape[1]).fillna(0)
    W[days[i + 1]] = w
Wd = pd.DataFrame(W).T.reindex(days).ffill().fillna(0)[min(W):'2022-12-31']
R = r.reindex(Wd.index).fillna(0)
x = (Wd.shift(1) * R).sum(axis=1) - Wd.diff().abs().sum(axis=1) * 3e-4; g = (Wd.shift(1) * R).sum(axis=1); tv = Wd.diff().abs().sum(axis=1)
sv = x.rolling(126).std() * np.sqrt(252); sc = pd.Series(np.nan, index=x.index)
for d in [d for d in x.index if d.weekday() == 4]:
    i = x.index.get_loc(d)
    if i + 1 < len(x) and np.isfinite(sv.iloc[i]) and sv.iloc[i] > 0: sc.iloc[i + 1] = 0.05 / sv.iloc[i]
sc = sc.ffill(); xs = (x * sc.shift(1)).dropna()
def st(s, a, b):
    s = s[a:b]; cum = (1 + s).cumprod()
    return dict(ret_pct=s.mean() * 252 * 100, vol_pct=s.std() * np.sqrt(252) * 100, sharpe=s.mean() / s.std() * np.sqrt(252),
                t=s.mean() / s.std() * np.sqrt(len(s)), max_dd_pct=(cum / cum.cummax() - 1).min() * 100)
out = {f'{lab} | {p}': st(s, a, b) for lab, s in [('Vol-scaled (main)', xs), ('As traded', x)]
       for p, a, b in [('2013-2022', '2013-01-01', '2022-12-31'), ('2013-2017', '2013-01-01', '2017-12-31'), ('2018-2022', '2018-01-01', '2022-12-31')]}
T = pd.DataFrame(out).T; print(T.round(2).to_string())
print(f"breakeven {g['2013':].sum() / tv['2013':].sum() * 1e4:.1f}bp per trade | turnover {tv['2013':].sum() / 10:.1f}x a year")
m, h1, h2 = (out[f'Vol-scaled (main) | {p}'] for p in ('2013-2022', '2013-2017', '2018-2022'))
print('PRE-REGISTERED PASS MARK:', 'PASS' if (m['ret_pct'] > 0 and m['t'] > 2 and h1['ret_pct'] > 0 and h2['ret_pct'] > 0) else 'FAIL',
      '| combination rule:', 'IN' if (h1['ret_pct'] > 0 and h2['ret_pct'] > 0) else 'OUT')
pickle.dump(dict(T=T, xs=xs, x=x), open('msb/sens_trend_cost3.pkl', 'wb'))
