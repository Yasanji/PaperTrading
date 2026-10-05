"""Paper 2: hold-out tests (20 March 2023 to September 2026), run once, with the same regressions as Step 1 and step2_main.py."""
import numpy as np, pandas as pd, statsmodels.api as sm
from step2_main import S, NW, us_lagged, fit, ivx_p, BASE
H0, H1 = '2023-03-20', '2026-09-30'
us = S['US'].loc[H0:H1].dropna(subset=['y_next', 'mom'])
m = sm.OLS(us.y_next, sm.add_constant(us[['thr', 'cal', 'week4', 'calw4', 'mom', 'xa0']])).fit(cov_type='HC1')
print(f'US replication, hold-out (N {int(m.nobs)}): Threshold {m.params.thr:.3f} (t {m.tvalues.thr:.2f}) | Calendar x last week {m.params.calw4:.3f} (t {m.tvalues.calw4:.2f})')
rows = []
for mkt in ('DE', 'UK'):
    d = S[mkt].copy(); d = d.join(us_lagged(d.index)); d = d.loc[H0:H1].dropna()
    for lab, cols in (('local only', BASE), ('with US signals', BASE + ['us_thr', 'us_calw4'])):
        f = fit(d, cols)
        for x in ('thr', 'calw4'):
            rows.append(dict(market=mkt, model=lab, signal=x, coef=round(f.params[x], 3), t_nw=round(f.tvalues[x], 2), ivx_p=round(ivx_p(d, x, cols)[1], 3), N=int(f.nobs)))
R = pd.DataFrame(rows); print(R.to_string(index=False)); R.to_pickle('step3_holdout_results.pkl')
