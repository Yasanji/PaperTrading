import pandas as pd, numpy as np, yfinance as yf, pickle, warnings; warnings.filterwarnings('ignore')
d = pd.read_pickle('cot/cot_all.pkl'); cc = [c for c in d.columns if 'Contract Market Code' in c][0]
d[cc] = d[cc].astype(str).str.strip()
MK = {'13874A': ('S&P 500', 'ES=F'), '209742': ('Nasdaq-100', 'NQ=F'), '042601': ('2y Treasury', 'ZT=F'),
      '043602': ('10y Treasury', 'ZN=F'), '020601': ('30y Treasury', 'ZB=F'), '067651': ('WTI crude', 'CL=F'),
      '023651': ('Natural gas', 'NG=F'), '088691': ('Gold', 'GC=F'), '084691': ('Silver', 'SI=F'),
      '085692': ('Copper', 'HG=F'), '099741': ('Euro', '6E=F'), '097741': ('Yen', '6J=F'),
      '096742': ('Pound', '6B=F'), '232741': ('Australian dollar', '6A=F'), '090741': ('Canadian dollar', '6C=F')}
cot = {}
for code, (name, tk) in MK.items():
    x = d[d[cc] == code].copy(); x['asof'] = pd.to_datetime(x['As of Date in Form YYYY-MM-DD']); x = x.groupby('asof').first().sort_index()
    net = (x['Noncommercial Positions-Long (All)'] - x['Noncommercial Positions-Short (All)']) / x['Open Interest (All)']
    cot[name] = net; print(f"{name:18s} {code} {len(net):4d} weeks {net.index[0].date()} -> {net.index[-1].date()}  [{x['Market and Exchange Names'].iloc[-1][:45]}]")
px = yf.download([v[1] for v in MK.values()], start='2007-01-01', end='2026-09-26', progress=False, auto_adjust=True)['Close']
px.columns = [{v[1]: v[0] for v in MK.values()}[c] for c in px.columns]
print({c: str(px[c].first_valid_index().date()) for c in px.columns})
pickle.dump(dict(cot=cot, px=px), open('tsmom_data.pkl', 'wb'))
