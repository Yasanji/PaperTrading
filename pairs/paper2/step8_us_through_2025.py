"""Paper 2, Step 8 (exploratory, not pre-registered; specified and committed 8 October 2026 before it was run).

Question: Harvey, Mazzoleni and Melone (working paper, 14 January 2026, footnote 32) state that extending their sample
"through 2025" makes the results "even stronger". Our US hold-out (20 March 2023 to 30 September 2026) found no effect.
This step checks whether the difference comes from the period or from the data.

Equation: Step 1 (their Table 1, column 1): next-day equity-minus-bond return on Threshold, Calendar, last-week
indicator, Calendar x last week, momentum and the current return; HC1 and Newey-West (9 lags) t-statistics.
Data, three versions, each with signals rebuilt from its own returns:
  A. S&P 500 index and 10-year Treasury par-yield returns (as Step 1 and the hold-out)
  B. S&P 500 and 10-year note front-month futures (Yahoo ES=F, ZN=F, unadjusted, from late 2000; roll days kept)
  C. Total-return ETFs SPY and IEF (from August 2002)
Periods: their sample (10 Sep 1997 to 17 Mar 2023, trimmed to data start), their extension (20 Mar 2023 to 31 Dec 2025),
1997 to 2025 combined, and our hold-out (20 Mar 2023 to 30 Sep 2026)."""
import io, requests, numpy as np, pandas as pd, statsmodels.api as sm, yfinance as yf

def treasury_10y(first=1996, last=2026):
    fr = []
    for y in range(first, last + 1):
        u = (f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all'
             f'?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv')
        r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        if r.status_code == 200 and 'Date' in r.text[:40]: fr.append(pd.read_csv(io.StringIO(r.text))[['Date', '10 Yr']])
    t = pd.concat(fr); t['Date'] = pd.to_datetime(t.Date); return t.set_index('Date').sort_index()['10 Yr'].astype(float) / 100

def par_price(c, yy, n=20):
    i = np.arange(1, n + 1); return (c / 2 * (1 + yy / 2) ** -i).sum() + (1 + yy / 2) ** -n

def signals(re, rb):
    d = pd.DataFrame(dict(re=re, rb=rb)).dropna(); d['xa'] = d.re - d.rb
    a, b, n = d.re.values, d.rb.values, len(d)
    drift = lambda w, x, y: w * (1 + x) / (w * (1 + x) + (1 - w) * (1 + y))
    def thr(delta):
        w, s = 0.6, np.empty(n)
        for t in range(n):
            w = drift(w, a[t], b[t]); s[t] = w - 0.6
            if abs(w - 0.6) > delta: w = 0.6
        return s
    d['thr'] = np.mean([thr(x) for x in np.arange(0, 0.02501, 0.001)], axis=0)
    idx = d.index.to_series(); mend = idx.groupby(d.index.to_period('M')).transform('max') == idx
    w, cal = 0.6, np.empty(n)
    for t in range(n):
        w = drift(w, a[t], b[t]); cal[t] = w - 0.6
        if mend.iloc[t]: w = 0.6
    d['cal'] = cal
    d['week4'] = (idx.groupby(d.index.to_period('M')).cumcount(ascending=False) < 5).astype(float); d['calw4'] = d.cal * d.week4
    cum = d.xa.cumsum()
    med = np.mean([np.sign(cum - cum.shift(h)) for h in range(11, 21)], axis=0)
    slow = np.mean([np.sign(cum - cum.shift(h)) for h in (21, 42, 63, 126, 252)], axis=0)
    d['mom'] = (med + slow) / 2; d['ret'] = d.xa; d['y_next'] = d.xa.shift(-1)
    return d

def fit(d, a, b):
    s = d.loc[a:b].dropna(); X = sm.add_constant(s[['thr', 'cal', 'week4', 'calw4', 'mom', 'ret']])
    hc = sm.OLS(s.y_next, X).fit(cov_type='HC1'); nw = sm.OLS(s.y_next, X).fit(cov_type='HAC', cov_kwds=dict(maxlags=9))
    return dict(N=int(hc.nobs), start=s.index[0].date(), end=s.index[-1].date(),
                thr=hc.params.thr, thr_t=hc.tvalues.thr, thr_tnw=nw.tvalues.thr,
                calw4=hc.params.calw4, calw4_t=hc.tvalues.calw4, calw4_tnw=nw.tvalues.calw4)

if __name__ == '__main__':
    px = yf.download(['^GSPC', 'ES=F', 'ZN=F', 'SPY', 'IEF'], start='1996-01-01', end='2026-10-01', progress=False, auto_adjust=True)['Close']
    y = treasury_10y()
    A = pd.concat([px['^GSPC'].rename('px'), y.rename('y')], axis=1, join='inner').dropna()
    rbA = pd.Series([np.nan] + [par_price(A.y.iloc[k - 1], A.y.iloc[k]) - 1 for k in range(1, len(A))], index=A.index)
    data = {'A index+yields': signals(A.px.pct_change(), rbA)}
    F = px[['ES=F', 'ZN=F']].dropna(); data['B futures'] = signals(F['ES=F'].pct_change(), F['ZN=F'].pct_change())
    E = px[['SPY', 'IEF']].dropna(); data['C ETFs'] = signals(E.SPY.pct_change(), E.IEF.pct_change())
    P = {'their sample': ('1997-09-10', '2023-03-17'), 'their extension': ('2023-03-20', '2025-12-31'),
         '1997-2025': ('1997-09-10', '2025-12-31'), 'our hold-out': ('2023-03-20', '2026-09-30')}
    rows = [dict(data=k, period=p, **fit(d, *ab)) for k, d in data.items() for p, ab in P.items()]
    r = pd.DataFrame(rows); r.to_csv('step8_us_through_2025.csv', index=False)
    pd.set_option('display.width', 220); print(r.round(3).to_string(index=False))
