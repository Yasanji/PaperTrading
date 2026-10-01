import pandas as pd, requests, io, yfinance as yf, pickle
from concurrent.futures import ThreadPoolExecutor
h = requests.get('https://en.wikipedia.org/wiki/FTSE_250_Index', headers={'User-Agent': 'Mozilla/5.0'}).text
t = [x for x in pd.read_html(io.StringIO(h)) if len(x) > 100][0]; t.columns = ['company', 'ticker', 'icb']
t = t[~t.icb.str.contains('Investment Trust|Closed End', case=False, na=False)].copy()
t['yf'] = t.ticker.str.strip().str.replace('.', '-', regex=False).str.rstrip('-') + '.L'
print('operating companies:', len(t), flush=True)
def info(y):
    try: i = yf.Ticker(y).info; return y, i.get('industry'), i.get('currency')
    except Exception: return y, None, None
with ThreadPoolExecutor(8) as ex: meta = pd.DataFrame(list(ex.map(info, t.yf)), columns=['yf', 'industry', 'currency'])
meta = t.merge(meta, on='yf').dropna(subset=['industry'])
raw = yf.download(list(meta.yf), start='2021-09-27', end='2026-09-25', auto_adjust=False, progress=False, threads=True)
px, vol, cl = raw['Adj Close'], raw['Volume'], raw['Close']
good = [c for c in px.columns if px[c].notna().sum() >= 1000]
print('with industry:', len(meta), '| full history:', len(good), flush=True)
bond = yf.download('EUNH.DE', start='2021-09-20', end='2026-09-25', auto_adjust=False, progress=False)['Adj Close'].squeeze().dropna()
print('bond ETF EUNH.DE:', len(bond), bond.index[0].date(), bond.index[-1].date(), flush=True)
pickle.dump(dict(meta=meta[meta.yf.isin(good)].reset_index(drop=True), px={c: px[c].dropna() for c in good},
                 adv_gbp={c: (cl[c] * vol[c] / 100).dropna() for c in good}, bond=bond), open('data250.pkl', 'wb'))
m = meta[meta.yf.isin(good)]; print('currencies:', m.currency.value_counts().to_dict()); print(m.industry.value_counts().head(10).to_string())
