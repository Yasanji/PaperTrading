"""Paper 2: pre-specified checks and economic significance, run once."""
import numpy as np, pandas as pd, statsmodels.api as sm, yfinance as yf
from local_data import build, bund, gilt, eq
from step2_main import S, fit, ivx_p, BASE
MAIN, HOLD = ('1999-01-01', '2023-03-17'), ('2023-03-20', '2026-09-30')
def build_etf(eq_px, bond_px):
    """Same signals as local_data.build, with bond returns taken from an ETF's total-return prices."""
    y = pd.Series(0.0, index=bond_px.index)                        # placeholder yield, carry switched off below
    d = build(eq_px, y, 'zero', carry=False)
    rb = bond_px.pct_change().reindex(d.index)
    return build_from(eq_px.reindex(d.index), rb)
def build_from(px, rb):
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
def local_test(d, label):
    out = []
    for per, (a, b) in (('main', MAIN), ('hold-out', HOLD)):
        x = d.loc[a:b].dropna()
        if len(x) < 250: continue
        f = fit(x, BASE)
        for s in ('thr', 'calw4'):
            out.append(dict(check=label, period=per, start=str(x.index[0].date()), signal=s, coef=round(f.params[s], 3), t_nw=round(f.tvalues[s], 2), ivx_p=round(ivx_p(x, s, BASE)[1], 3), N=int(f.nobs)))
    return out
rows = []
by = bund(); rows += local_test(build(eq('^GDAXIP'), by, 'zero'), 'Germany, DAX price index')
rows += local_test(build(eq('^STOXX50E'), by, 'zero'), 'EURO STOXX 50 with Bund')
dax, ftse = eq('^GDAXI'), eq('^FTSE')
rows += local_test(build_from(dax, eq('EXX6.DE').pct_change()), 'Germany, bond ETF (EXX6)')
rows += local_test(build_from(ftse, eq('IGLT.L').pct_change()), 'UK, gilt ETF (IGLT)')
C = pd.DataFrame(rows); pd.set_option('display.width', 200); print(C.to_string(index=False)); C.to_pickle('step4_checks.pkl')
# Threshold error-correction model with the band estimated (secondary): grid over single bands, regime split, fixed-regressor bootstrap for linearity
def single_band(d, delta):
    re, rb, n = d.re.values, d.rb.values, len(d); w, s = 0.6, np.empty(n)
    for t in range(n):
        w = w * (1 + re[t]) / (w * (1 + re[t]) + (1 - w) * (1 + rb[t])); s[t] = w - 0.6
        if abs(w - 0.6) > delta: w = 0.6
    return pd.Series(s, index=d.index)
rng = np.random.default_rng(11)
for mkt in ('DE', 'UK'):
    d = S[mkt].loc[MAIN[0]:MAIN[1]].dropna(); ctrl = sm.add_constant(d[['calw4', 'xa0', 'xa1', 'xa2', 'xa3', 'xa4', 'mom']]).values; best = None; stats_ = []
    for delta in np.arange(0.0025, 0.02501, 0.0025):
        s = single_band(d, delta).values; out = np.abs(s) >= delta
        X1 = np.column_stack([ctrl, s]); X2 = np.column_stack([ctrl, s * out, s * ~out])
        ssr1 = np.sum((d.y_next.values - X1 @ np.linalg.lstsq(X1, d.y_next.values, rcond=None)[0]) ** 2)
        b2 = np.linalg.lstsq(X2, d.y_next.values, rcond=None)[0]; ssr2 = np.sum((d.y_next.values - X2 @ b2) ** 2)
        F = (ssr1 - ssr2) / (ssr2 / (len(d) - X2.shape[1])); stats_.append((delta, F, b2[-2], b2[-1], X1, X2))
        if best is None or F > best[1]: best = (delta, F, b2[-2], b2[-1])
    e = d.y_next.values - d.y_next.mean(); supF = []
    for _ in range(199):
        ys = e * rng.standard_normal(len(e)); mx = 0
        for delta, F, _, _, X1, X2 in stats_:
            s1 = np.sum((ys - X1 @ np.linalg.lstsq(X1, ys, rcond=None)[0]) ** 2); s2 = np.sum((ys - X2 @ np.linalg.lstsq(X2, ys, rcond=None)[0]) ** 2)
            mx = max(mx, (s1 - s2) / (s2 / (len(ys) - X2.shape[1])))
        supF.append(mx)
    p = (np.sum(np.array(supF) >= best[1]) + 1) / 200
    print(f'{mkt} threshold model: estimated band {best[0]*100:.2f}% | adjustment outside the band {best[2]:.3f}, inside {best[3]:.3f} | sup-F {best[1]:.2f}, bootstrap p {p:.3f}')
# Economic significance: positions as in Harvey, Mazzoleni and Melone, 1 basis point a trade on each leg
def strategy(d):
    cal_pos = np.where(d.week4 > 0, -np.sign(d.cal), 0.0); thr_pos = np.clip(-d.thr / 0.015, -1, 1)
    res = {}
    for name, pos in (('Calendar', pd.Series(cal_pos, d.index)), ('Threshold', pd.Series(thr_pos, d.index)), ('Combined', pd.Series((cal_pos + thr_pos) / 2, d.index))):
        gross = pos * d.y_next; cost = pos.diff().abs().fillna(0) * 2 * 1e-4; net = (gross - cost).dropna()
        res[name] = dict(ret_pct=net.mean() * 252 * 100, vol_pct=net.std() * np.sqrt(252) * 100, sharpe=net.mean() / net.std() * np.sqrt(252), turnover=pos.diff().abs().sum() / (len(pos) / 252))
    return res
print('\nEconomic significance (net of 1 basis point a trade on each leg):')
E = []
for mkt in ('DE', 'UK'):
    for per, (a, b) in (('main', MAIN), ('hold-out', HOLD)):
        for k, v in strategy(S[mkt].loc[a:b].dropna(subset=['y_next'])).items(): E.append(dict(market=mkt, period=per, strategy=k, **{x: round(y, 2) for x, y in v.items()}))
E = pd.DataFrame(E); print(E.to_string(index=False)); E.to_pickle('step4_strategy.pkl')
