"""Paper 2: local data and signals for Germany and the UK, as specified in PREREGISTRATION.md and AMENDMENTS.md."""
import io, requests, numpy as np, pandas as pd, yfinance as yf
def par_price(c, yy, n=20):
    i = np.arange(1, n + 1); return (c / 2 * (1 + yy / 2) ** -i).sum() + (1 + yy / 2) ** -n
BBK = 'https://api.statistiken.bundesbank.de/rest/download/BBSIS/D.I.ZST.ZI.EUR.S1311.B.A604.R10XX.R.A.A._Z._Z.A?format=csv&lang=en'
BOE = ('https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/1990&Dateto=now'
       '&SeriesCodes=IUDMNPY&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N')
get = lambda u: io.StringIO(requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=90).text)
def bund():
    k = pd.read_csv(get(BBK), skiprows=9, header=None, names=['d', 'y', 'f']); k['d'] = pd.to_datetime(k.d, errors='coerce')
    k['y'] = pd.to_numeric(k.y, errors='coerce'); return k.dropna(subset=['d', 'y']).set_index('d').y / 100
def gilt():
    b = pd.read_csv(get(BOE)); b['DATE'] = pd.to_datetime(b.DATE, format='%d %b %Y'); return b.dropna().set_index('DATE').IUDMNPY / 100
def ust(first=1997, last=2026):
    fr = []
    for y in range(first, last + 1):
        u = (f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all'
             f'?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv')
        r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        if r.status_code == 200 and 'Date' in r.text[:40]: fr.append(pd.read_csv(io.StringIO(r.text))[['Date', '10 Yr']])
    t = pd.concat(fr); t['Date'] = pd.to_datetime(t.Date); return t.set_index('Date').sort_index()['10 Yr'].astype(float) / 100
def eq(tk): return yf.download(tk, start='1996-01-01', end='2026-10-01', progress=False, auto_adjust=True)['Close'].squeeze().dropna()
def build(px, y, kind, carry=True):
    d = pd.concat([px.rename('px'), y.rename('y')], axis=1, join='inner').dropna(); d['re'] = d.px.pct_change()
    if kind == 'par': rb = [np.nan] + [par_price(d.y.iloc[k - 1], d.y.iloc[k]) - 1 for k in range(1, len(d))]
    else: rb = [np.nan] + [((1 + d.y.iloc[k - 1]) / (1 + d.y.iloc[k])) ** 10 - 1 for k in range(1, len(d))]
    d['rb'] = np.array(rb) + (d.y.shift(1) / 252 if carry else 0)
    d = d.dropna(); d['xa'] = d.re - d.rb; re, rb_, n = d.re.values, d.rb.values, len(d)
    drift = lambda w, a, b: w * (1 + a) / (w * (1 + a) + (1 - w) * (1 + b))
    def thr(delta):
        w, s = 0.6, np.empty(n)
        for t in range(n):
            w = drift(w, re[t], rb_[t]); s[t] = w - 0.6
            if abs(w - 0.6) > delta: w = 0.6
        return s
    d['thr'] = np.mean([thr(x) for x in np.arange(0, 0.02501, 0.001)], axis=0)
    mend = d.index.to_series().groupby(d.index.to_period('M')).transform('max') == d.index.to_series()
    w, cal = 0.6, np.empty(n)
    for t in range(n):
        w = drift(w, re[t], rb_[t]); cal[t] = w - 0.6
        if mend.iloc[t]: w = 0.6
    d['cal'] = cal; pos = d.index.to_series().groupby(d.index.to_period('M')).cumcount(ascending=False)
    d['week4'] = (pos < 5).astype(float); d['calw4'] = d.cal * d.week4
    cum = d.xa.cumsum()
    med = np.mean([np.sign(cum - cum.shift(h)) for h in range(11, 21)], axis=0)
    slow = np.mean([np.sign(cum - cum.shift(h)) for h in (21, 42, 63, 126, 252)], axis=0)
    d['mom'] = (med + slow) / 2
    for k in range(5): d[f'xa{k}'] = d.xa.shift(k)
    d['y_next'] = d.xa.shift(-1); return d
if __name__ == '__main__':
    US = build(eq('^GSPC'), ust(), 'par', carry=False)            # as in Step 1
    DE = build(eq('^GDAXI'), bund(), 'zero'); UK = build(eq('^FTSE'), gilt(), 'par')
    pd.to_pickle(dict(US=US, DE=DE, UK=UK), 'local_signals.pkl')
    for k, v in dict(US=US, DE=DE, UK=UK).items(): print(k, v.index[0].date(), '->', v.index[-1].date(), len(v), 'days')
