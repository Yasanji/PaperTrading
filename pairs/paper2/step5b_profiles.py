"""Paper 2: exploratory profiles of the Calendar effect by week of the month and by day around month-end (not pre-registered)."""
import numpy as np, pandas as pd, statsmodels.api as sm
from step2_main import S, NW
MAIN = ('1999-01-01', '2023-03-17'); US_MAIN = ('1997-09-10', '2023-03-17')
def prep(d):
    d = d.copy(); idx = d.index.to_series(); per = idx.dt.to_period('M')
    d['k_end'] = -(idx.groupby(per).cumcount(ascending=False) + 1); d['k_start'] = idx.groupby(per).cumcount() + 1
    d['wk'] = np.minimum((d.k_start - 1) // 5 + 1, 4); d.loc[d.k_end >= -5, 'wk'] = 4; return d
def run(d, terms): return sm.OLS(d.y_next, sm.add_constant(d[terms])).fit(cov_type='HAC', cov_kwds={'maxlags': NW(len(d))})
if __name__ == '__main__':
    for mkt, (a, b) in (('US', US_MAIN), ('UK', MAIN), ('DE', MAIN)):
        d = prep(S[mkt]).loc[a:b].dropna(subset=['y_next', 'mom'])
        for w in (1, 2, 3, 4): d[f'cw{w}'] = d.cal * (d.wk == w); d[f'w{w}'] = (d.wk == w).astype(float)
        f = run(d, ['thr', 'cw1', 'cw2', 'cw3', 'cw4', 'w2', 'w3', 'w4', 'mom', 'xa0'])
        print(f'{mkt} by week: ' + ' | '.join(f'week {w} {f.params[f"cw{w}"]:+.3f} (t {f.tvalues[f"cw{w}"]:+.2f})' for w in (1, 2, 3, 4)))
        terms = ['thr', 'cal', 'mom', 'xa0']; days = [('end', k) for k in range(-10, 0)] + [('start', k) for k in range(1, 6)]
        for side, k in days:
            col = f'c{side}{k}'; dm = (d.k_end == k) if side == 'end' else (d.k_start == k); d[col] = d.cal * dm; d['D' + col] = dm.astype(float); terms += [col, 'D' + col]
        f = run(d, terms); print(f'{mkt} by day: ' + ', '.join(f'{k:+d} {f.params[f"c{s}{k}"]:+.2f} ({f.tvalues[f"c{s}{k}"]:+.1f})' for s, k in days))
