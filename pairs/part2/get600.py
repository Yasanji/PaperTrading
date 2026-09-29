import pandas as pd, yfinance as yf, pickle
from concurrent.futures import ThreadPoolExecutor
# Wikipedia constituent table -> Yahoo tickers by country suffix
SUF = {'United Kingdom':'.L','France':'.PA','Germany':'.DE','Switzerland':'.SW','Netherlands':'.AS','Spain':'.MC',
       'Italy':'.MI','Sweden':'.ST','Denmark':'.CO','Finland':'.HE','Norway':'.OL','Belgium':'.BR','Austria':'.VI',
       'Ireland':'.IR','Portugal':'.LS','Poland':'.WA','Luxembourg':'.AS','Greece':'.AT'}
t = pd.read_csv('stoxx600_constituents.csv')
t['yf'] = [str(k).strip().replace(' ', '-').replace('.', '-') + SUF.get(c, '?') for k, c in zip(t.Ticker, t.Country)]
t = t[~t.yf.str.endswith('?')]
def info(y):
    try:
        i = yf.Ticker(y).info; return y, i.get('industry'), i.get('currency')
    except Exception: return y, None, None
with ThreadPoolExecutor(8) as ex: meta = pd.DataFrame(list(ex.map(info, t.yf)), columns=['yf','industry','currency'])
meta = t.merge(meta, on='yf'); ok = meta.dropna(subset=['industry','currency'])
print('with industry:', len(ok), 'of', len(meta), flush=True)
px = yf.download(list(ok.yf), start='2021-09-27', end='2026-09-25', auto_adjust=False, progress=False, threads=True)['Adj Close']
good = [c for c in px.columns if px[c].notna().sum() >= 1000]
print('full price history:', len(good), flush=True)
pickle.dump(dict(meta=ok[ok.yf.isin(good)].reset_index(drop=True), px={c: px[c].dropna() for c in good}), open('data600.pkl','wb'))
