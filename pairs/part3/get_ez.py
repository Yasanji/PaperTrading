import pandas as pd, yfinance as yf, pickle, time, warnings; warnings.filterwarnings('ignore')
from concurrent.futures import ThreadPoolExecutor
EZ = ['Germany','France','Italy','Spain','Netherlands','Belgium','Finland','Austria','Portugal','Ireland']
HOME = {'Germany':'GER','France':'PAR','Italy':'MIL','Spain':'MCE','Netherlands':'AMS','Belgium':'BRU','Finland':'HEL','Austria':'VIE','Portugal':'LIS','Ireland':'ISE'}
ez = pd.read_csv('ez_small.csv'); ez = ez[ez['Trade Country Name'].isin(EZ)].copy()
def lookup(row):
    for _ in range(2):
        try:
            q = yf.Search(row.ISIN, max_results=8).quotes
            home = [x['symbol'] for x in q if x.get('exchange') == HOME[row['Trade Country Name']]]
            return row.ISIN, (home or [x['symbol'] for x in q if x.get('quoteType') == 'EQUITY'] or [None])[0]
        except Exception: time.sleep(1)
    return row.ISIN, None
with ThreadPoolExecutor(6) as ex: sym = dict(ex.map(lookup, [r for _, r in ez.iterrows()]))
ez['yf'] = ez.ISIN.map(sym); print('mapped', ez.yf.notna().sum(), 'of', len(ez), flush=True)
ez = ez.dropna(subset=['yf']).drop_duplicates('yf')
raw = yf.download(list(ez.yf), start='2021-09-27', end='2026-09-25', auto_adjust=False, progress=False, threads=True)
px, cl, vol = raw['Adj Close'], raw['Close'], raw['Volume']
good = [c for c in px.columns if px[c].notna().sum() >= 1000]
meta = pd.DataFrame({'yf': ez.yf, 'company': ez['Security Name'], 'icb': ez['Sector Classification'],
                     'industry': ez['Industry Classification'], 'currency': 'EUR', 'country': ez['Trade Country Name']})
meta = meta[meta.yf.isin(good)].reset_index(drop=True)
mf = yf.download(['DBMF', 'KMLM', 'WTMF'], start='2021-09-20', end='2026-09-25', auto_adjust=False, progress=False)['Adj Close']
pickle.dump(dict(meta=meta, px={c: px[c].dropna() for c in good}, adv_gbp={c: (cl[c] * vol[c]).dropna() for c in good},
                 mf={c: mf[c].dropna() for c in mf.columns}), open('data_ezsmall.pkl', 'wb'))
print('full history:', len(meta), '| by country', meta.country.value_counts().to_dict())
print('MF ETFs:', {c: (str(mf[c].dropna().index[0].date()), int(mf[c].notna().sum())) for c in mf.columns})
