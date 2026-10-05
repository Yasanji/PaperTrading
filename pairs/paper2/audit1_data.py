import numpy as np, pandas as pd, yfinance as yf, warnings; warnings.filterwarnings('ignore')
from local_data import bund, gilt, eq, ust
S = pd.read_pickle('local_signals.pkl')
print('== (a) largest daily moves, as a check for bad data points')
for m in ('DE', 'UK', 'US'):
    d = S[m]
    for col in ('re', 'rb'):
        top = d[col].abs().sort_values(ascending=False).head(4)
        print(f'  {m} {col}: ' + ', '.join(f'{i.date()} {d.loc[i, col]*100:+.1f}%' for i in top.index))
print('\n== (b) days lost when equity and bond dates are joined, overall and in the last week of a month')
src = {'DE': (eq('^GDAXI'), bund()), 'UK': (eq('^FTSE'), gilt()), 'US': (eq('^GSPC'), ust() if False else None)}
for m in ('DE', 'UK'):
    e, y = src[m]; e = e.loc['1999':'2026-09']; y = y.loc['1999':'2026-09']
    only_e, only_y = e.index.difference(y.index), y.index.difference(e.index)
    print(f'  {m}: equity days without a yield {len(only_e)}, yield days without equity {len(only_y)}')
print('\n== (c) month-ends: months whose last joined date is not the last weekday of the month')
for m in ('DE', 'UK'):
    d = S[m].loc['1999':'2026-09']; last = d.index.to_series().groupby(d.index.to_period('M')).max()
    lastwk = pd.Series({p: pd.date_range(p.start_time, p.end_time, freq='B')[-1] for p in last.index})
    diff = last[last.values != lastwk.reindex(last.index).values]
    print(f'  {m}: {len(diff)} of {len(last)} months; examples: ' + ', '.join(str(pd.Timestamp(x).date()) for x in diff.values[:8]))
print('\n== (d) bond returns from yields against bond ETF total returns (correlation, slope)')
for m, tk in (('DE', 'EXX6.DE'), ('UK', 'IGLT.L')):
    r = eq(tk).pct_change(); z = pd.concat([S[m].rb, r.rename('etf')], axis=1).dropna().loc['2009':]
    for a, b in (('2009', '2016'), ('2017', '2026')):
        w = z.loc[a:b]; print(f'  {m} {a}-{b}: correlation {w.corr().iloc[0, 1]:.2f}, ETF return per unit of ours {np.polyfit(w.rb, w.etf, 1)[0]:.2f}')
print('\n== (e) Bund compounding: annual (used) against continuous')
y = bund(); y = y.loc['1997':]; ann = ((1 + y.shift(1)) / (1 + y)) ** 10 - 1; cont = np.exp(-10 * (y - y.shift(1))) - 1
w = pd.concat([ann, cont], axis=1).dropna(); print(f'  correlation {w.corr().iloc[0,1]:.5f}; mean absolute difference {(w.iloc[:,0]-w.iloc[:,1]).abs().mean()*1e4:.2f} bp a day')
print('\n== (f) UK dividends: FTSE 100 price index against a total-return proxy (ISF.L, iShares Core FTSE 100)')
tr = yf.download('ISF.L', start='1999-01-01', end='2026-10-01', progress=False, auto_adjust=True)['Close'].squeeze().dropna()
px = yf.download('ISF.L', start='1999-01-01', end='2026-10-01', progress=False, auto_adjust=False)['Close'].squeeze().dropna()
print(f'  ISF.L from {tr.index[0].date()}')
div = (tr.pct_change() - px.pct_change()).dropna(); div = div[div.abs() > 1e-6]
pos = pd.Series(np.arange(len(S["UK"])), index=S['UK'].index); w4 = S['UK'].week4.reindex(div.index).fillna(0)
print(f'  ex-dividend days found {len(div)}; share falling in the last week of a month {w4.mean():.2f} (last week is about {S["UK"].week4.mean():.2f} of days)')
print(f'  average dividend on those days {div.mean()*100:.2f}%; total a year about {div.groupby(div.index.year).sum().mean()*100:.2f}%')
pd.to_pickle(dict(isf_tr=tr), 'audit_isf.pkl')
