"""Paper 2: corrected analysis after amendment 3 (post-audit), run once. Full equation of Harvey, Mazzoleni and Melone; ECB AAA yields for Germany."""
import io, requests, numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
from local_data import eq
from step2_main import S, fit, ivx_p, boot_p, hodrick, us_lagged
FULL = ['thr', 'cal', 'week4', 'calw4', 'xa0', 'xa1', 'xa2', 'xa3', 'xa4', 'mom']
MAIN, HOLD = ('1999-01-01', '2023-03-17'), ('2023-03-20', '2026-09-30')
def ecb10():
    u = 'https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?format=csvdata'
    e = pd.read_csv(io.StringIO(requests.get(u, timeout=90).text)); return e.set_index(pd.to_datetime(e.TIME_PERIOD)).OBS_VALUE.sort_index() / 100
def build_rb(px, rb):
    d = pd.concat([px.rename('px'), rb.rename('rb')], axis=1).dropna(); d['re'] = d.px.pct_change(); d = d.dropna()
    d['xa'] = d.re - d.rb; re, r_b, n = d.re.values, d.rb.values, len(d)
    drift = lambda w, a, b: w * (1 + a) / (w * (1 + a) + (1 - w) * (1 + b))
    def thr(delta):
        w, s = 0.6, np.empty(n)
        for t in range(n):
            w = drift(w, re[t], r_b[t]); s[t] = w - 0.6
            if abs(w - 0.6) > delta: w = 0.6
        return s
    d['thr'] = np.mean([thr(x) for x in np.arange(0, 0.02501, 0.001)], axis=0)
    mend = d.index.to_series().groupby(d.index.to_period('M')).transform('max') == d.index.to_series()
    w, cal = 0.6, np.empty(n)
    for t in range(n):
        w = drift(w, re[t], r_b[t]); cal[t] = w - 0.6
        if mend.iloc[t]: w = 0.6
    d['cal'] = cal; pos = d.index.to_series().groupby(d.index.to_period('M')).cumcount(ascending=False)
    d['week4'] = (pos < 5).astype(float); d['calw4'] = d.cal * d.week4; cum = d.xa.cumsum()
    d['mom'] = (np.mean([np.sign(cum - cum.shift(h)) for h in range(11, 21)], axis=0) + np.mean([np.sign(cum - cum.shift(h)) for h in (21, 42, 63, 126, 252)], axis=0)) / 2
    for k in range(5): d[f'xa{k}'] = d.xa.shift(k)
    d['y_next'] = d.xa.shift(-1); return d
if __name__ == '__main__':
    e = ecb10(); rb_de = np.exp(-10 * (e - e.shift(1))) - 1 + e.shift(1) / 252          # continuously compounded spot yield, constant 10-year maturity
    data = {'DE': build_rb(eq('^GDAXI'), rb_de.dropna()), 'UK': S['UK']}
    R, P, panels = {}, {}, {}
    for mkt in ('DE', 'UK'):
        d = data[mkt].copy().join(us_lagged(data[mkt].index)).dropna()
        d['thr_o'] = sm.OLS(d.thr, sm.add_constant(d.us_thr)).fit().resid; d['calw4_o'] = sm.OLS(d.calw4, sm.add_constant(d.us_calw4)).fit().resid
        A, B = FULL, FULL + ['us_thr', 'us_calw4']; Bo = ['thr_o', 'cal', 'week4', 'calw4_o'] + FULL[4:] + ['us_thr', 'us_calw4']
        for per, (a, b) in (('main', MAIN), ('hold-out', HOLD)):
            x = d.loc[a:b]; out = {}
            for lab, cols, xs in (('A local', A, ('thr', 'calw4')), ('B with US', B, ('thr', 'calw4')), ('B orthogonal', Bo, ('thr_o', 'calw4_o'))):
                m = fit(x, cols)
                for s in xs:
                    ip = ivx_p(x, s, cols)[1]; bp = boot_p(x, s, cols) if per == 'main' else np.nan
                    out[(lab, s)] = dict(coef=m.params[s], t_nw=m.tvalues[s], ivx_p=ip, boot_p=bp, supported=bool(m.params[s] < 0 and m.tvalues[s] < -2 and ip < 0.05))
                    if per == 'main': P[f'{mkt} {lab} {s}'] = 2 * (1 - stats.norm.cdf(abs(m.tvalues[s])))
                out[('N', lab)] = int(m.nobs)
            if per == 'main':
                for s in ('thr', 'calw4'):
                    b1, t1 = hodrick(x, s, A, 1); b5, t5 = hodrick(x, s, A, 5); b10, t10 = hodrick(x, s, A, 10)
                    out[('LP', s)] = dict(day1=b1, day5=b5, t5=t5, day10=b10, t10=t10, reverses=bool(abs(b10) < 0.5 * abs(b1) and abs(t10) < 2))
                    P[f'{mkt} LP5 {s}'] = 2 * (1 - stats.norm.cdf(abs(t5))); P[f'{mkt} LP10 {s}'] = 2 * (1 - stats.norm.cdf(abs(t10)))
                panels[mkt] = x
            R[(mkt, per)] = out; print(f'\n=== {mkt} {per}  {x.index[0].date()} to {x.index[-1].date()}, N {out[("N","A local")]}')
            for k, v in out.items():
                if isinstance(v, dict): print(f'  {k[0]:13s} {k[1]:8s} ' + '  '.join(f'{a}={b:.4f}' if isinstance(b, float) else f'{a}={b}' for a, b in v.items()))
    st = []
    for mkt in ('DE', 'UK'):
        z = panels[mkt][FULL + ['y_next']].copy(); z['uk'] = float(mkt == 'UK')
        for c in FULL: z[c + '_uk'] = z[c] * z.uk
        st.append(z)
    st = pd.concat(st); cols = FULL + ['uk'] + [c + '_uk' for c in FULL]
    h4 = sm.OLS(st.y_next, sm.add_constant(st[cols])).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(st.index)[0]})
    P['H4 UK minus DE thr'] = 2 * (1 - stats.norm.cdf(abs(h4.tvalues['thr_uk'])))
    print(f'\nH4 (main, common dates): UK minus Germany adjustment coefficient {h4.params["thr_uk"]:.4f} (t {h4.tvalues["thr_uk"]:.2f})')
    pv = pd.Series(P).sort_values(); m_ = len(pv); holm = np.minimum(1, np.maximum.accumulate([(m_ - i) * p for i, p in enumerate(pv.values)]))
    print('\nHolm-adjusted p-values (main sample):'); print(pd.DataFrame(dict(raw=pv.round(4), holm=np.round(holm, 4))).head(8).to_string())
    pd.to_pickle(dict(R=R, h4=(h4.params['thr_uk'], h4.tvalues['thr_uk']), raw=pv, holm=pd.Series(holm, index=pv.index)), 'step6_corrected_results.pkl')
