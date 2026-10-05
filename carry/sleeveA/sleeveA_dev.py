"""Sleeve A (G10 currency carry): development period only, 2000-2012, as in PREREGISTRATION.md."""
import numpy as np, pandas as pd, statsmodels.api as sm
fx = pd.read_pickle('boe_fx.pkl').set_index('DATE').sort_index()
gbp = {'USD': 'XUDLUSS', 'EUR': 'XUDLERS', 'JPY': 'XUDLJYS', 'CHF': 'XUDLSFS', 'CAD': 'XUDLCDS', 'AUD': 'XUDLADS', 'NZD': 'XUDLNDS', 'SEK': 'XUDLSKS', 'NOK': 'XUDLNKS'}
f = fx[[c for c in gbp.values()]].apply(pd.to_numeric, errors='coerce').dropna(subset=['XUDLUSS'])
usd = pd.DataFrame({k: f['XUDLUSS'] / f[v] for k, v in gbp.items() if k != 'USD'})
o = pd.read_pickle('oecd_rates.pkl'); o = o[o.MEASURE == 'IR3TIB']
area = {'USA': 'USD', 'EA20': 'EUR', 'JPN': 'JPY', 'GBR': 'GBP', 'CHE': 'CHF', 'CAN': 'CAD', 'AUS': 'AUD', 'NZL': 'NZD', 'SWE': 'SEK', 'NOR': 'NOK'}
r = o[o.REF_AREA.isin(area)].pivot_table(index='TIME_PERIOD', columns='REF_AREA', values='OBS_VALUE').rename(columns=area) / 100
r.index = pd.PeriodIndex(r.index, freq='M')
CCY = list(usd.columns)
d = usd.loc['1999-06':'2012-12'].dropna(how='all'); dret = d.pct_change()
mend = d.groupby(d.index.to_period('M')).tail(1).index
prev = pd.Series(0.0, index=CCY); daily, cost = [], {}
for i, t in enumerate(mend[:-1]):
    p = t.to_period('M')
    carry = (r.loc[p - 1, CCY] - r.loc[p - 1, 'USD']).dropna()
    vol = dret.loc[:t].iloc[-63:][carry.index].std() * np.sqrt(252)
    carry = carry[vol.notna() & (vol > 0)]
    if len(carry) < 6: continue
    hi, lo = carry.nlargest(3).index, carry.nsmallest(3).index
    w = pd.Series(0.0, index=CCY)
    w[hi] = (1 / vol[hi]) / (1 / vol[hi]).sum(); w[lo] = -(1 / vol[lo]) / (1 / vol[lo]).sum()
    nxt = mend[i + 1]; hold = dret.loc[t:nxt].iloc[1:]
    q = nxt.to_period('M'); diff = (r.loc[q, CCY] - r.loc[q, 'USD']).fillna(0)
    daily.append(hold[CCY].fillna(0).mul(w).sum(axis=1) + (w * diff).sum() / 252)
    cost[hold.index[0]] = 2e-4 * (w - prev).abs().sum(); prev = w
raw = pd.concat(daily); raw.loc[list(cost)] -= pd.Series(cost)
lev = (0.05 / (raw.rolling(126).std() * np.sqrt(252))).shift(1)
lev = lev.groupby(lev.index.to_period('M')).transform('first')
s = (raw * lev).dropna().loc['2000-01-01':'2012-12-31']
def stats(x):
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type='HAC', cov_kwds={'maxlags': 10})
    return dict(ret=x.mean() * 252 * 100, vol=x.std() * np.sqrt(252) * 100, sharpe=x.mean() / x.std() * np.sqrt(252), t_nw=m.tvalues[0])
for k, v in {'2000-2012': stats(s), '2000-2006': stats(s.loc[:'2006']), '2007-2012': stats(s.loc['2007':])}.items():
    print(f"{k}: return {v['ret']:.2f}% a year, vol {v['vol']:.1f}%, Sharpe {v['sharpe']:.2f}, Newey-West t {v['t_nw']:.2f}")
s.to_pickle('sleeveA_dev_daily.pkl')
