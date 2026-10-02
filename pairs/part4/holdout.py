"""Hold-out run (fixed 2 Oct 2026): futures trend, development rules unchanged, 2023-01-01 to latest. Run once."""
import pickle, numpy as np, pandas as pd
D = pickle.load(open('tsmom_data_ext.pkl', 'rb')); px = D['px'].ffill(); days = px.index
r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252)
W = {}
for d in [d for d in days if d.weekday() == 4 and d >= pd.Timestamp('2021-06-01')]:
    i = days.get_loc(d)
    if i + 1 >= len(days): continue
    sig = np.sign(px.iloc[i] / px.iloc[i - 252] - 1); W[days[i + 1]] = (0.10 / vol.iloc[i] * sig / px.shape[1]).fillna(0)
Wd = pd.DataFrame(W).T.reindex(days).ffill().fillna(0)[min(W):]
R = r.reindex(Wd.index).fillna(0); x = (Wd.shift(1) * R).sum(axis=1) - Wd.diff().abs().sum(axis=1) * 1e-4
def scale(s):
    sv = s.rolling(126).std() * np.sqrt(252); sc = pd.Series(np.nan, index=s.index)
    for d in [d for d in s.index if d.weekday() == 4]:
        i = s.index.get_loc(d)
        if i + 1 < len(s) and np.isfinite(sv.iloc[i]) and sv.iloc[i] > 0: sc.iloc[i + 1] = 0.05 / sv.iloc[i]
    return (s * sc.ffill().shift(1)).dropna()
trend = scale(x)['2023-01-01':]
def st(s):
    c = (1 + s).cumprod(); m = s.resample('ME').apply(lambda z: (1 + z).prod() - 1)
    return dict(start=str(s.index[0].date()), end=str(s.index[-1].date()), ret_pct=s.mean() * 252 * 100, vol_pct=s.std() * np.sqrt(252) * 100,
                sharpe=s.mean() / s.std() * np.sqrt(252), t=s.mean() / s.std() * np.sqrt(len(s)), max_dd_pct=(c / c.cummax() - 1).min() * 100,
                worst_month_pct=m.min() * 100, cum_pct=(c.iloc[-1] - 1) * 100)
out = {'Hold-out book: futures trend': st(trend)}
by_year = {y: ((1 + g).prod() - 1) * 100 for y, g in trend.groupby(trend.index.year)}
# comparison, labelled: trend plus the Part 2 STOXX 600 ten-pair sleeve at equal risk, over the shared period
O = pickle.load(open('results_600.pkl', 'rb')); pairs = scale(O[10]['pa'].pair_net)
both = pd.concat([scale(x), pairs], axis=1, join='inner').dropna(); both.columns = ['trend', 'pairs']
combo = scale(both.mean(axis=1)); a = max(trend.index[0], combo.index[0])
out['Comparison only: trend + pairs, equal risk'] = st(combo[a:])
out['Comparison only: trend alone, same dates'] = st(trend[a:])
T = pd.DataFrame(out).T; pd.set_option('display.width', 220); print(T.round(2).to_string())
print('\ntrend by calendar year, %:', {k: round(v, 1) for k, v in by_year.items()})
print('correlation trend vs pairs (shared period):', round(both.trend[a:].corr(both.pairs[a:]), 2))
print('PASS CRITERION (positive return after costs):', 'PASS' if out['Hold-out book: futures trend']['ret_pct'] > 0 else 'FAIL')
pickle.dump(dict(T=T, trend=trend, combo=combo, by_year=by_year), open('msb/holdout_results.pkl', 'wb'))
