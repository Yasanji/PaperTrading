"""Figure data for the letter: pooled local projections h=1..10 and cumulative signal-trade returns."""
import numpy as np, pandas as pd, statsmodels.api as sm
import a4_step3_battery as B
R = B.raw(); S = B.build(R); NEW = ['CA', 'AU']; MAIN = B.MAIN
rows = []
for k in ('thr', 'calw4'):
    for h in range(1, 11):
        T = {}
        for m in NEW:
            d = S[m].loc[MAIN[0]:MAIN[1]].copy(); d[f'cum{h}'] = sum(d.xa.shift(-j) for j in range(1, h + 1)); T[m] = d
        z = B.stack(T, NEW, *MAIN, y=f'cum{h}'); tt = pd.factorize(z.index)[0]; o = np.argsort(tt, kind='stable')
        X = [c for c in z.columns if c not in ('y', 'mkt')]
        r = sm.OLS(z.y.iloc[o], z[X].iloc[o]).fit(cov_type='hac-groupsum', cov_kwds={'time': tt[o], 'maxlags': h + 5})
        ci = r.conf_int().loc[k]; rows.append(dict(signal=k, h=h, coef=r.params[k], lo=ci[0], hi=ci[1]))
pd.DataFrame(rows).to_csv('fig1_lp.csv', index=False)
# cumulative gross return of a unit position against the Threshold signal: -sign(thr_t) * (equity minus bond)_{t+1}
cum = {}
for m in ['US', 'UK', 'CA', 'AU', 'DE']:
    d = S[m].dropna(subset=['thr', 'y_next']); cum[m] = (-np.sign(d.thr) * d.y_next).cumsum() * 100
pd.DataFrame(cum).to_csv('fig2_cum.csv')
print(pd.DataFrame(rows).round(3).to_string()); print(pd.DataFrame(cum).ffill().iloc[[0, -1]]); print(MAIN, B.POST, B.END)
