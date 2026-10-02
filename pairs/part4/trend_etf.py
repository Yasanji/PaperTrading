"""Robustness check: the trend rules unchanged, on ETFs tracking the same 15 markets (no roll jumps; commodity ETFs carry real roll costs)."""
import numpy as np, pandas as pd, yfinance as yf, pickle, warnings; warnings.filterwarnings('ignore')
MAP = {'S&P 500': 'SPY', 'Nasdaq-100': 'QQQ', '2y Treasury': 'SHY', '10y Treasury': 'IEF', '30y Treasury': 'TLT', 'WTI crude': 'USO',
       'Natural gas': 'UNG', 'Gold': 'GLD', 'Silver': 'SLV', 'Copper': 'CPER', 'Euro': 'FXE', 'Yen': 'FXY', 'Pound': 'FXB',
       'Australian dollar': 'FXA', 'Canadian dollar': 'FXC'}
px = yf.download(list(MAP.values()), start='2004-01-01', end='2026-09-26', auto_adjust=True, progress=False)['Close']
px.columns = [{v: k for k, v in MAP.items()}[c] for c in px.columns]; days = px.index
r = px.pct_change(fill_method=None); vol = r.rolling(63).std() * np.sqrt(252)
W = {}
for d in [d for d in days if d.weekday() == 4 and d >= pd.Timestamp('2005-06-01')]:
    i = days.get_loc(d)
    if i + 1 >= len(days) or i < 252: continue
    sig = np.sign(px.iloc[i] / px.iloc[i - 252] - 1); n = int(sig.notna().sum())
    if n == 0: continue
    W[days[i + 1]] = (0.10 / vol.iloc[i] * sig / n).fillna(0)
Wd = pd.DataFrame(W).T.reindex(days).ffill().fillna(0)[min(W):]
x = (Wd.shift(1) * r.reindex(Wd.index).fillna(0)).sum(axis=1) - Wd.diff().abs().sum(axis=1) * 1e-4
sv = x.rolling(126).std() * np.sqrt(252); sc = pd.Series(np.nan, index=x.index)
for d in [d for d in x.index if d.weekday() == 4]:
    i = x.index.get_loc(d)
    if i + 1 < len(x) and np.isfinite(sv.iloc[i]) and sv.iloc[i] > 0: sc.iloc[i + 1] = 0.05 / sv.iloc[i]
xs = (x * sc.ffill().shift(1)).dropna()
F = pickle.load(open('msb/trend_dev_results.pkl', 'rb'))['xs']; P = pickle.load(open('msb/pre_trend.pkl', 'rb'))['xs']; H = pickle.load(open('msb/holdout_results.pkl', 'rb'))['trend']
fut = pd.concat([P['2008':'2012'], F['2013':'2022'], H['2023':]])
def st(s):
    c = (1 + s).cumprod(); return f"{s.mean() * 252 * 100:5.1f}%  Sharpe {s.mean() / s.std() * np.sqrt(252):5.2f}  maxDD {(c / c.cummax() - 1).min() * 100:6.1f}%"
for lab, a, b in [('Crisis years 2008-2012', '2008-01-01', '2012-12-31'), ('Development 2013-2022', '2013-01-01', '2022-12-31'), ('Hold-out 2023-2026', '2023-01-01', '2026-12-31')]:
    print(f'{lab:24s} futures: {st(fut[a:b])}   |   ETFs: {st(xs[a:b])}')
both = pd.concat([fut, xs], axis=1, join='inner').dropna(); print('daily correlation, futures vs ETF versions:', round(both.corr().iloc[0, 1], 2))
print('ETF first dates:', {k: str(px[k].first_valid_index().date()) for k in ['Copper', 'Natural gas', 'Yen']})
pickle.dump(dict(xs=xs), open('msb/trend_etf.pkl', 'wb'))
