"""IVX on the independent panel (reusing only the battery's ivx_multi estimator), US-signal correlations, US-signal coefficients.
Run from the paper2 folder."""
import sys, os, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from indep import *
import a4_step3_battery as B
D = pickle.load(open(os.path.join(HERE, 'D.pkl'), 'rb'))
ren = {'cal_lw': 'calw4', 'lw': 'week4', 'x': 'ret', 'us_cal_lw': 'us_calw4', 'y': 'y_next'}
for m in ['CA', 'AU', 'UK', 'US']:
    d = D[m].rename(columns=ren).loc[MAIN[0]:MAIN[1]]
    X = ['thr', 'cal', 'calw4', 'mom'] + ([] if m == 'US' else ['us_thr', 'us_calw4']) + ['week4', 'ret']
    o, p = B.ivx_multi(d, X); print('IVX', m, {k: (round(b, 3), round(t, 2)) for k, (b, t) in o.items()}, 'joint p', round(p, 4))
for m in ['CA', 'AU', 'UK']:
    d = D[m].loc[MAIN[0]:MAIN[1]]; print('corr local thr/us_thr', m, round(d[['thr', 'us_thr']].corr().iloc[0, 1], 3))
    r, _ = single(D, m, *MAIN); print('  us_thr coef', r.loc[f'us_thr_{m}'].round(3).to_dict(), 'us_cal_lw', r.loc[f'us_cal_lw_{m}'].round(3).to_dict())
    # local signal without US controls
    Z = panel(D, [m], *MAIN).drop(columns=[f'us_thr_{m}', f'us_cal_lw_{m}']).sort_index(); r2, _ = ols(Z, 'nw'); print('  no US ctrl thr', r2.loc['thr'].round(3).to_dict())
