import pandas as pd, yfinance as yf, pickle, time, warnings; warnings.filterwarnings('ignore')
from concurrent.futures import ThreadPoolExecutor
fca = pd.read_excel('shorts/fca.xlsx'); 
amf = None
for enc in ('utf-8', 'latin1'):
    try: amf = pd.read_csv('shorts/amf.csv', sep=';', encoding=enc); break
    except Exception: pass
print('AMF cols:', amf.columns.tolist())
isin_col = [c for c in amf.columns if 'isin' in c.lower()][0]
m = pickle.load(open('msb/long_data.pkl', 'rb'))['meta']; ours = set(m.yf[m.yf.str.endswith(('.PA', '.L'))])
isins = sorted(set(fca.ISIN.dropna().astype(str)) | set(amf[isin_col].dropna().astype(str)))
print('unique ISINs to look up:', len(isins), flush=True)
def look(isin):
    for _ in range(2):
        try:
            q = yf.Search(isin, max_results=6).quotes
            syms = [x['symbol'] for x in q if x.get('symbol', '').endswith(('.PA', '.L'))]
            return isin, syms
        except Exception: time.sleep(1)
    return isin, []
with ThreadPoolExecutor(8) as ex: res = dict(ex.map(look, isins))
mp = {}
for isin, syms in res.items():
    hit = [s for s in syms if s in ours]
    if hit: mp[hit[0]] = isin
print('matched to our universe:', len(mp), 'of', len(ours))
missing = sorted(ours - set(mp)); print('unmatched sample:', missing[:15])
pickle.dump(dict(map=mp, isin_col=isin_col), open('msb/isin_map.pkl', 'wb'))
