"""Paper 2 audit: Step 1 on total-return ETFs, Bund timing against an ETF, the ECB yield as an alternative, and the omitted-terms test."""
import io, requests, numpy as np, pandas as pd, statsmodels.api as sm
from local_data import eq
from step2_main import S, fit, ivx_p, us_lagged, BASE
from step6_corrected import build_rb, ecb10
if __name__ == '__main__':
    spy, ief = eq('SPY'), eq('IEF'); etf = build_rb(spy, ief.pct_change())
    for lab, d in (('ETFs (SPY, IEF)', etf), ('index and yields', S['US'])):
        s = d.loc['2003-09-03':'2023-03-17'].dropna(subset=['y_next', 'mom'])
        m = sm.OLS(s.y_next, sm.add_constant(s[['thr', 'cal', 'week4', 'calw4', 'mom', 'xa0']])).fit(cov_type='HC1')
        print(f'Step 1, {lab}: Threshold {m.params.thr:+.3f} (t {m.tvalues.thr:+.2f}) | Calendar x last week {m.params.calw4:+.3f} (t {m.tvalues.calw4:+.2f})')
    x = eq('EXX6.DE').pct_change().rename('etf')
    z = pd.concat([S['DE'].rb.rename('bbk'), x], axis=1).dropna().loc['2009':]
    print('Bundesbank returns against ETF on day t-1, t, t+1:', [round(z.bbk.corr(z.etf.shift(-k)), 3) for k in (-1, 0, 1)])
    e = ecb10(); rb = np.exp(-10 * (e - e.shift(1))) - 1 + e.shift(1) / 252; z = pd.concat([rb.rename('ecb'), x], axis=1).dropna().loc['2009':]
    print('ECB returns against ETF on day t-1, t, t+1:', [round(z.ecb.corr(z.etf.shift(-k)), 3) for k in (-1, 0, 1)])
    FULL = ['thr', 'cal', 'week4', 'calw4', 'xa0', 'xa1', 'xa2', 'xa3', 'xa4', 'mom']
    for mkt in ('DE', 'UK'):
        d = S[mkt].copy().join(us_lagged(S[mkt].index)).dropna()
        for per, (a, b) in (('main', ('1999-01-01', '2023-03-17')), ('hold-out', ('2023-03-20', '2026-09-30'))):
            x_ = d.loc[a:b]; f0, f1 = fit(x_, BASE), fit(x_, FULL)
            print(f'{mkt} {per}: pre-registered calw4 {f0.params.calw4:+.3f} (t {f0.tvalues.calw4:+.2f}) | full equation {f1.params.calw4:+.3f} (t {f1.tvalues.calw4:+.2f})')
