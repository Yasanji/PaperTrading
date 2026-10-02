import pickle, pandas as pd, yfinance as yf, warnings; warnings.filterwarnings('ignore')
D6 = pickle.load(open('data600.pkl', 'rb')); meta = D6['meta'].drop_duplicates('yf'); meta = meta[meta.yf.isin(D6['px'].keys())].reset_index(drop=True)
names = list(meta.yf)
raw = yf.download(names, start='2009-06-01', end='2026-09-26', auto_adjust=False, progress=False, threads=True)
px, cl, vol = raw['Adj Close'], raw['Close'], raw['Volume']
fx = {}
for c in ['GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'USD', 'PLN']:
    fx[c] = yf.download(f'{c}EUR=X', start='2009-06-01', end='2026-09-26', progress=False)['Close'].squeeze().dropna()
first = px.apply(lambda s: s.first_valid_index())
print('names:', len(names), '| with data by Jan 2012:', int((first <= '2012-01-01').sum()), '| by Jan 2013:', int((first <= '2013-01-01').sum()))
pickle.dump(dict(meta=meta, px=px, close=cl, volume=vol, fx=fx), open('msb/long_data.pkl', 'wb'))
print('saved', px.shape, px.index[0].date(), px.index[-1].date())
