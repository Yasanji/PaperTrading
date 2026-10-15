"""Recompute every numeric claim of the draft with the independent pipeline (indep.py) and run extra robustness.
Run from the paper2 folder: python ../../../audit_v2/ledger.py  -> writes audit_v2/ledger_out.txt"""
import sys, os, pickle, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from indep import *
from scipy import stats

OUT = open(os.path.join(HERE, 'ledger_out.txt'), 'w')
def P(*a):
    s = ' '.join(str(x) for x in a); print(s); OUT.write(s + '\n'); OUT.flush()

D = pickle.load(open(os.path.join(HERE, 'D.pkl'), 'rb'))
Dc = attach_us({m: D[m].drop(columns=['us_thr', 'us_cal_lw', 'spx'], errors='ignore').copy() for m in D}, ca_same=True)
NEW, ALL = ['CA', 'AU'], ['US', 'UK', 'DE', 'CA', 'AU']
fmt = lambda r, k: f"{r.loc[k,'b']:+.3f} (t {r.loc[k,'t']:+.2f})"
def pooled(DD, mk, a, b, **kw):
    r, n = ols(panel(DD, mk, a, b, **kw), kw.pop('se', 'cluster') if 'se' in kw else 'cluster'); return r, n

P('=== TABLE 2 ===')
r, n = ols(panel(D, NEW, *MAIN)); P('pooled new', fmt(r, 'thr'), fmt(r, 'cal_lw'), 'N', n)
for m in NEW: P('  start', m, D[m].loc[MAIN[0]:].dropna(subset=['thr', 'mom', 'us_thr', 'y']).index[0].date())
rp, _ = ols(panel(D, NEW, MAIN[0], END, post=POST))
for k in ('thr_post', 'cal_lw_post'):
    b, s = rp.loc[k, 'b'], rp.loc[k, 'se']; P('change', k, f'{b:+.3f} CI [{b-1.96*s:.3f}, {b+1.96*s:.3f}] t {b/s:.2f}')
for m in ['CA', 'AU', 'UK', 'DE', 'US']:
    r_, _ = single(D, m, *MAIN); P('single NW', m, fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
r_, _ = single(Dc, 'CA', *MAIN); P('CA same-day US', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
r_, _ = ols(panel(Dc, NEW, *MAIN)); P('pooled new CA same-day', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
r_, _ = ols(panel(D, ALL, *MAIN)); P('pooled all five', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
P('DE first date', D['DE'].dropna(subset=['mom', 'y', 'us_thr']).index[0].date())

# own wild bootstrap (Rademacher by date, null imposed), and Romano-Wolf over 14 tests
rng = np.random.default_rng(7); B = 999
def boot_t(Z, k, W, dates):
    y = Z['__y'].values; X = Z.drop(columns='__y'); names = list(X.columns); X = X.values; j = names.index(k)
    g = pd.factorize(Z.index)[0]; G = g.max() + 1; pos = dates.get_indexer(pd.Index(Z.index).unique())
    X0 = np.delete(X, j, 1); b0 = np.linalg.lstsq(X0, y, rcond=None)[0]; f0 = X0 @ b0; e0 = y - f0
    XtXi = np.linalg.inv(X.T @ X)
    def t(yy):
        b = XtXi @ (X.T @ yy); u = yy - X @ b; sc = np.zeros((G, X.shape[1])); np.add.at(sc, g, X * u[:, None])
        V = XtXi @ sc.T @ sc @ XtXi; return b[j] / np.sqrt(V[j, j])
    t0 = t(y); tb = np.array([t(f0 + e0 * W[i, pos][g]) for i in range(len(W))]); return t0, tb
fam = {'pooled new': panel(D, NEW, *MAIN), 'pooled all': panel(D, ALL, *MAIN)}
for m in ALL: fam[m] = panel(D, [m], *MAIN)
dates = pd.Index(sorted(set().union(*[set(z.index) for z in fam.values()]))); W = rng.choice([-1., 1.], size=(B, len(dates)))
T0, TB = {}, {}
for nm, Z in fam.items():
    for k in ('thr', 'cal_lw'):
        T0[(nm, k)], TB[(nm, k)] = boot_t(Z, k, W, dates)
        if nm == 'pooled new': P('wild p', nm, k, (1 + np.sum(np.abs(TB[(nm, k)]) >= abs(T0[(nm, k)]))) / (B + 1))
keys = sorted(T0, key=lambda k: -abs(T0[k])); M_ = np.abs(np.array([TB[k] for k in keys])); prev = 0; RW = {}
for i, k in enumerate(keys):
    p = (1 + np.sum(M_[i:].max(0) >= abs(T0[k]))) / (B + 1); prev = max(prev, p); RW[k] = prev
for k in keys: P('RW', k, round(RW[k], 3))
cal_rw = [RW[k] for k in keys if k[1] == 'cal_lw']; P('Calendar RW range', min(cal_rw), max(cal_rw))

P('=== Threshold paragraph ===')
Z = panel(D, NEW, *MAIN); Zs = Z.sort_index(); r_, _ = ols(Zs, 'dk', lags=10); P('DK', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
r_, _ = ols(panel(D, NEW, *MAIN, extra=('spx', 'spx_l'), ) if False else panel({m: D[m].assign(spx_l=D[m].spx.shift(1)) for m in NEW}, NEW, *MAIN, extra=('spx', 'spx_l')))
P('+2 lagged SPX', fmt(r_, 'thr'))
# NB: battery's spx2 is US-calendar lag; here lag on local calendar (check)
est = {m: single(D, m, *MAIN)[0] for m in ALL}
for g, mk in (('new', NEW), ('all', ALL)):
    for k in ('thr', 'cal_lw'):
        e = np.array([est[m].loc[k, 'b'] for m in mk]); t = e.mean() / (e.std(ddof=1) / np.sqrt(len(e)))
        P('IM', g, k, round(e.mean(), 3), 'p', round(2 * stats.t.sf(abs(t), len(e) - 1), 3))
# Wald equal CA vs AU
Zs = []
for m in NEW:
    z = panel(D, [m], *MAIN); z[f'thrX_{m}'] = z['thr']; Zs.append(z.drop(columns='thr'))
Zw = pd.concat(Zs).fillna(0.0); rw_, _ = ols(Zw)
y = Zw['__y'].values; X = Zw.drop(columns='__y'); nm = list(X.columns); Xv = X.values
XtXi = np.linalg.inv(Xv.T @ Xv); bb = XtXi @ Xv.T @ y; u = y - Xv @ bb; g = pd.factorize(Zw.index)[0]; G = g.max() + 1
sc = np.zeros((G, Xv.shape[1])); np.add.at(sc, g, Xv * u[:, None]); V = XtXi @ sc.T @ sc @ XtXi * G / (G - 1) * (len(y) - 1) / (len(y) - Xv.shape[1])
i, j = nm.index('thrX_CA'), nm.index('thrX_AU'); dlt = bb[i] - bb[j]; vd = V[i, i] + V[j, j] - 2 * V[i, j]
P('Wald CA=AU p', round(2 * stats.norm.sf(abs(dlt / np.sqrt(vd))), 3), 'CA', round(bb[i], 3), 'AU', round(bb[j], 3))
# Clark-West
for m in ['CA', 'AU']:
    d = D[m].dropna(subset=['thr', 'cal_lw'] + ctrls(m) + ['y']).loc[:MAIN[1]]; X_ = ['thr', 'cal_lw'] + ctrls(m); f, bm = [], []
    for yr in range(2010, 2024):
        tr = d.loc[:f'{yr-1}-12-31']; te = d.loc[f'{yr}']
        if te.empty: continue
        A = np.c_[np.ones(len(tr)), tr[X_].values]; c = np.linalg.lstsq(A, tr.y.values, rcond=None)[0]
        f.append(pd.Series(np.c_[np.ones(len(te)), te[X_].values] @ c, te.index)); bm.append(pd.Series(tr.y.mean(), te.index))
    f, bm = pd.concat(f), pd.concat(bm); yy = d.y.reindex(f.index); cw = (yy - bm) ** 2 - ((yy - f) ** 2 - (bm - f) ** 2)
    Zc = pd.DataFrame({'__y': cw.values, 'c': 1.0}, index=cw.index); rc, _ = ols(Zc, 'nw', lags=10)
    P('Clark-West', m, 't', round(rc.loc['c', 't'], 2), 'OOS R2', round(1 - ((yy - f) ** 2).sum() / ((yy - bm) ** 2).sum(), 4))

P('=== Has it faded / sub-periods (pooled new, cluster) ===')
for lab, a, b in [('1999-2019', MAIN[0], '2019-12-31'), ('2020-Mar2023', '2020-01-01', MAIN[1]), ('later alone', POST, END),
                  ('1999-2008', MAIN[0], '2008-12-31'), ('2009-2019', '2009-01-01', '2019-12-31'), ('2009-Mar2023', '2009-01-01', MAIN[1])]:
    r_, n_ = ols(panel(D, NEW, a, b)); P(lab, fmt(r_, 'thr'), fmt(r_, 'cal_lw'), 'N', n_)
noc = lambda d: ~((d.index >= '2020-02-01') & (d.index <= '2020-05-31'))
r_, _ = ols(panel(D, NEW, *MAIN, mask=noc)); P('ex Feb-May 2020', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
ex2023 = lambda d: ~((d.index >= '2020-01-01'))
r_, _ = ols(panel(D, NEW, *MAIN, mask=ex2023)); P('ex 2020-Mar2023 (=1999-2019)', fmt(r_, 'thr'))
r_, _ = ols(panel(D, NEW, MAIN[0], END, mask=lambda d: ~((d.index >= '2020-01-01') & (d.index <= '2023-12-31')))); P('full to 2026 excl 2020-2023', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
r_, _ = ols(panel(D, NEW, MAIN[0], END)); P('full to Sep 2026, one coefficient', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
# rolling 4-year windows, ending each June/Dec
rows = []
for e in pd.date_range('2005-06-30', '2026-09-30', freq='6ME'):
    s = e - pd.DateOffset(years=4); r_, _ = ols(panel(D, NEW, s, e)); rows.append((e.date(), r_.loc['thr', 'b'], r_.loc['thr', 't']))
rr = pd.DataFrame(rows, columns=['end', 'b', 't']); P(rr.round(3).to_string()); rr.to_csv(os.path.join(HERE, 'rolling_own.csv'), index=False)
fr = pd.read_csv('fig2_rolling.csv'); P('repo fig2_rolling first/last:', fr.iloc[0].to_dict(), fr.iloc[-1].to_dict())
for m in ALL:
    for lab, a, b in [('1999-2008', MAIN[0], '2008-12-31'), ('2009-2019', '2009-01-01', '2019-12-31'), ('2020-Mar23', '2020-01-01', MAIN[1]), ('post', POST, END)]:
        try: r_, n_ = single(D, m, a, b); P('by market', m, lab, fmt(r_, 'thr'), fmt(r_, 'cal_lw'), n_)
        except Exception as ex: P('by market', m, lab, 'n/a')

P('=== Month-end / mechanism ===')
for w in (1, 2, 3):
    DD = {}
    for m in NEW:
        d = D[m].copy(); pos = pd.Series(1, index=d.index).groupby(d.index.to_period('M')).cumsum() - 1
        d['cal_lw'] = d.cal * ((pos >= 5 * (w - 1)) & (pos < 5 * w)); DD[m] = d
    r_, _ = ols(panel(DD, NEW, *MAIN)); P('placebo week', w, fmt(r_, 'cal_lw'))
for y_ in ('re1', 'rb1'):
    r_, _ = ols(panel(D, NEW, *MAIN, y=y_)); P('leg', y_, fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
for h in (1, 5, 10):
    DD = {m: D[m].assign(cum=sum(D[m].x.shift(-j) for j in range(1, h + 1))) for m in NEW}
    r_, _ = ols(panel(DD, NEW, *MAIN, y='cum').sort_index(), 'dk', lags=h + 5); P('LP h', h, fmt(r_, 'thr'), fmt(r_, 'cal_lw'))

P('=== Is Threshold short-term reversal? ===')
DL = {m: D[m].assign(**{f'x_l{k}': D[m].x.shift(k) for k in range(1, 6)}, re0=D[m].re, re_l1=D[m].re.shift(1)) for m in D}
r_, _ = ols(panel(DL, NEW, *MAIN, extra=tuple(f'x_l{k}' for k in range(1, 5)))); P('+ lags 1-4 (draft: 4 further)', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
r_, _ = ols(panel(DL, NEW, *MAIN, extra=tuple(f'x_l{k}' for k in range(1, 6)))); P('+ lags 1-5', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
r_, _ = ols(panel(DL, NEW, *MAIN, extra=('re0',))); P('+ current equity return', fmt(r_, 'thr'))
r_, _ = ols(panel(DL, NEW, *MAIN, extra=('re0', 're_l1'))); P('+ equity ret t, t-1', fmt(r_, 'thr'))
# cumulative 20-day excess return as a control (Threshold is a function of recent cumulative returns)
DL = {m: d.assign(c5=d.x.rolling(5).sum(), c20=d.x.rolling(20).sum()) for m, d in DL.items()}
r_, _ = ols(panel(DL, NEW, *MAIN, extra=('c5',))); P('+ 5-day cum return', fmt(r_, 'thr'))
r_, _ = ols(panel(DL, NEW, *MAIN, extra=('c5', 'c20'))); P('+ 5 & 20-day cum return', fmt(r_, 'thr'))
# reversal-only regressions (no signals) for comparison
r_, _ = ols(panel(DL, NEW, *MAIN, sig=('c5',), extra=())); P('5-day cum return alone (with controls)', fmt(r_, 'c5'))
for m in NEW: P('corr thr with 5d/20d cum', m, round(DL[m][['thr', 'c5']].corr().iloc[0, 1], 3), round(DL[m][['thr', 'c20']].corr().iloc[0, 1], 3))

P('=== Inference variants ===')
for se in ('hc1',):
    r_, _ = ols(panel(D, NEW, *MAIN), se); P('pooled HC1', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
for m in ALL:
    r1, _ = single(D, m, *MAIN, se='hc1'); P('single HC1', m, fmt(r1, 'thr'), fmt(r1, 'cal_lw'))
r_, _ = ols(panel(D, NEW, *MAIN).sort_index(), 'dk', lags=20); P('DK 20 lags', fmt(r_, 'thr'))

P('=== Outliers: winsorise y at 1/99% per market ===')
DW = {}
for m in D:
    d = D[m].copy(); lo, hi = d.y.loc[MAIN[0]:MAIN[1]].quantile([.01, .99]); d['y'] = d.y.clip(lo, hi); DW[m] = d
r_, _ = ols(panel(DW, NEW, *MAIN)); P('winsorised pooled', fmt(r_, 'thr'), fmt(r_, 'cal_lw'))
for m in NEW: r1, _ = single(DW, m, *MAIN); P('winsorised', m, fmt(r1, 'thr'), fmt(r1, 'cal_lw'))
# influence: drop the 10 largest |thr*resid| dates
Z = panel(D, NEW, *MAIN); r0, _ = ols(Z)
yv = Z['__y'].values; Xv = Z.drop(columns='__y'); u = yv - Xv.values @ r0.b.values
infl = pd.Series(np.abs(Z['thr'].values * u), index=Z.index).groupby(level=0).sum().sort_values(ascending=False)
for kdrop in (10, 25, 50):
    keep = ~Z.index.isin(infl.index[:kdrop]); r_, _ = ols(Z[keep]); P(f'drop {kdrop} most influential dates', fmt(r_, 'thr'))
P('top influential dates', [str(x.date()) for x in infl.index[:10]])

P('=== Band averaging ===')
for lab, bands in [('band 0 only', [0.0]), ('band 0.5%', [0.005]), ('band 1%', [0.01]), ('band 2%', [0.02]), ('band 2.5%', [0.025]), ('0-2% avg', np.arange(0, 21) / 1000)]:
    DD = {}
    for m in NEW + ['US']:
        d = make(m, bands=np.array(bands)); DD[m] = d
    DD = attach_us(DD)
    r_, _ = ols(panel(DD, NEW, *MAIN)); P(lab, fmt(r_, 'thr'))

P('=== Economic size ===')
for m in NEW + ['US']:
    s = D[m].loc[MAIN[0]:MAIN[1]].thr.dropna(); P('thr sd (pp)', m, round(s.std() * 100, 3), 'mean |thr| pp', round(s.abs().mean() * 100, 3))
sd = pd.concat([D[m].loc[MAIN[0]:MAIN[1]].thr for m in NEW]).std()
P('pooled: -0.321 * 1 sd =', round(-0.321 * sd * 1e4, 2), 'bp; per 1pp =', -0.321 * 0.01 * 1e4, 'bp')
for m in NEW:
    d = D[m].loc[MAIN[0]:MAIN[1]].dropna(subset=['thr', 'y']); pnl = -np.sign(d.thr) * d.y
    P('cost-free sign trade', m, 'ann ret %', round(pnl.mean() * 252 * 100, 2), 'Sharpe', round(pnl.mean() / pnl.std() * np.sqrt(252), 2))
    cost = (np.sign(d.thr).diff().abs().fillna(0) > 0) * 2 * 2e-4; pn2 = pnl - cost
    P('   after 1bp a leg per flip', round(pn2.mean() / pn2.std() * np.sqrt(252), 2), 'flips/yr', round((np.sign(d.thr).diff().abs() > 0).sum() / (len(d) / 252), 1))
    d2 = D[m].loc[POST:END].dropna(subset=['thr', 'y']); p2 = -np.sign(d2.thr) * d2.y; P('   post-Mar2023 cost-free Sharpe', round(p2.mean() / p2.std() * np.sqrt(252), 2))

P('=== Placebo: randomly shifted signal ===')
rng2 = np.random.default_rng(11); ts = []
base = panel(D, NEW, *MAIN)
for i in range(200):
    DD = {}
    for m in NEW:
        d = D[m].copy(); k = rng2.integers(250, len(d) - 250); d['thr'] = np.roll(d.thr.values, k); DD[m] = d
    r_, _ = ols(panel(DD, NEW, *MAIN)); ts.append(r_.loc['thr', 't'])
ts = np.array(ts); P('shift placebo: share |t|>=3.10:', np.mean(np.abs(ts) >= 3.0958), 'share t<=-3.10', np.mean(ts <= -3.0958), 'sd of t', round(ts.std(), 2), '95th |t|', round(np.quantile(np.abs(ts), .95), 2))
OUT.close()
