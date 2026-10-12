"""Paper 2: Amendments 6, 7 and 8, run once. Checks around the Amendment 4 primary tests.

All series use the bond-alignment fix of Amendment 7.1: yields are aligned to the equity calendar (last yield on or
before each equity date, at most five days old) before the bond return is computed, so both legs span the same days.
Writes a4_step3_results.csv and prints a summary. Usage: python a4_step3_battery.py"""
import os, pickle, numpy as np, pandas as pd, statsmodels.api as sm, yfinance as yf
from scipy import stats
import a4_step2_main as M

RNG = np.random.default_rng(20261012); B = 999
MAIN, END, POST = M.MAIN, M.END, M.POST
BASE = ['thr', 'cal', 'week4', 'calw4', 'mom', 'ret']; US2 = ['us_thr', 'us_calw4']
CACHE = 'a4_step3_raw.pkl'


def raw():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, 'rb'))
    px = yf.download(['^GSPC', '^FTSE', '^GDAXIP', '^GDAXI', '^GSPTSE', '^AXJO', '^990100-USD-STRD', 'CADUSD=X', 'AUDUSD=X', 'GBPUSD=X', 'EURUSD=X'],
                     start='1997-01-01', end='2026-10-02', progress=False, auto_adjust=True)['Close']
    y = dict(US=M.ust(), UK=M.gilt(), DE=M.ecb(), CA=M.boc(), AU=M.y4['AU'].dropna())
    r = dict(px=px, y=y); pickle.dump(r, open(CACHE, 'wb')); return r


def bond(yld, dates, zero=False):
    a = yld.reindex(yld.index.union(dates)).ffill(limit=5).reindex(dates)
    return (np.exp(-10 * (a - a.shift(1))) - 1) if zero else M.par_ret(a.dropna()).reindex(dates)


EQ = dict(US='^GSPC', UK='^FTSE', DE='^GDAXIP', CA='^GSPTSE', AU='^AXJO'); FX = dict(UK='GBPUSD=X', DE='EURUSD=X', CA='CADUSD=X', AU='AUDUSD=X')


def build(R, target=0.6, ca_same_day=False):
    px, Y, S = R['px'], R['y'], {}
    for m, tk in EQ.items():
        p = px[tk].dropna(); rb = bond(Y[m], p.index, zero=(m == 'DE'))
        d = M.signals(p.pct_change(), rb, target)
        d['re_next'] = d.re.shift(-1); d['rb_next'] = d.rb.shift(-1)
        for k in range(1, 5): d[f'xa{k}'] = d.xa.shift(k)
        pos = d.index.to_series().groupby(d.index.to_period('M')).cumcount()
        for w in (1, 2, 3):
            d[f'wk{w}'] = ((pos >= 5 * (w - 1)) & (pos < 5 * w)).astype(float); d[f'calw{w}'] = d.cal * d[f'wk{w}']
        mret = p.resample('ME').last().pct_change(); mret.index = mret.index.to_period('M')
        d['down_prev'] = (mret.shift(1).reindex(d.index.to_period('M')).values < 0).astype(float)
        g = px['^990100-USD-STRD'].dropna() / (px[FX[m]].dropna() if m in FX else 1.0)
        g = g.dropna().reindex(d.index).ffill(limit=3)
        gs = M.signals(g.pct_change(), d.rb, target)[['thr', 'calw4']].rename(columns={'thr': 'thr_g', 'calw4': 'calw4_g'})
        S[m] = d.join(gs)
    us = S['US'][['thr', 'calw4', 're']].rename(columns={'thr': 'us_thr', 'calw4': 'us_calw4', 're': 'spx1'})
    us['spx2'] = us.spx1.shift(1)
    for m in S:
        if m == 'US': continue
        same = ca_same_day and m == 'CA'
        l = pd.merge_asof(pd.DataFrame({'d': S[m].index}), us.reset_index().rename(columns={us.index.name or 'index': 'd'}),
                          on='d', direction='backward', allow_exact_matches=same).set_index('d')
        S[m] = S[m].join(l)
    return S


def cols(m, extra=()):
    return BASE + ([] if m == 'US' else US2) + list(extra)


def fit(d, y, X, cov='nw'):
    d = d.dropna(subset=[y] + X); f = sm.OLS(d[y], sm.add_constant(d[X]))
    r = f.fit(cov_type='HAC', cov_kwds={'maxlags': M.nw_lags(len(d))}) if cov == 'nw' else f.fit(cov_type='HC1')
    return r, d


def stack(S, mk, a, b, y='y_next', extra=(), post=False, common=('thr', 'calw4'), inter=None):
    parts = []
    for m in mk:
        c = cols(m, extra); d = S[m].loc[a:b].dropna(subset=c + [y]).copy(); z = pd.DataFrame(index=d.index); z['y'] = d[y]
        for k in common: z[k] = d[k]
        for k in [k for k in c if k not in common] + ['const']: z[f'{k}_{m}'] = d[k] if k != 'const' else 1.0
        if post:
            p = (d.index >= POST).astype(float)
            for k in common: z[f'{k}_post'] = d[k] * p
        if inter is not None:
            for k in common: z[f'{k}_{inter}'] = d[k] * d[inter]
        z['mkt'] = m; parts.append(z)
    z = pd.concat(parts); z = z.fillna(0.0); return z


def ols_cluster(z, dk=False):
    X = [c for c in z.columns if c not in ('y', 'mkt')]; t = pd.factorize(z.index)[0]
    f = sm.OLS(z.y, z[X])
    if dk:
        o = np.argsort(t, kind='stable'); return sm.OLS(z.y.iloc[o], z[X].iloc[o]).fit(cov_type='hac-groupsum', cov_kwds={'time': t[o], 'maxlags': 10})
    return f.fit(cov_type='cluster', cov_kwds={'groups': t})


def wild(z, k, B=B, w=None):
    """Wild bootstrap by date (Rademacher, shared across markets), null imposed on coefficient k. Returns p-value and draws of t."""
    X = [c for c in z.columns if c not in ('y', 'mkt')]; Xm = z[X].values; y = z.y.values
    t_id = pd.factorize(z.index)[0]; nT = t_id.max() + 1
    j = X.index(k); X0 = np.delete(Xm, j, axis=1)
    b0 = np.linalg.lstsq(X0, y, rcond=None)[0]; fit0 = X0 @ b0; e0 = y - fit0
    XtXi = np.linalg.inv(Xm.T @ Xm)
    def tstat(yy):
        b = XtXi @ (Xm.T @ yy); u = yy - Xm @ b
        g = np.zeros((nT, Xm.shape[1])); np.add.at(g, t_id, Xm * u[:, None])
        V = XtXi @ (g.T @ g) @ XtXi; return b[j] / np.sqrt(V[j, j])
    t0 = tstat(y); W = w if w is not None else RNG.choice([-1.0, 1.0], size=(B, nT))
    tb = np.array([tstat(fit0 + e0 * W[i][t_id]) for i in range(len(W))])
    return (1 + np.sum(np.abs(tb) >= abs(t0))) / (len(W) + 1), t0, tb


def hodrick(d, x, X, h):
    d = d.dropna(subset=X + ['xa']).copy(); d['cum'] = sum(d.xa.shift(-k) for k in range(1, h + 1)); d = d.dropna(subset=['cum'])
    Xm = sm.add_constant(d[X]).values; b = np.linalg.lstsq(Xm, d.cum.values, rcond=None)[0]; T = len(d)
    eps = (d.y_next - d.y_next.mean()).values; W = pd.DataFrame(Xm).rolling(h, min_periods=1).sum().values
    Zi = np.linalg.inv(Xm.T @ Xm / T); Sm = (W.T * eps ** 2) @ W / T; V = Zi @ Sm @ Zi / T; j = 1 + X.index(x)
    return b[j], b[j] / np.sqrt(V[j, j])


def ivx_multi(d, X, y='y_next'):
    """Multivariate IVX (Kostakis-Magdalinos-Stamatogiannis instruments for all regressors), White variance; returns coef, t, Wald p for thr/calw4."""
    d = d.dropna(subset=X + [y]); T = len(d); rz = 1 - 1 / T ** 0.95
    Xv = d[X].values; Z = np.empty_like(Xv); acc = np.zeros(Xv.shape[1]); dx = np.vstack([np.zeros(Xv.shape[1]), np.diff(Xv, axis=0)])
    for t in range(T): acc = rz * acc + dx[t]; Z[t] = acc
    yv = d[y].values - d[y].mean(); Xc = Xv - Xv.mean(0); Zc = Z - Z.mean(0)
    A = np.linalg.inv(Zc.T @ Xc); b = A @ (Zc.T @ yv); e = yv - Xc @ b
    V = A @ ((Zc * e[:, None] ** 2).T @ Zc) @ A.T
    out = {k: (b[X.index(k)], b[X.index(k)] / np.sqrt(V[X.index(k), X.index(k)])) for k in ('thr', 'calw4')}
    ii = [X.index('thr'), X.index('calw4')]; w = b[ii] @ np.linalg.inv(V[np.ix_(ii, ii)]) @ b[ii]
    return out, 1 - stats.chi2.cdf(w, 2)


if __name__ == '__main__':
    R = raw(); S = build(R); Sc = build(R, ca_same_day=True); rows = []
    add = lambda **k: rows.append(k)
    NEW, ALL = ['CA', 'AU'], ['US', 'UK', 'DE', 'CA', 'AU']

    # A. primary tests re-run with the alignment fix (7.1); Canada same-day US signal (7.2)
    for lab, SS in (('aligned', S), ('aligned, Canada same-day US', Sc)):
        for g, mk in (('new', NEW), ('all', ALL)):
            r = ols_cluster(stack(SS, mk, *MAIN)); rp = ols_cluster(stack(SS, mk, MAIN[0], END, post=True))
            for k in ('thr', 'calw4'):
                add(block='A primary', spec=lab, test=f'pooled {g}', signal=k, coef=r.params[k], t=r.tvalues[k])
                add(block='A primary', spec=lab, test=f'change after Mar 2023, {g}', signal=k, coef=rp.params[f'{k}_post'], t=rp.tvalues[f'{k}_post'],
                    note=f"95% CI {rp.conf_int().loc[f'{k}_post', 0]:.3f} to {rp.conf_int().loc[f'{k}_post', 1]:.3f}")
        for m in ALL:
            r, _ = fit(SS[m].loc[MAIN[0]:MAIN[1]], 'y_next', cols(m))
            for k in ('thr', 'calw4'): add(block='A primary', spec=lab, test=m, signal=k, coef=r.params[k], t=r.tvalues[k])

    # B. error correction (6.1): current and four previous returns
    for m in ALL:
        X = [c for c in cols(m) if c != 'ret'] + ['xa'] + [f'xa{k}' for k in range(1, 5)]
        r, _ = fit(S[m].loc[MAIN[0]:MAIN[1]], 'y_next', X); a = r.params['thr']
        add(block='B error correction', spec='5 lags', test=m, signal='thr', coef=a, t=r.tvalues['thr'], note=f'half-life {np.log(0.5) / np.log(1 + a):.2f} days' if -1 < a < 0 else '')
        add(block='B error correction', spec='5 lags', test=m, signal='calw4', coef=r.params['calw4'], t=r.tvalues['calw4'])

    # C. local projections and reversal (6.2, 8.8)
    for m in ALL:
        d = S[m].loc[MAIN[0]:MAIN[1]]; X = cols(m)
        for k in ('thr', 'calw4'):
            res = {h: hodrick(d, k, X, h) for h in (1, 5, 10)}
            rev = abs(res[10][0]) < 0.5 * abs(res[1][0]) and abs(res[10][1]) < 2
            for h, (b, t) in res.items(): add(block='C local projections', spec=f'h={h}', test=m, signal=k, coef=b, t=t, note=f'reversal by day 10: {rev}' if h == 10 else '')
    for k in ('thr', 'calw4'):                                     # pooled new markets: cumulative return on the stacked panel
        for h in (1, 5, 10):
            parts = []
            for m in NEW:
                d = S[m].loc[MAIN[0]:MAIN[1]].copy(); d[f'cum{h}'] = sum(d.xa.shift(-j) for j in range(1, h + 1)); parts.append(d)
            T = {m: p for m, p in zip(NEW, parts)}
            z = stack(T, NEW, *MAIN, y=f'cum{h}'); o = np.argsort(pd.factorize(z.index)[0], kind='stable')
            X_ = [c for c in z.columns if c not in ('y', 'mkt')]; tt = pd.factorize(z.index)[0]
            r = sm.OLS(z.y.iloc[o], z[X_].iloc[o]).fit(cov_type='hac-groupsum', cov_kwds={'time': tt[o], 'maxlags': h + 5})
            add(block='C local projections', spec=f'h={h}', test='pooled new (Driscoll-Kraay)', signal=k, coef=r.params[k], t=r.tvalues[k],
                note=f"95% CI {r.conf_int().loc[k, 0]:.3f} to {r.conf_int().loc[k, 1]:.3f}")

    # D. global equity leg (6.3)
    for m in ALL:
        d = S[m].loc[MAIN[0]:MAIN[1]]
        Xg = [c for c in cols(m) if c not in ('thr', 'calw4')] + ['thr_g', 'calw4_g']
        r, dd = fit(d, 'y_next', Xg); add(block='D global leg', spec='global only', test=m, signal='thr_g', coef=r.params['thr_g'], t=r.tvalues['thr_g'], note=f'from {dd.index[0].date()}')
        add(block='D global leg', spec='global only', test=m, signal='calw4_g', coef=r.params['calw4_g'], t=r.tvalues['calw4_g'])
        if m != 'US':
            r, _ = fit(d, 'y_next', cols(m) + ['thr_g', 'calw4_g'])
            for k in ('thr', 'calw4', 'thr_g', 'calw4_g'): add(block='D global leg', spec='local and global', test=m, signal=k, coef=r.params[k], t=r.tvalues[k])

    # E. spillover control (6.4)
    for g, mk in (('new', NEW),):
        r = ols_cluster(stack(S, mk, *MAIN, extra=('spx1', 'spx2')))
        for k in ('thr', 'calw4'): add(block='E spillover', spec='+ two lagged S&P 500 returns', test=f'pooled {g}', signal=k, coef=r.params[k], t=r.tvalues[k])
    for m in ['CA', 'AU', 'UK', 'DE']:
        r, _ = fit(S[m].loc[MAIN[0]:MAIN[1]], 'y_next', cols(m, ('spx1', 'spx2')))
        for k in ('thr', 'calw4'): add(block='E spillover', spec='+ two lagged S&P 500 returns', test=m, signal=k, coef=r.params[k], t=r.tvalues[k])

    # F. Driscoll-Kraay (6.5), joint Wald (8.4)
    for g, mk in (('new', NEW), ('all', ALL)):
        z = stack(S, mk, *MAIN); r = ols_cluster(z, dk=True)
        for k in ('thr', 'calw4'): add(block='F inference', spec='Driscoll-Kraay', test=f'pooled {g}', signal=k, coef=r.params[k], t=r.tvalues[k])
        rc = ols_cluster(z); w = rc.wald_test('thr = 0, calw4 = 0', scalar=True)
        add(block='F inference', spec='joint Wald', test=f'pooled {g}', signal='thr and calw4', coef=np.nan, t=np.nan, note=f'p = {float(w.pvalue):.4f}')

    # G. placebo weeks (6.6)
    for g, mk in (('new', NEW),):
        for w in (1, 2, 3):
            parts = {}
            for m in mk:
                d = S[m].copy(); d['calw4'] = d[f'calw{w}']; parts[m] = d
            r = ols_cluster(stack(parts, mk, *MAIN))
            add(block='G placebo', spec=f'Calendar x week {w}', test=f'pooled {g}', signal='calw (placebo)', coef=r.params['calw4'], t=r.tvalues['calw4'])

    # H. which leg moves (6.7)
    for y in ('re_next', 'rb_next'):
        r = ols_cluster(stack(S, NEW, *MAIN, y=y))
        for k in ('thr', 'calw4'): add(block='H legs', spec=y, test='pooled new', signal=k, coef=r.params[k], t=r.tvalues[k])

    # I. stability (6.8), drawdown split (8.5)
    for a, b in (('1999-01-01', '2008-12-31'), ('2009-01-01', MAIN[1])):
        r = ols_cluster(stack(S, NEW, a, b))
        for k in ('thr', 'calw4'): add(block='I stability', spec=f'{a[:4]}-{b[:4]}', test='pooled new', signal=k, coef=r.params[k], t=r.tvalues[k])
    parts = []
    for m in NEW:
        d = S[m].loc[MAIN[0]:MAIN[1]].dropna(subset=cols(m) + ['y_next']); z = pd.DataFrame({'y': d.y_next, 'thr': d.thr, 'calw4': d.calw4})
        for mm in NEW:
            z[f'thr_{mm}'] = d.thr * (m == mm)
        for k in [k for k in cols(m) if k not in ('thr', 'calw4')] + ['const']: z[f'{k}_{m}'] = d[k] if k != 'const' else 1.0
        parts.append(z)
    z = pd.concat(parts).fillna(0.0).drop(columns=['thr']); r = ols_cluster(z)
    w = r.wald_test(f'thr_{NEW[0]} = thr_{NEW[1]}', scalar=True)
    add(block='I stability', spec='equal Threshold across new markets', test='Wald', signal='thr', coef=np.nan, t=np.nan, note=f'p = {float(w.pvalue):.4f}')
    r = ols_cluster(stack(S, NEW, *MAIN, inter='down_prev'))
    add(block='I stability', spec='extra Threshold effect after a down month', test='pooled new', signal='thr x down', coef=r.params['thr_down_prev'], t=r.tvalues['thr_down_prev'])

    # J. out-of-sample R2 and Clark-West (6.9, 8.3); month-end trade Sharpe after 1bp a leg
    for m in ALL:
        d = S[m].dropna(subset=cols(m) + ['y_next']).loc[:MAIN[1]]; X = cols(m); f, b_ = [], []
        for yr in range(2010, int(MAIN[1][:4]) + 1):
            tr = d.loc[:f'{yr - 1}-12-31']; te = d.loc[f'{yr}-01-01':f'{yr}-12-31']
            if te.empty: continue
            c = np.linalg.lstsq(sm.add_constant(tr[X]).values, tr.y_next.values, rcond=None)[0]
            f.append(pd.Series(sm.add_constant(te[X], has_constant='add').values @ c, index=te.index)); b_.append(pd.Series(tr.y_next.mean(), index=te.index))
        f, b_ = pd.concat(f), pd.concat(b_); y = d.y_next.reindex(f.index)
        r2 = 1 - ((y - f) ** 2).sum() / ((y - b_) ** 2).sum()
        cw = (y - b_) ** 2 - ((y - f) ** 2 - (b_ - f) ** 2); cwt = sm.OLS(cw.values, np.ones(len(cw))).fit(cov_type='HAC', cov_kwds={'maxlags': 10}).tvalues[0]
        add(block='J out of sample', spec='expanding from 2010', test=m, signal='R2 (Campbell-Thompson)', coef=r2, t=cwt, note='t is Clark-West, one-sided')
        dd = S[m].loc[MAIN[0]:MAIN[1]].dropna(subset=['calw4', 'y_next']); pos = -np.sign(dd.calw4) * dd.week4
        pnl = pos * dd.y_next - pos.diff().abs().fillna(abs(pos)) * 2e-4
        add(block='J out of sample', spec='month-end trade, 1bp a leg', test=m, signal='Sharpe', coef=pnl.mean() / pnl.std() * np.sqrt(252), t=np.nan)

    # K. IVX (8.6), wild bootstrap and Romano-Wolf (8.1, 8.2), Ibragimov-Mueller (8.7)
    for m in ALL:
        d = S[m].loc[MAIN[0]:MAIN[1]]; X = [c for c in cols(m) if c not in ('week4', 'ret')] + ['week4', 'ret']
        o, p = ivx_multi(d, X)
        for k, (b, t) in o.items(): add(block='K IVX multivariate', spec='White variance', test=m, signal=k, coef=b, t=t, note=f'joint p = {p:.4f}' if k == 'calw4' else '')
    fam = {}
    for g, mk in (('pooled new', NEW), ('pooled all', ALL)):
        fam[g] = stack(S, mk, *MAIN)
    for m in ALL:
        d = S[m].loc[MAIN[0]:MAIN[1]].dropna(subset=cols(m) + ['y_next']); z = pd.DataFrame({'y': d.y_next}, index=d.index)
        for k in cols(m) + ['const']: z[k] = d[k] if k != 'const' else 1.0
        z['mkt'] = m; fam[m] = z
    dates = sorted(set().union(*[set(z.index) for z in fam.values()])); Wd = pd.DataFrame(RNG.choice([-1.0, 1.0], size=(B, len(dates))), columns=dates)
    T0, TB = {}, {}
    for name, z in fam.items():
        w = Wd[list(pd.unique(z.index))].values; zid = pd.factorize(z.index)[0]
        for k in ('thr', 'calw4'):
            pv, t0, tb = wild(z, k, w=w); T0[(name, k)] = t0; TB[(name, k)] = tb
            add(block='K wild bootstrap', spec='by date, Rademacher, 999', test=name, signal=k, coef=np.nan, t=t0, note=f'p = {pv:.4f}')
    keys = sorted(T0, key=lambda k: -abs(T0[k])); maxd = np.array([TB[k] for k in keys]); rw = {}; prev = 0
    for i, k in enumerate(keys):
        p = (1 + np.sum(np.max(np.abs(maxd[i:]), axis=0) >= abs(T0[k]))) / (B + 1); prev = max(prev, p); rw[k] = prev
    for k in keys: add(block='K Romano-Wolf', spec='step-down over 14 tests', test=k[0], signal=k[1], coef=np.nan, t=T0[k], note=f'p = {rw[k]:.4f}')
    for g, mk in (('new', NEW), ('all', ALL)):
        for k in ('thr', 'calw4'):
            est = [fit(S[m].loc[MAIN[0]:MAIN[1]], 'y_next', cols(m))[0].params[k] for m in mk]
            t = np.mean(est) / (np.std(est, ddof=1) / np.sqrt(len(est)))
            add(block='K Ibragimov-Mueller', spec=f'{len(est)} markets', test=g, signal=k, coef=np.mean(est), t=t, note=f'p = {2 * (1 - stats.t.cdf(abs(t), len(est) - 1)):.4f}')

    out = pd.DataFrame(rows); out.to_csv('a4_step3_results.csv', index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500); pd.set_option('display.max_colwidth', 60)
    print(out.round(4).to_string(index=False))
