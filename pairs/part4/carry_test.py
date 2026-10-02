"""Signal test 8, interim (fixed 1 Oct 2026): currency and bond carry, 2013-2022. Credit part pending (FRED)."""
import pickle, numpy as np, pandas as pd
D = pickle.load(open('tsmom_data_ext.pkl', 'rb')); px = D['px'].ffill(); days = px.index
r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252)
o = pd.read_csv('msb/oecd_raw.csv'); o['TIME_PERIOD'] = pd.PeriodIndex(o.TIME_PERIOD, freq='M')
rate = o.pivot_table(index='TIME_PERIOD', columns='REF_AREA', values='OBS_VALUE')
FXMAP = {'Euro': 'EA20', 'Yen': 'JPN', 'Pound': 'GBR', 'Australian dollar': 'AUS', 'Canadian dollar': 'CAN'}
TY = pickle.load(open('msb/treasury.pkl', 'rb')).apply(pd.to_numeric, errors='coerce').ffill()
BOND = {'2y Treasury': '2 Yr', '10y Treasury': '10 Yr', '30y Treasury': '30 Yr'}
fr = [d for d in days if d.weekday() == 4 and pd.Timestamp('2011-06-01') <= d <= pd.Timestamp('2022-12-31')]
WF, WB = {}, {}
for d in fr:
    i = days.get_loc(d)
    if i + 1 >= len(days): continue
    m = d.to_period('M') - 1                                                        # last month's rate, already published
    if m not in rate.index: continue
    c = pd.Series({f: rate.loc[m, a] - rate.loc[m, 'USA'] for f, a in FXMAP.items()}).dropna().sort_values()
    wf = pd.Series(0.0, index=px.columns)
    if len(c) == 5:
        for f in c.index[-2:]: wf[f] = 0.10 / vol[f].iloc[i] / 4
        for f in c.index[:2]: wf[f] = -0.10 / vol[f].iloc[i] / 4
    prev = TY[TY.index < d]                                                         # yields known by the day before
    if len(prev):
        y = prev.iloc[-1]; bc = pd.Series({b: y[col] - y['3 Mo'] for b, col in BOND.items()}).dropna().sort_values()
        wb = pd.Series(0.0, index=px.columns)
        if len(bc) == 3:
            wb[bc.index[-1]] = 0.10 / vol[bc.index[-1]].iloc[i] / 2; wb[bc.index[0]] = -0.10 / vol[bc.index[0]].iloc[i] / 2
        WB[days[i + 1]] = wb
    WF[days[i + 1]] = wf
def sleeve(W):
    Wd = pd.DataFrame(W).T.reindex(days).ffill().fillna(0)[min(W):'2022-12-31']; R = r.reindex(Wd.index).fillna(0)
    g = (Wd.shift(1) * R).sum(axis=1); tv = Wd.diff().abs().sum(axis=1); return g - tv * 1e-4, g, tv
def scale(x):
    sv = x.rolling(126).std() * np.sqrt(252); sc = pd.Series(np.nan, index=x.index)
    for d in [d for d in x.index if d.weekday() == 4]:
        i = x.index.get_loc(d)
        if i + 1 < len(x) and np.isfinite(sv.iloc[i]) and sv.iloc[i] > 0: sc.iloc[i + 1] = 0.05 / sv.iloc[i]
    return (x * sc.ffill().shift(1)).dropna()
fx, fxg, fxt = sleeve(WF); bd, bdg, bdt = sleeve(WB)
comb = scale(pd.concat([scale(fx), scale(bd)], axis=1).dropna().mean(axis=1))
def st(s, a, b):
    s = s[a:b]; cum = (1 + s).cumprod()
    return dict(ret_pct=s.mean() * 252 * 100, sharpe=s.mean() / s.std() * np.sqrt(252), t=s.mean() / s.std() * np.sqrt(len(s)), max_dd_pct=(cum / cum.cummax() - 1).min() * 100)
P = [('2013-2022', '2013-01-01', '2022-12-31'), ('2013-2017', '2013-01-01', '2017-12-31'), ('2018-2022', '2018-01-01', '2022-12-31')]
out = {f'{lab} | {p}': st(s, a, b) for lab, s in [('Currencies + bonds (interim)', comb), ('Currencies only', scale(fx)), ('Bonds only', scale(bd))] for p, a, b in P}
T = pd.DataFrame(out).T; print(T.round(2).to_string())
for lab, g, t in [('currencies', fxg, fxt), ('bonds', bdg, bdt)]: print(f"breakeven {lab}: {g['2013':].sum() / t['2013':].sum() * 1e4:.1f}bp per trade")
T7 = pickle.load(open('msb/trend_dev_results.pkl', 'rb'))['xs']; print(f"correlation with futures trend, 2013-2022: {comb.corr(T7.reindex(comb.index)):.2f}")
pickle.dump(dict(T=T, comb=comb, fx=fx, bd=bd), open('msb/carry_results.pkl', 'wb'))
