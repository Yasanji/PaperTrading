"""Paper 2, Step 1: replicate Harvey, Mazzoleni and Melone (Table 1, column 1) on the S&P 500 index and 10-year Treasury yields.
Downloads its own data. Threshold signal: average over bands from 0% to 2.5% in 0.1-point steps, as in their equation (2)."""
import io, requests, numpy as np, pandas as pd, statsmodels.api as sm, yfinance as yf
def treasury_10y(first=1997, last=2023):
    fr = []
    for y in range(first, last + 1):
        u = (f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all'
             f'?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv')
        r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        if r.status_code == 200 and 'Date' in r.text[:40]: fr.append(pd.read_csv(io.StringIO(r.text))[['Date', '10 Yr']])
    t = pd.concat(fr); t['Date'] = pd.to_datetime(t.Date); return t.set_index('Date').sort_index()['10 Yr'].astype(float)
spx = yf.download('^GSPC', start='1996-01-01', end='2023-03-31', progress=False, auto_adjust=True)['Close'].squeeze().dropna()
y = treasury_10y() / 100
d = pd.concat([spx.rename('px'), y.rename('y')], axis=1, join='inner').dropna()
def par_price(c, yy, n=20):                                     # semi-annual par bond, 10 years
    i = np.arange(1, n + 1); return (c / 2 * (1 + yy / 2) ** -i).sum() + (1 + yy / 2) ** -n
d['re'] = d.px.pct_change()
d['rb'] = [np.nan] + [par_price(d.y.iloc[k - 1], d.y.iloc[k]) - 1 for k in range(1, len(d))]   # price return of yesterday's par bond
d = d.dropna(); d['xa'] = d.re - d.rb
re, rb = d.re.values, d.rb.values; n = len(d)
def drift(w, a, b): return w * (1 + a) / (w * (1 + a) + (1 - w) * (1 + b))
def threshold(delta):
    w, s = 0.6, np.empty(n)
    for t in range(n):
        w = drift(w, re[t], rb[t]); s[t] = w - 0.6
        if abs(w - 0.6) > delta: w = 0.6
    return s
deltas = np.arange(0, 0.02501, 0.001)                           # 0% to 2.5% in 0.1-point steps, as in the paper's equation (2)
d['thr'] = np.mean([threshold(x) for x in deltas], axis=0)
mend = d.index.to_series().groupby(d.index.to_period('M')).transform('max') == d.index.to_series()
w, cal = 0.6, np.empty(n)
for t in range(n):
    w = drift(w, re[t], rb[t]); cal[t] = w - 0.6
    if mend.iloc[t]: w = 0.6
d['cal'] = cal
pos = d.index.to_series().groupby(d.index.to_period('M')).cumcount(ascending=False)
d['week4'] = (pos < 5).astype(float); d['calw4'] = d.cal * d.week4
cum = d.xa.cumsum()
med = np.mean([np.sign(cum - cum.shift(h)) for h in range(11, 21)], axis=0)
slow = np.mean([np.sign(cum - cum.shift(h)) for h in (21, 42, 63, 126, 252)], axis=0)
d['mom'] = (med + slow) / 2; d['ret'] = d.xa; d['y_next'] = d.xa.shift(-1)
s = d.loc['1997-09-10':'2023-03-17'].dropna()
X = sm.add_constant(s[['thr', 'cal', 'week4', 'calw4', 'mom', 'ret']]); m = sm.OLS(s.y_next, X).fit(cov_type='HC1')
pub = {'thr': (-0.4144, 0.1148), 'cal': (0.0553, 0.0709), 'week4': (0.0002, 0.0004), 'calw4': (-0.3029, 0.0808), 'mom': (0.0023, 0.0006), 'ret': (-0.0203, 0.0289)}
print(f"{'':10s}{'ours':>10s}{'(se)':>10s}{'published':>12s}{'(se)':>10s}")
for k, (b, se) in pub.items(): print(f'{k:10s}{m.params[k]:10.4f}{m.bse[k]:10.4f}{b:12.4f}{se:10.4f}')
print(f'observations {int(m.nobs)} (published 6,226) | adjusted R2 {m.rsquared_adj:.4f} (published 0.0239)')
