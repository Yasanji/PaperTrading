"""Paper 2: main-sample tests (January 1999 to 17 March 2023), run once, as in PREREGISTRATION.md with AMENDMENTS.md."""
import numpy as np, pandas as pd, statsmodels.api as sm
from scipy import stats
S = pd.read_pickle('local_signals.pkl'); START, END = '1999-01-01', '2023-03-17'; rng = np.random.default_rng(7)
NW = lambda T: int(np.floor(4 * (T / 100) ** (2 / 9)))           # standard Newey-West lag rule
def us_lagged(local_idx):
    u = S['US'][['thr', 'calw4']].rename(columns={'thr': 'us_thr', 'calw4': 'us_calw4'})
    m = pd.merge_asof(pd.DataFrame(index=local_idx).reset_index().rename(columns={'index': 'd'}).sort_values('d'),
                      u.reset_index().rename(columns={'index': 'd', 'Date': 'd'}), on='d', direction='backward', allow_exact_matches=False)
    return m.set_index('d')[['us_thr', 'us_calw4']]
BASE = ['thr', 'calw4', 'xa0', 'xa1', 'xa2', 'xa3', 'xa4', 'mom']
def fit(df, cols, cov='nw'):
    X = sm.add_constant(df[cols]); T = len(df)
    return sm.OLS(df.y_next, X).fit(cov_type='HAC', cov_kwds={'maxlags': NW(T)}) if cov == 'nw' else sm.OLS(df.y_next, X).fit(cov_type='HC1')
def ivx_p(df, x, cols):
    oth = [c for c in cols if c != x]; Z = sm.add_constant(df[oth]); T = len(df)
    res = lambda v: v - Z.values @ np.linalg.lstsq(Z.values, v, rcond=None)[0]
    rz = 1 - 1 / T ** 0.95; dx = np.diff(df[x].values, prepend=df[x].values[0]); z = np.empty(T); acc = 0.0
    for t in range(T): acc = rz * acc + dx[t]; z[t] = acc
    yt, xt, zt = res(df.y_next.values), res(df[x].values), res(z)
    b = (zt @ yt) / (zt @ xt); e = yt - b * xt; v = (zt ** 2 @ e ** 2) / (zt @ xt) ** 2
    return b, 2 * (1 - stats.norm.cdf(abs(b / np.sqrt(v))))
def boot_p(df, x, cols, B=499, L=21):
    oth = [c for c in cols if c != x]; r0 = sm.OLS(df.y_next, sm.add_constant(df[oth])).fit(); e = r0.resid.values; T = len(e)
    t0 = abs(fit(df, cols, 'hc').tvalues[x]); X = sm.add_constant(df[cols]).values; j = list(sm.add_constant(df[cols]).columns).index(x); cnt = 0
    for _ in range(B):
        idx = np.empty(T, int); i = rng.integers(T)
        for t in range(T): idx[t] = i; i = rng.integers(T) if rng.random() < 1 / L else (i + 1) % T
        ys = r0.fittedvalues.values + e[idx]; bb = np.linalg.lstsq(X, ys, rcond=None)[0]; u = ys - X @ bb
        XtXi = np.linalg.inv(X.T @ X); V = XtXi @ (X.T * u ** 2) @ X @ XtXi * T / (T - X.shape[1])
        cnt += abs(bb[j] / np.sqrt(V[j, j])) >= t0
    return (cnt + 1) / (B + 1)
def hodrick(df, x, cols, h):
    d = df.copy(); d['cum'] = sum(d.xa.shift(-k) for k in range(1, h + 1)); d = d.dropna(subset=['cum'])
    X = sm.add_constant(d[cols]).values; b = np.linalg.lstsq(X, d.cum.values, rcond=None)[0]; T = len(d)
    eps = (d.y_next - d.y_next.mean()).values; W = pd.DataFrame(X).rolling(h, min_periods=1).sum().values
    Zi = np.linalg.inv(X.T @ X / T); Sm = (W.T * eps ** 2) @ W / T; V = Zi @ Sm @ Zi / T
    j = 1 + cols.index(x); return b[j], b[j] / np.sqrt(V[j, j])
R, P = {}, {}
for mkt in ('DE', 'UK'):
    d = S[mkt].copy(); d = d.join(us_lagged(d.index)); d = d.loc[START:END].dropna()
    d['thr_o'] = sm.OLS(d.thr, sm.add_constant(d.us_thr)).fit().resid; d['calw4_o'] = sm.OLS(d.calw4, sm.add_constant(d.us_calw4)).fit().resid
    A, B = BASE, BASE + ['us_thr', 'us_calw4']; Bo = ['thr_o', 'calw4_o'] + BASE[2:] + ['us_thr', 'us_calw4']
    out = {}
    for lab, cols, xs in (('A local', A, ('thr', 'calw4')), ('B with US', B, ('thr', 'calw4')), ('B orthogonal', Bo, ('thr_o', 'calw4_o'))):
        m, mh = fit(d, cols), fit(d, cols, 'hc')
        for x in xs:
            ib, ip = ivx_p(d, x, cols); bp = boot_p(d, x, cols)
            ok = m.params[x] < 0 and m.tvalues[x] < -2 and ip < 0.05
            out[(lab, x)] = dict(coef=m.params[x], t_hc=mh.tvalues[x], t_nw=m.tvalues[x], ivx_p=ip, boot_p=bp, supported=ok)
            P[f'{mkt} {lab} {x}'] = 2 * (1 - stats.norm.cdf(abs(m.tvalues[x])))
        out[(lab, 'R2')] = m.rsquared_adj; out[(lab, 'N')] = int(m.nobs)
    for x in ('thr', 'calw4'):
        b1, t1 = hodrick(d, x, A, 1); b5, t5 = hodrick(d, x, A, 5); b10, t10 = hodrick(d, x, A, 10)
        rev = abs(b10) < 0.5 * abs(b1) and abs(t10) < 2
        out[('LP', x)] = dict(day1=b1, t1=t1, day5=b5, t5=t5, day10=b10, t10=t10, reverses=rev)
        P[f'{mkt} LP5 {x}'] = 2 * (1 - stats.norm.cdf(abs(t5))); P[f'{mkt} LP10 {x}'] = 2 * (1 - stats.norm.cdf(abs(t10)))
    a = fit(d, A); out['half_life_days'] = np.log(0.5) / np.log(1 + a.params['thr']) if -1 < a.params['thr'] < 0 else np.nan
    R[mkt] = out; R[mkt + '_data'] = d
st = []
for mkt in ('DE', 'UK'):
    d = R[mkt + '_data'][BASE + ['y_next']].copy(); d['uk'] = float(mkt == 'UK')
    for c in BASE: d[c + '_uk'] = d[c] * d.uk
    st.append(d)
st = pd.concat(st); cols = BASE + ['uk'] + [c + '_uk' for c in BASE]
h4 = sm.OLS(st.y_next, sm.add_constant(st[cols])).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(st.index)[0]})
P['H4 UK minus DE thr'] = 2 * (1 - stats.norm.cdf(abs(h4.tvalues['thr_uk'])))
pv = pd.Series(P).sort_values(); m_ = len(pv); holm = np.minimum(1, np.maximum.accumulate([(m_ - i) * p for i, p in enumerate(pv.values)]))
pd.to_pickle(dict(R={k: v for k, v in R.items() if not k.endswith('_data')}, h4=(h4.params['thr_uk'], h4.tvalues['thr_uk']), holm=pd.Series(holm, index=pv.index), raw=pv), 'step2_main_results.pkl')
for mkt in ('DE', 'UK'):
    o = R[mkt]; print(f'\n=== {mkt}  (N {o[("A local","N")]}, adj R2 {o[("A local","R2")]:.4f}, half-life {o["half_life_days"]:.1f} days)')
    for k, v in o.items():
        if isinstance(v, dict): print(f'{k[0]:14s} {k[1]:8s} ' + '  '.join(f'{a}={b:.4f}' if isinstance(b, float) else f'{a}={b}' for a, b in v.items()))
print(f'\nH4 stacked: UK minus DE adjustment coefficient = {h4.params["thr_uk"]:.4f} (t {h4.tvalues["thr_uk"]:.2f})')
print('\nHolm-adjusted p-values:'); print(pd.DataFrame(dict(raw=pv.round(4), holm=np.round(holm, 4))).to_string())
