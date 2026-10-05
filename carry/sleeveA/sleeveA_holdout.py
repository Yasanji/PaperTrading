"""Sleeve A (G10 currency carry): hold-out, January 2013 to September 2026, run once."""
import io, requests, numpy as np, pandas as pd, statsmodels.api as sm
fx = pd.read_pickle('boe_fx.pkl').set_index('DATE').sort_index()
gbp = {'USD': 'XUDLUSS', 'EUR': 'XUDLERS', 'JPY': 'XUDLJYS', 'CHF': 'XUDLSFS', 'CAD': 'XUDLCDS', 'AUD': 'XUDLADS', 'NZD': 'XUDLNDS', 'SEK': 'XUDLSKS', 'NOK': 'XUDLNKS'}
f = fx[list(gbp.values())].apply(pd.to_numeric, errors='coerce').dropna(subset=['XUDLUSS'])
usd = pd.DataFrame({k: f['XUDLUSS'] / f[v] for k, v in gbp.items() if k != 'USD'})
o = pd.read_pickle('oecd_rates.pkl'); o = o[o.MEASURE == 'IR3TIB']
area = {'USA': 'USD', 'EA20': 'EUR', 'JPN': 'JPY', 'GBR': 'GBP', 'CHE': 'CHF', 'CAN': 'CAD', 'AUS': 'AUD', 'NZL': 'NZD', 'SWE': 'SEK', 'NOR': 'NOK'}
r = o[o.REF_AREA.isin(area)].pivot_table(index='TIME_PERIOD', columns='REF_AREA', values='OBS_VALUE').rename(columns=area) / 100
r.index = pd.PeriodIndex(r.index, freq='M')
u = ('https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2026&Dateto=now&SeriesCodes=IUDSOIA&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N')
so = pd.read_csv(io.StringIO(requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60).text)); so['DATE'] = pd.to_datetime(so.DATE, format='%d %b %Y')
sonia = so.set_index('DATE').IUDSOIA.groupby(lambda d: d.to_period('M')).mean() / 100
r = r.reindex(pd.period_range(r.index.min(), '2026-10', freq='M'))
for p in sonia.index:
    if p > pd.Period('2026-02', 'M') and p in r.index: r.loc[p, 'GBP'] = sonia[p]
r = r.ffill(limit=1)
CCY = list(usd.columns)
d = usd.loc['2012-06':'2026-09'].dropna(how='all'); dret = d.pct_change()
mend = d.groupby(d.index.to_period('M')).tail(1).index
prev = pd.Series(0.0, index=CCY); daily, cost = [], {}
for i, t in enumerate(mend[:-1]):
    p = t.to_period('M'); carry = (r.loc[p - 1, CCY] - r.loc[p - 1, 'USD']).dropna()
    vol = dret.loc[:t].iloc[-63:][carry.index].std() * np.sqrt(252); carry = carry[vol.notna() & (vol > 0)]
    if len(carry) < 6: continue
    hi, lo = carry.nlargest(3).index, carry.nsmallest(3).index
    w = pd.Series(0.0, index=CCY); w[hi] = (1 / vol[hi]) / (1 / vol[hi]).sum(); w[lo] = -(1 / vol[lo]) / (1 / vol[lo]).sum()
    nxt = mend[i + 1]; hold = dret.loc[t:nxt].iloc[1:]; q = nxt.to_period('M'); diff = (r.loc[q, CCY] - r.loc[q, 'USD']).fillna(0)
    daily.append(hold[CCY].fillna(0).mul(w).sum(axis=1) + (w * diff).sum() / 252); cost[hold.index[0]] = 2e-4 * (w - prev).abs().sum(); prev = w
raw = pd.concat(daily); raw.loc[list(cost)] -= pd.Series(cost)
lev = (0.05 / (raw.rolling(126).std() * np.sqrt(252))).shift(1); lev = lev.groupby(lev.index.to_period('M')).transform('first')
s = (raw * lev).dropna().loc['2013-01-01':'2026-09-30']
m = sm.OLS(s.values, np.ones(len(s))).fit(cov_type='HAC', cov_kwds={'maxlags': 10})
print(f"hold-out: return {s.mean()*252*100:.2f}% a year, vol {s.std()*np.sqrt(252)*100:.1f}%, Sharpe {s.mean()/s.std()*np.sqrt(252):.2f}, Newey-West t {m.tvalues[0]:.2f}")
print('by year, %:', (s.groupby(s.index.year).sum() * 100).round(1).to_dict())
