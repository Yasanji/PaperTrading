"""Paper 2, Amendment 4 (with 5): main tests, run once. Markets: Canada and Australia (new), the UK, Germany and the
US (seen). Basis 4.4: equity price index; bond = price change of a constant-maturity 10-year bond at the official
yield, no carry. Equation 4.5: Harvey, Mazzoleni and Melone Table 1 (Threshold, Calendar, last-week indicator,
Calendar x last week, momentum, current return) plus the lagged US Threshold and Calendar x last week signals.
Tests 4.6; standard errors clustered by date for pools, Newey-West for single markets (HC1 alongside)."""
import io, requests, numpy as np, pandas as pd, statsmodels.api as sm, yfinance as yf
from scipy import stats
H = {'User-Agent': 'Mozilla/5.0'}; get = lambda u: requests.get(u, headers=H, timeout=90)
MAIN, END, POST = ('1999-01-01', '2023-03-17'), '2026-09-30', '2023-03-20'
X = ['thr', 'cal', 'week4', 'calw4', 'mom', 'ret']

def par_price(c, y, n=20):
    i = np.arange(1, n + 1); return (c / 2 * (1 + y / 2) ** -i).sum() + (1 + y / 2) ** -n
def par_ret(y): return pd.Series([np.nan] + [par_price(y.iloc[k - 1], y.iloc[k]) - 1 for k in range(1, len(y))], index=y.index)
def ust():
    fr = []
    for yr in range(1997, 2027):
        r = get(f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{yr}/all?type=daily_treasury_yield_curve&field_tdr_date_value={yr}&page&_format=csv')
        if r.status_code == 200 and 'Date' in r.text[:40]: fr.append(pd.read_csv(io.StringIO(r.text))[['Date', '10 Yr']])
    t = pd.concat(fr); t['Date'] = pd.to_datetime(t.Date); return t.set_index('Date').sort_index()['10 Yr'].astype(float) / 100
def gilt():
    b = pd.read_csv(io.StringIO(get('https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/1997&Dateto=now&SeriesCodes=IUDMNPY&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N').text))
    b['DATE'] = pd.to_datetime(b.DATE, format='%d %b %Y'); return b.dropna().set_index('DATE').IUDMNPY / 100
def ecb():
    e = pd.read_csv(io.StringIO(get('https://data-api.ecb.europa.eu/service/data/YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y?format=csvdata').text))
    return e.set_index(pd.to_datetime(e.TIME_PERIOD)).OBS_VALUE.sort_index() / 100
y4 = pd.read_csv('a4_step1_yields.csv', index_col=0, parse_dates=True)
def boc():
    t = get('https://www.bankofcanada.ca/valet/observations/BD.CDN.10YR.DQ.YLD/json?start_date=1997-01-01').json()
    return pd.Series({pd.Timestamp(o['d']): float(o['BD.CDN.10YR.DQ.YLD']['v']) for o in t['observations'] if o.get('BD.CDN.10YR.DQ.YLD')}).sort_index() / 100

def signals(re, rb, target=0.6):
    d = pd.DataFrame(dict(re=re, rb=rb)).dropna(); d['xa'] = d.re - d.rb; a, b, n = d.re.values, d.rb.values, len(d)
    drift = lambda w, x, y: w * (1 + x) / (w * (1 + x) + (1 - w) * (1 + y))
    def thr(delta):
        w, s = target, np.empty(n)
        for t in range(n):
            w = drift(w, a[t], b[t]); s[t] = w - target
            if abs(w - target) > delta: w = target
        return s
    d['thr'] = np.mean([thr(x) for x in np.arange(0, 0.02501, 0.001)], axis=0)
    idx = d.index.to_series(); mend = idx.groupby(d.index.to_period('M')).transform('max') == idx
    w, cal = target, np.empty(n)
    for t in range(n):
        w = drift(w, a[t], b[t]); cal[t] = w - target
        if mend.iloc[t]: w = target
    d['cal'] = cal; d['week4'] = (idx.groupby(d.index.to_period('M')).cumcount(ascending=False) < 5).astype(float); d['calw4'] = d.cal * d.week4
    cum = d.xa.cumsum()
    d['mom'] = (np.mean([np.sign(cum - cum.shift(h)) for h in range(11, 21)], axis=0) + np.mean([np.sign(cum - cum.shift(h)) for h in (21, 42, 63, 126, 252)], axis=0)) / 2
    d['ret'] = d.xa; d['y_next'] = d.xa.shift(-1); return d

def build(target=0.6):
    px = yf.download(['^GSPC', '^FTSE', '^GDAXIP', '^GSPTSE', '^AXJO'], start='1997-01-01', end='2026-10-02', progress=False, auto_adjust=True)['Close']
    ecb_y = ecb(); de_rb = np.exp(-10 * (ecb_y - ecb_y.shift(1))) - 1
    M = {'US': (px['^GSPC'], par_ret(ust())), 'UK': (px['^FTSE'], par_ret(gilt())), 'DE': (px['^GDAXIP'], de_rb),
         'CA': (px['^GSPTSE'], par_ret(boc())), 'AU': (px['^AXJO'], par_ret(y4['AU'].dropna()))}
    S = {}
    for m, (p, rb) in M.items():
        p = p.dropna(); j = pd.concat([p.rename('p'), rb.rename('rb')], axis=1, join='inner').dropna()
        S[m] = signals(j.p.pct_change(), j.rb, target)
    us = S['US'][['thr', 'calw4']].rename(columns={'thr': 'us_thr', 'calw4': 'us_calw4'})
    for m in S:
        if m == 'US': continue
        l = pd.merge_asof(pd.DataFrame(index=S[m].index).reset_index().rename(columns={'index': 'd', 'Date': 'd'}),
                          us.reset_index().rename(columns={'index': 'd', 'Date': 'd'}), on='d', direction='backward', allow_exact_matches=False).set_index('d')
        S[m] = S[m].join(l)
    return S

def nw_lags(T): return int(np.floor(4 * (T / 100) ** (2 / 9)))
def ivx_p(df, x, cols):
    oth = [c for c in cols if c != x]; Z = sm.add_constant(df[oth]).values; T = len(df)
    res = lambda v: v - Z @ np.linalg.lstsq(Z, v, rcond=None)[0]
    rz = 1 - 1 / T ** 0.95; dx = np.diff(df[x].values, prepend=df[x].values[0]); z = np.empty(T); acc = 0.0
    for t in range(T): acc = rz * acc + dx[t]; z[t] = acc
    yt, xt, zt = res(df.y_next.values), res(df[x].values), res(z)
    b = (zt @ yt) / (zt @ xt); e = yt - b * xt; v = (zt ** 2 @ e ** 2) / (zt @ xt) ** 2
    return 2 * (1 - stats.norm.cdf(abs(b / np.sqrt(v))))

def single(S, m, a, b):
    cols = X + (['us_thr', 'us_calw4'] if m != 'US' else []); d = S[m].loc[a:b].dropna(subset=cols + ['y_next'])
    f = sm.OLS(d.y_next, sm.add_constant(d[cols])); nw = f.fit(cov_type='HAC', cov_kwds={'maxlags': nw_lags(len(d))}); hc = f.fit(cov_type='HC1')
    out = {}
    for s in ('thr', 'calw4'):
        p = ivx_p(d, s, cols)
        out[s] = dict(coef=nw.params[s], t_nw=nw.tvalues[s], t_hc=hc.tvalues[s], ivx_p=p, supported=bool(nw.params[s] < 0 and nw.tvalues[s] < -2 and p < 0.05))
    return out, len(d), d.index[0].date()

def pooled(S, markets, a, b, post=False):
    parts = []
    for m in markets:
        cols = X + (['us_thr', 'us_calw4'] if m != 'US' else []); d = S[m].loc[a:b].dropna(subset=cols + ['y_next']).copy()
        z = pd.DataFrame(index=d.index); z['y'] = d.y_next; z['thr'] = d.thr; z['calw4'] = d.calw4
        for c in [c for c in cols if c not in ('thr', 'calw4')] + ['const']:
            z[f'{c}_{m}'] = d[c] if c != 'const' else 1.0                      # constant and controls per market
        for mm in markets:
            if mm != m:
                for c in [c for c in (X + (['us_thr', 'us_calw4'] if mm != 'US' else [])) if c not in ('thr', 'calw4')] + ['const']: z[f'{c}_{mm}'] = 0.0
        if post:
            p = (d.index >= POST).astype(float); z['thr_post'] = d.thr * p; z['calw4_post'] = d.calw4 * p
        parts.append(z)
    z = pd.concat(parts).fillna(0.0); Xc = [c for c in z.columns if c != 'y']
    r = sm.OLS(z.y, z[Xc]).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(z.index)[0]})
    keys = ['thr_post', 'calw4_post'] if post else ['thr', 'calw4']
    return {k: dict(coef=r.params[k], t=r.tvalues[k], p=r.pvalues[k], ci=tuple(r.conf_int().loc[k])) for k in keys}, int(r.nobs)

if __name__ == '__main__':
    import sys
    target = float(sys.argv[1]) if len(sys.argv) > 1 else 0.6
    S = build(target); rows = []; P = {}
    for lab, mk in (('new (CA, AU)', ['CA', 'AU']), ('all five', ['US', 'UK', 'DE', 'CA', 'AU'])):
        res, n = pooled(S, mk, *MAIN)
        for k, v in res.items(): rows.append(dict(test=f'4.6.1 pooled {lab}, main', signal=k, coef=v['coef'], t=v['t'], p=v['p'], n=n)); P[f'pooled {lab} {k}'] = v['p']
        res, n = pooled(S, mk, MAIN[0], END, post=True)
        for k, v in res.items(): rows.append(dict(test=f'4.6.2 change after Mar 2023, {lab}', signal=k, coef=v['coef'], t=v['t'], p=v['p'], n=n, ci=f"{v['ci'][0]:.3f} to {v['ci'][1]:.3f}")); P[f'change {lab} {k}'] = v['p']
    for m in ['CA', 'AU', 'UK', 'DE', 'US']:
        res, n, start = single(S, m, *MAIN)
        for k, v in res.items():
            rows.append(dict(test=f'4.6.3 {m} main', signal=k, coef=v['coef'], t=v['t_nw'], t_hc=v['t_hc'], ivx_p=v['ivx_p'], supported=v['supported'], n=n, start=start))
            P[f'{m} {k}'] = 2 * (1 - stats.norm.cdf(abs(v['t_nw'])))
    pv = pd.Series(P).sort_values(); k = len(pv); holm = pd.Series(np.minimum(1, np.maximum.accumulate([(k - i) * p for i, p in enumerate(pv.values)])), index=pv.index)
    R = pd.DataFrame(rows); R.to_csv(f'a4_step2_results_target{int(target*100)}.csv', index=False); holm.to_csv(f'a4_step2_holm_target{int(target*100)}.csv')
    pd.set_option('display.width', 250); print(R.round(4).to_string(index=False)); print('\nHolm-adjusted p-values:'); print(holm.round(4).to_string())
