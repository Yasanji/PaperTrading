"""Sleeve A: diversification test against trend (rules of pairs/part4/trend_dev.py), development overlap only."""
import numpy as np, pandas as pd, yfinance as yf
tick = ['ES=F', 'NQ=F', 'ZT=F', 'ZN=F', 'ZB=F', 'CL=F', 'NG=F', 'GC=F', 'SI=F', 'HG=F', '6E=F', '6J=F', '6B=F', '6A=F', '6C=F']
px = yf.download(tick, start='2004-01-01', end='2013-01-10', progress=False, auto_adjust=True)['Close'].ffill(); days = px.index
r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252)
W = {}
for d in [d for d in days if d.weekday() == 4 and pd.Timestamp('2005-01-01') <= d <= pd.Timestamp('2012-12-31')]:
    i = days.get_loc(d)
    if i + 1 >= len(days) or i < 252: continue
    W[days[i + 1]] = (0.10 / vol.iloc[i] * np.sign(px.iloc[i] / px.iloc[i - 252] - 1) / px.shape[1]).fillna(0)
Wd = pd.DataFrame(W).T.reindex(days).ffill().fillna(0)[min(W):'2012-12-31']; R = r.reindex(Wd.index).fillna(0)
x = (Wd.shift(1) * R).sum(axis=1) - Wd.diff().abs().sum(axis=1) * 1e-4
sv = x.rolling(126).std() * np.sqrt(252); sc = pd.Series(np.nan, index=x.index)
for d in [d for d in x.index if d.weekday() == 4]:
    i = x.index.get_loc(d)
    if i + 1 < len(x) and np.isfinite(sv.iloc[i]) and sv.iloc[i] > 0: sc.iloc[i + 1] = 0.05 / sv.iloc[i]
trend = (x * sc.ffill().shift(1)).dropna()
j = pd.concat([trend.rename('trend'), pd.read_pickle('sleeveA_dev_daily.pkl').rename('carry')], axis=1).dropna().loc['2005-07-01':'2012-12-31']
mo = (1 + j).resample('ME').prod() - 1; sh = lambda s: s.mean() / s.std() * np.sqrt(252)
comb = 0.5 * j.trend / j.trend.std() + 0.5 * j.carry / j.carry.std()
print(f"monthly correlation {mo.trend.corr(mo.carry):.2f} | Sharpe trend {sh(j.trend):.2f}, carry {sh(j.carry):.2f}, combined {sh(comb):.2f}")
