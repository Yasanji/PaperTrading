"""Independent re-implementation of signals, bond returns, panel and regressions for the audit.
Only the cached raw data (a4_step3_raw.pkl) is taken from the repo. Run from the paper2 folder:
  cd .../pt/pairs/paper2 && python ../../../audit_v2/indep.py
"""
import pickle, numpy as np, pandas as pd

RAW = pickle.load(open('a4_step3_raw.pkl', 'rb'))
EQ = dict(US='^GSPC', UK='^FTSE', DE='^GDAXIP', CA='^GSPTSE', AU='^AXJO')
MAIN = ('1999-01-01', '2023-03-17'); POST = '2023-03-20'; END = '2026-09-30'


def par_price(c, y):
    i = np.arange(1, 21)
    return (c / 2 * (1 + y / 2) ** -i[:, None]).sum(0) + (1 + y / 2) ** -20


def bond_ret(y, dates, zero):
    a = y.reindex(y.index.union(dates)).ffill(limit=5).reindex(dates)
    if zero:
        return np.exp(-10 * a.diff()) - 1
    prev = a.shift(1)
    v = pd.Series(np.nan, index=dates)
    ok = a.notna() & prev.notna()
    v[ok] = par_price(prev[ok].values, a[ok].values) - 1
    return v


def drift(w, re, rb):
    return w * (1 + re) / (w * (1 + re) + (1 - w) * (1 + rb))


def make(m, target=0.6, bands=None, px=None, yy=None):
    p = (px if px is not None else RAW['px'][EQ[m]]).dropna()
    re = p.pct_change(); rb = bond_ret(RAW['y'][m] if yy is None else yy, p.index, m == 'DE')
    d = pd.DataFrame({'re': re, 'rb': rb}).dropna()
    a, b, n = d.re.values, d.rb.values, len(d)
    bands = np.round(np.arange(0, 26) / 1000, 4) if bands is None else bands
    S = np.zeros((len(bands), n))
    for j, delta in enumerate(bands):
        w = target
        for t in range(n):
            w = drift(w, a[t], b[t]); S[j, t] = w - target
            if abs(w - target) > delta + 1e-15: w = target
    d['thr'] = S.mean(0)
    per = d.index.to_period('M'); last = pd.Series(d.index, index=d.index).groupby(per).transform('max') == d.index
    w = target; cal = np.zeros(n)
    for t in range(n):
        w = drift(w, a[t], b[t]); cal[t] = w - target
        if last.iloc[t]: w = target
    d['cal'] = cal
    rk = pd.Series(1, index=d.index).groupby(per).cumsum()
    cnt = pd.Series(1, index=d.index).groupby(per).transform('sum')
    d['lw'] = ((cnt - rk) < 5).astype(float); d['cal_lw'] = d.cal * d.lw
    d['x'] = d.re - d.rb; c = d.x.cumsum()
    fast = np.mean([np.sign(c - c.shift(h)) for h in range(11, 21)], 0)
    slow = np.mean([np.sign(c - c.shift(h)) for h in (21, 42, 63, 126, 252)], 0)
    d['mom'] = (fast + slow) / 2
    d['y'] = d.x.shift(-1); d['re1'] = d.re.shift(-1); d['rb1'] = d.rb.shift(-1)
    return d


def attach_us(D, ca_same=False):
    us = D['US'][['thr', 'cal_lw', 're']].rename(columns={'thr': 'us_thr', 'cal_lw': 'us_cal_lw', 're': 'spx'})
    for m in D:
        if m == 'US': continue
        out = []
        for t in D[m].index:
            k = us.index.searchsorted(t, side='right' if (ca_same and m == 'CA') else 'left') - 1
            out.append(us.iloc[k].values if k >= 0 else [np.nan] * 3)
        D[m][['us_thr', 'us_cal_lw', 'spx']] = np.array(out)
    return D


CTRL = ['cal', 'lw', 'mom', 'x']


def ctrls(m, extra=()):
    return CTRL + ([] if m == 'US' else ['us_thr', 'us_cal_lw']) + list(extra)


def panel(D, mk, a, b, y='y', sig=('thr', 'cal_lw'), extra=(), post=None, mask=None):
    rows = []
    for m in mk:
        c = ctrls(m, extra); d = D[m].loc[a:b].dropna(subset=list(sig) + c + [y])
        if mask is not None: d = d[mask(d)]
        Z = pd.DataFrame(index=d.index); Z['__y'] = d[y]
        for s in sig: Z[s] = d[s]
        if post:
            for s in sig: Z[s + '_post'] = d[s] * (d.index >= post)
        for k in c: Z[f'{k}_{m}'] = d[k]
        Z[f'const_{m}'] = 1.0; rows.append(Z)
    return pd.concat(rows).fillna(0.0)


def ols(Z, se='cluster', lags=None):
    y = Z['__y'].values; X = Z.drop(columns='__y'); names = list(X.columns); X = X.values
    n, k = X.shape; XtXi = np.linalg.inv(X.T @ X); b = XtXi @ X.T @ y; u = y - X @ b
    if se == 'cluster':
        g = pd.factorize(Z.index)[0]; G = g.max() + 1
        sc = np.zeros((G, k)); np.add.at(sc, g, X * u[:, None])
        V = XtXi @ (sc.T @ sc) @ XtXi * G / (G - 1) * (n - 1) / (n - k)
    elif se == 'hc1':
        V = XtXi @ ((X * u[:, None] ** 2).T @ X) @ XtXi * n / (n - k)
    elif se in ('nw', 'dk'):
        # nw: single market; dk: sum scores by date first (Driscoll-Kraay)
        if se == 'dk':
            g = pd.factorize(Z.index)[0]; G = g.max() + 1; o = np.argsort(pd.Index(Z.index).unique().argsort())
            sc = np.zeros((G, k)); np.add.at(sc, g, X * u[:, None])
            dates = pd.Index(Z.index).unique(); sc = sc[np.argsort(dates)]
        else:
            sc = X * u[:, None]
        L = lags if lags is not None else int(np.floor(4 * (len(sc) / 100) ** (2 / 9)))
        Sm = sc.T @ sc
        for l in range(1, L + 1):
            G_ = sc[l:].T @ sc[:-l]; Sm += (1 - l / (L + 1)) * (G_ + G_.T)
        V = XtXi @ Sm @ XtXi
    se_ = np.sqrt(np.diag(V))
    return pd.DataFrame({'b': b, 'se': se_, 't': b / se_}, index=names), n


def single(D, m, a, b, se='nw', y='y', extra=(), sig=('thr', 'cal_lw')):
    Z = panel(D, [m], a, b, y=y, sig=sig, extra=extra)
    Z = Z.sort_index()
    return ols(Z, se)


if __name__ == '__main__':
    D = attach_us({m: make(m) for m in EQ})
    pickle.dump(D, open('/tmp/claude-0/-home-claude/2d43c9b6-fb2c-5daf-ac7e-d062f06e8084/scratchpad/audit_v2/D.pkl', 'wb'))
    r, n = ols(panel(D, ['CA', 'AU'], *MAIN)); print('pooled new', n); print(r.loc[['thr', 'cal_lw']])
