"""Signal test 4 (fixed 1 Oct 2026): frozen pairs rules on 2013-2022, data cut at 31 Dec 2022."""
import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import model_600_long as M
M.SLOTS, M.SIGMA, M.IDLE_TO_EQUITY, M.BACKSTOP = 10, 0.035, 0.0, 1.0
pa, ex = M.run()
x = pa.pair_net; g = pa.pair_gross; tv = pa.turnover
assert x.index[-1] <= pd.Timestamp('2022-12-31')
# 5% vol scaling, as in signal tests 1-3: decided each Friday from the previous six months, applied from the next day
sv = x.rolling(126).std() * np.sqrt(252); sc = pd.Series(np.nan, index=x.index)
fr = [d for d in x.index if d.weekday() == 4]
for d in fr:
    i = x.index.get_loc(d)
    if i + 1 < len(x) and np.isfinite(sv.iloc[i]) and sv.iloc[i] > 0: sc.iloc[i + 1] = 0.05 / sv.iloc[i]
sc = sc.ffill(); xs = (x * sc.shift(1)).dropna()
def st(s, a, b):
    s = s[a:b]; cum = (1 + s).cumprod(); return dict(ret_pct=s.mean() * 252 * 100, vol_pct=s.std() * np.sqrt(252) * 100,
        sharpe=s.mean() / s.std() * np.sqrt(252), t=s.mean() / s.std() * np.sqrt(len(s)), max_dd_pct=(cum / cum.cummax() - 1).min() * 100)
out = {}
for lab, s in [('Vol-scaled (main)', xs), ('As traded', x)]:
    for per, a, b in [('2013-2022', '2013-01-01', '2022-12-31'), ('2013-2017', '2013-01-01', '2017-12-31'), ('2018-2022', '2018-01-01', '2022-12-31')]:
        out[f'{lab} | {per}'] = st(s, a, b)
T = pd.DataFrame(out).T; print(T.round(2).to_string())
gg, tt = g['2013':'2022'].sum(), tv['2013':'2022'].sum()
print(f"\nturnover {tt / 10:.1f}x a year | breakeven {gg / tt * 1e4:.1f}bp per trade | funded pairs avg {ex['active']['2013':].mean():.1f} | picks {len(ex['log'])} | scale median {sc['2013':].median():.2f}")
m, h1, h2 = out['Vol-scaled (main) | 2013-2022'], out['Vol-scaled (main) | 2013-2017'], out['Vol-scaled (main) | 2018-2022']
print('PRE-REGISTERED PASS MARK:', 'PASS' if (m['ret_pct'] > 0 and m['t'] > 2 and h1['ret_pct'] > 0 and h2['ret_pct'] > 0) else 'FAIL',
      '| combination rule (positive both halves):', 'IN' if (h1['ret_pct'] > 0 and h2['ret_pct'] > 0) else 'OUT')
pickle.dump(dict(T=T, x=x, xs=xs, log=ex['log']), open('pairs_dev_results.pkl', 'wb'))
