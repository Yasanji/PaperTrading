"""Full Chow-type test: every regressor (incl. constants and controls) interacted with the post-March-2023 dummy;
the Threshold difference is then the gap between separate pre and post regressions, tested with date-clustered SEs."""
import sys, os, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from indep import *
D = pickle.load(open(os.path.join(HERE, 'D.pkl'), 'rb'))
Z = panel(D, ['CA', 'AU'], MAIN[0], END); post = (Z.index >= POST).astype(float)
for c in [c for c in Z.columns if c != '__y']: Z[c + '_P'] = Z[c] * post
Z = Z[(Z.index <= MAIN[1]) | (Z.index >= POST)]
r, n = ols(Z); print('pre thr', r.loc['thr'].round(3).to_dict()); print('diff thr (full interaction)', r.loc['thr_P'].round(3).to_dict())
print('diff cal_lw', r.loc['cal_lw_P'].round(3).to_dict())
for k in ['x_CA', 'x_AU', 'mom_CA', 'mom_AU', 'us_thr_CA', 'us_thr_AU', 'cal_CA', 'cal_AU']: print(k, 'pre', round(r.loc[k, 'b'], 3), 'diff', round(r.loc[k + '_P', 'b'], 3), 't', round(r.loc[k + '_P', 't'], 2))
