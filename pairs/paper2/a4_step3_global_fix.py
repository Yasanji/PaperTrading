"""Amendment 6.3 re-run with the timing fix: the MSCI World index closes with the US market, after the UK, German and
Australian closes, so for those markets the global signal is taken from the previous global close (the same rule as the
US signal). Canada closes with the US, so its global signal is unchanged. Re-runs block D only."""
import numpy as np, pandas as pd
import a4_step3_battery as T
R = T.raw(); S = T.build(R); rows = []
for m in T.ALL if hasattr(T, 'ALL') else ['US', 'UK', 'DE', 'CA', 'AU']:
    d = S[m].copy()
    if m in ('UK', 'DE', 'AU'): d[['thr_g', 'calw4_g']] = d[['thr_g', 'calw4_g']].shift(1)
    d = d.loc[T.MAIN[0]:T.MAIN[1]]
    Xg = [c for c in T.cols(m) if c not in ('thr', 'calw4')] + ['thr_g', 'calw4_g']
    r, dd = T.fit(d, 'y_next', Xg)
    rows += [dict(spec='global only', test=m, signal=k, coef=r.params[k], t=r.tvalues[k], start=dd.index[0].date()) for k in ('thr_g', 'calw4_g')]
    if m != 'US':
        r, _ = T.fit(d, 'y_next', T.cols(m) + ['thr_g', 'calw4_g'])
        rows += [dict(spec='local and global', test=m, signal=k, coef=r.params[k], t=r.tvalues[k]) for k in ('thr', 'calw4', 'thr_g', 'calw4_g')]
    rows.append(dict(spec='correlation', test=m, signal='thr with thr_g', coef=d[['thr', 'thr_g']].corr().iloc[0, 1], t=np.nan))
out = pd.DataFrame(rows); out.to_csv('a4_step3_global_fixed.csv', index=False); pd.set_option('display.width', 200); print(out.round(4).to_string(index=False))
