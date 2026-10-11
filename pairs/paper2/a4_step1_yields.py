"""Paper 2, Amendment 4.3: data checks for the candidate markets, bond returns only (no equity data is touched).
Specified and committed 11 October 2026 before it was run.

For each market: the official daily 10-year government yield (source below), coverage from 1 January 2005 to
30 September 2026 with no gap over ten business days (rule 1), and the timing check (rule 2): daily price returns of a
constant-maturity 10-year par bond at the yield, correlated with the traded bond ETF named below, same day and
previous day; pass if same-day >= 0.6 and >= 3 x previous-day. The ETF is fixed here before any correlation is seen.
Markets whose official source cannot be reached from this workspace are reported as such, not failed.
Writes a4_step1_yields.csv (daily yields) and a4_step1_report.csv."""
import io, requests, numpy as np, pandas as pd, yfinance as yf
H = {'User-Agent': 'Mozilla/5.0'}; get = lambda u: requests.get(u, headers=H, timeout=90)

def japan():      # Ministry of Finance, JGB yields by maturity, daily since 1974
    t = get('https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/historical/jgbcme_all.csv').text
    d = pd.read_csv(io.StringIO(t), skiprows=1); d['Date'] = pd.to_datetime(d.Date, errors='coerce')
    s = pd.to_numeric(d.set_index('Date')['10Y'], errors='coerce')
    t2 = get('https://www.mof.go.jp/english/policy/jgbs/reference/interest_rate/jgbcme.csv').text     # current year
    e = pd.read_csv(io.StringIO(t2), skiprows=1); e['Date'] = pd.to_datetime(e.Date, errors='coerce')
    return pd.concat([s, pd.to_numeric(e.set_index('Date')['10Y'], errors='coerce')]).dropna()
def canada():     # Bank of Canada, 10-year benchmark bond yield
    t = get('https://www.bankofcanada.ca/valet/observations/BD.CDN.10YR.DQ.YLD/json?start_date=2004-01-01').json()
    return pd.Series({pd.Timestamp(o['d']): float(o['BD.CDN.10YR.DQ.YLD']['v']) for o in t['observations'] if o.get('BD.CDN.10YR.DQ.YLD')})
def australia():  # Reserve Bank of Australia, F2 (historical file to 2013, current csv after)
    cur = pd.read_csv(io.StringIO(get('https://www.rba.gov.au/statistics/tables/csv/f2.1-data.csv').content.decode('utf-8-sig')), skiprows=10)
    cur = cur.set_index(cur.columns[0]); cur.index = pd.to_datetime(cur.index, format='%d-%b-%Y', errors='coerce')
    s = pd.to_numeric(cur['FCMYGBAG10D'], errors='coerce')
    h = pd.read_excel(io.BytesIO(get('https://www.rba.gov.au/statistics/tables/xls-hist/f02dhist.xls').content), skiprows=10, index_col=0)
    h.index = pd.to_datetime(h.index, errors='coerce')
    return pd.concat([pd.to_numeric(h['FCMYGBAG10D'], errors='coerce'), s]).dropna().sort_index()
def sweden():     # Riksbank, Swedish government bond 10 years
    t = get('https://api.riksbank.se/swea/v1/Observations/SEGVB10YC/2004-01-01/2026-10-10').json()
    return pd.Series({pd.Timestamp(o['date']): float(o['value']) for o in t})
def switzerland():  # Swiss National Bank, spot interest rates on Confederation bonds, 10 years (zero coupon, 10J0)
    d = pd.read_csv(io.StringIO(get('https://data.snb.ch/api/cube/rendoblid/data/csv/en').content.decode('utf-8-sig')), sep=';', skiprows=3)
    d = d[d.D0 == '10J0']; return pd.to_numeric(d.set_index(pd.to_datetime(d.Date)).Value, errors='coerce').dropna()
SOURCES = {'JP': (japan, '1482.T'), 'CA': (canada, 'XGB.TO'), 'AU': (australia, 'IGB.AX'), 'SE': (sweden, None),
           'CH': (switzerland, 'CSBGC0.SW'), 'FR': (None, None), 'NL': (None, None), 'ES': (None, None), 'IT': (None, None)}
UNREACHED = {'FR': 'Banque de France webstat (TEC10) returns no observations without an API key',
             'NL': 'De Nederlandsche Bank data portal refuses this workspace (403)',
             'ES': 'Banco de Espana daily bond table not identified in its CSV service',
             'IT': 'Banca d\'Italia BDS not reachable as a file from this workspace'}

def par_price(c, y, n=20):
    i = np.arange(1, n + 1); return (c / 2 * (1 + y / 2) ** -i).sum() + (1 + y / 2) ** -n

rows, Y = [], {}
for m, (fn, etf) in SOURCES.items():
    if fn is None: rows.append(dict(market=m, status='source not reached', note=UNREACHED[m])); continue
    try: y = fn().sort_index(); y = y[~y.index.duplicated()] / 100
    except Exception as e: rows.append(dict(market=m, status='source error', note=f'{type(e).__name__}: {e}'[:200])); continue
    Y[m] = y; w = y.loc['2005-01-01':'2026-09-30']
    gap = int((pd.Series(w.index[1:]) - pd.Series(w.index[:-1])).dt.days.max()) if len(w) > 1 else 9999
    bd_gap = len(pd.bdate_range(w.index[0], w.index[-1])) - len(w) if len(w) else None
    cover = bool(len(w)) and w.index[0] <= pd.Timestamp('2005-01-14') and w.index[-1] >= pd.Timestamp('2026-09-23')
    longest = int(max((len(pd.bdate_range(a, b)) - 2 for a, b in zip(w.index[:-1], w.index[1:])), default=0))
    r1 = cover and longest <= 10
    rb = pd.Series([np.nan] + [par_price(y.iloc[k - 1], y.iloc[k]) - 1 for k in range(1, len(y))], index=y.index)
    same = prev = np.nan; r2 = False; note = ''
    if etf:
        p = yf.download(etf, start='2004-01-01', end='2026-10-01', progress=False, auto_adjust=True)['Close'].squeeze().dropna()
        j = pd.concat([rb.rename('b'), p.pct_change().rename('e')], axis=1, join='inner').dropna()
        same, prev = j.b.corr(j.e), j.b.shift(1).corr(j.e)
        r2 = bool(same >= 0.6 and same >= 3 * prev); note = f'{etf}, {len(j)} common days from {j.index[0].date()}'
    else: note = 'no traded local government bond series on Yahoo Finance'
    rows.append(dict(market=m, status='pass' if (r1 and r2) else 'fail', first=w.index[0].date() if len(w) else None,
                     last=w.index[-1].date() if len(w) else None, longest_gap_bdays=longest, rule1=r1,
                     corr_same=round(same, 2) if same == same else None, corr_prev=round(prev, 2) if prev == prev else None, rule2=r2, note=note))
pd.DataFrame(Y).to_csv('a4_step1_yields.csv'); r = pd.DataFrame(rows); r.to_csv('a4_step1_report.csv', index=False)
pd.set_option('display.width', 250); print(r.to_string(index=False))
