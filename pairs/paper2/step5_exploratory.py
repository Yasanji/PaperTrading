"""Paper 2: exploratory checks of time variation (not pre-registered), on the primary data only."""
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from step2_main import S, fit, NW, us_lagged, BASE
PER = [('1999-2008', '1999-01-01', '2008-12-31'), ('2009-2016', '2009-01-01', '2016-12-31'), ('2017-Mar 2023', '2017-01-01', '2023-03-17'), ('hold-out', '2023-03-20', '2026-09-30')]
rows = []
for mkt in ('DE', 'UK'):
    d = S[mkt].copy().join(us_lagged(S[mkt].index)).dropna()
    for name, a, b in PER:
        x = d.loc[a:b]
        for lab, cols in (('local', BASE), ('with US', BASE + ['us_thr', 'us_calw4'])):
            f = fit(x, cols); rows.append(dict(market=mkt, period=name, model=lab, calw4=round(f.params.calw4, 3), t=round(f.tvalues.calw4, 2), N=int(f.nobs)))
    # equality of the month-end coefficient across the four periods: interactions with period dummies, Wald test with Newey-West errors
    x = d.loc['1999-01-01':'2026-09-30'].copy(); x['per'] = 0
    for i, (_, a, b) in enumerate(PER): x.loc[a:b, 'per'] = i
    cols = [c for c in BASE if c != 'calw4']
    for i in range(4): x[f'cw{i}'] = x.calw4 * (x.per == i)
    f = sm.OLS(x.y_next, sm.add_constant(x[cols + [f'cw{i}' for i in range(4)]])).fit(cov_type='HAC', cov_kwds={'maxlags': NW(len(x))})
    R = np.zeros((3, len(f.params))); names = list(f.params.index)
    for k in range(3): R[k, names.index('cw0')] = 1; R[k, names.index(f'cw{k+1}')] = -1
    w = f.wald_test(R, scalar=True); print(f'{mkt}: Wald test that the month-end effect is equal in all four periods: chi2(3) = {w.statistic:.2f}, p = {w.pvalue:.3f}')
    # influence: share of the month-end coefficient from the five most influential month-end weeks, main sample and hold-out
    for name, a, b in (PER[0][0] + ' to Mar 2023', '1999-01-01', '2023-03-17'), ('hold-out', '2023-03-20', '2026-09-30'):
        z = d.loc[a:b]; base = fit(z, BASE).params.calw4; mo = z[z.week4 > 0].index.to_period('M').unique(); infl = []
        for m in mo: infl.append((str(m), base - fit(z[z.index.to_period('M') != m], BASE).params.calw4))
        infl = sorted(infl, key=lambda t: -abs(t[1]))[:5]; drop = [m for m, _ in infl]
        rest = fit(z[~z.index.to_period('M').astype(str).isin(drop)], BASE)
        print(f'   {name}: coefficient {base:.3f}; without its 5 most influential months ({", ".join(drop)}) {rest.params.calw4:.3f} (t {rest.tvalues.calw4:.2f}), from {len(mo)} months')
T = pd.DataFrame(rows); print(); print(T.pivot_table(index=['market', 'period'], columns='model', values=['calw4', 't'], sort=False).round(3).to_string())
T.to_pickle('step5_exploratory.pkl')
