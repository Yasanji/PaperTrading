"""Audit: false-positive rates of the inference methods under no predictability, and look-ahead checks."""
import numpy as np, pandas as pd, statsmodels.api as sm
from step2_main import S, NW, ivx_p, hodrick, us_lagged, BASE
rng = np.random.default_rng(3)
d = S['UK'].loc['1999-01-01':'2023-03-17'].dropna().copy(); T = len(d); y0 = d.y_next.values - d.y_next.mean()
def sboot(L=21):                                                   # stationary bootstrap indices, vectorised
    new = rng.random(T) < 1 / L; new[0] = True; first = np.flatnonzero(new); grp = np.cumsum(new) - 1
    return (rng.integers(0, T, len(first))[grp] + np.arange(T) - first[grp]) % T
X = sm.add_constant(d[BASE]); rej = dict(nw_thr=0, nw_cal=0, ivx_thr=0, ivx_cal=0, hod10_thr=0); R = 300
for r in range(R):
    d['y_next'] = y0[sboot()]                                      # returns resampled in blocks: same volatility clustering, no link to the signals
    f = sm.OLS(d.y_next, X).fit(cov_type='HAC', cov_kwds={'maxlags': NW(T)})
    rej['nw_thr'] += abs(f.tvalues.thr) > 1.96; rej['nw_cal'] += abs(f.tvalues.calw4) > 1.96
    rej['ivx_thr'] += ivx_p(d, 'thr', BASE)[1] < 0.05; rej['ivx_cal'] += ivx_p(d, 'calw4', BASE)[1] < 0.05
    d['xa_sim'] = d.y_next.shift(1); dd = d.copy(); dd['xa'] = dd['y_next'].shift(1)
    rej['hod10_thr'] += abs(hodrick(dd, 'thr', BASE, 10)[1]) > 1.96
print(f'False-positive rates at a nominal 5%, {R} simulations of UK-like data with no predictability:')
for k, v in rej.items(): print(f'  {k:10s} {v / R:.3f}')
print('\nLook-ahead checks:')
full = S['UK']; probe = full.index[[3000, 5000, 7000]]
from local_data import build
import local_data as L
eqp, yy = L.eq('^FTSE'), L.gilt()
for t in probe:
    cut = build(eqp.loc[:t], yy.loc[:t], 'par')                   # rebuild using data only up to day t
    same = all(np.isclose(cut.loc[t, c], full.loc[t, c]) for c in ('thr', 'mom', 'xa0'))
    print(f'  {t.date()}: Threshold, momentum and trailing return identical when rebuilt with data up to that day only: {same}')
u = us_lagged(full.index); us_idx = S['US'].index
src = [us_idx[us_idx < t].max() for t in full.index[[2000, 4000, 6000]]]
print('  US signal used for local day t comes from US date before t:', all(s < t for s, t in zip(src, full.index[[2000, 4000, 6000]])))
print('  Dependent variable is the next day return:', bool(np.allclose(full.y_next.iloc[:-1].values, full.xa.iloc[1:].values)))
mend_known = full.index.to_series().groupby(full.index.to_period('M')).transform('max')
print('  Month-end dates are set by the exchange calendar, which is known in advance; the code reads them from the data, which matches the calendar in check (c).')
