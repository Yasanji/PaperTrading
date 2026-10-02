import pickle, pandas as pd, yfinance as yf, warnings; warnings.filterwarnings('ignore')
L = pickle.load(open('msb/long_data.pkl', 'rb')); names = list(L['meta'].yf)
raw = yf.download(names, start='2004-01-01', end='2026-09-26', auto_adjust=False, progress=False, threads=True)
fx = {c: yf.download(f'{c}EUR=X', start='2004-01-01', end='2026-09-26', progress=False)['Close'].squeeze().dropna() for c in ['GBP', 'CHF', 'SEK', 'NOK', 'DKK', 'USD', 'PLN']}
first = raw['Adj Close'].apply(lambda s: s.first_valid_index())
print('equity names with prices by Jan 2006:', int((first <= '2006-01-01').sum()), 'of', len(names), '| by Jan 2008:', int((first <= '2008-01-01').sum()))
print('FX first dates:', {k: str(v.index[0].date()) for k, v in fx.items()})
pickle.dump(dict(meta=L['meta'], px=raw['Adj Close'], close=raw['Close'], volume=raw['Volume'], fx=fx), open('msb/long_data_ext.pkl', 'wb'))
T = pickle.load(open('tsmom_data.pkl', 'rb')); tick = {'S&P 500': 'ES=F', 'Nasdaq-100': 'NQ=F', '2y Treasury': 'ZT=F', '10y Treasury': 'ZN=F', '30y Treasury': 'ZB=F',
    'WTI crude': 'CL=F', 'Natural gas': 'NG=F', 'Gold': 'GC=F', 'Silver': 'SI=F', 'Copper': 'HG=F', 'Euro': '6E=F', 'Yen': '6J=F', 'Pound': '6B=F',
    'Australian dollar': '6A=F', 'Canadian dollar': '6C=F'}
fp = yf.download(list(tick.values()), start='2004-01-01', end='2026-09-26', progress=False, auto_adjust=True)['Close']; fp.columns = [{v: k for k, v in tick.items()}[c] for c in fp.columns]
print('futures first dates:', {c: str(fp[c].first_valid_index().date()) for c in fp.columns})
pickle.dump(dict(cot=T['cot'], px=fp), open('tsmom_data_ext.pkl', 'wb'))
