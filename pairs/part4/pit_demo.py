import pandas as pd, numpy as np, yfinance as yf, pickle, warnings; warnings.filterwarnings('ignore')
d = pd.read_pickle('cot/cot_all.pkl'); code_col = [c for c in d.columns if 'Contract Market Code' in c][0]
MK = {'13874A': ('S&P 500 E-mini', 'ES=F'), '043602': ('10y Treasury', 'ZN=F'), '067651': ('WTI crude', 'CL=F'),
      '088691': ('Gold', 'GC=F'), '099741': ('Euro', '6E=F'), '097741': ('Yen', '6J=F')}
d[code_col] = d[code_col].astype(str).str.strip()
cot = {}
for code, (name, tk) in MK.items():
    x = d[d[code_col] == code].copy(); x['asof'] = pd.to_datetime(x['As of Date in Form YYYY-MM-DD'])
    x = x.groupby('asof').first().sort_index()
    net = (x['Noncommercial Positions-Long (All)'] - x['Noncommercial Positions-Short (All)']) / x['Open Interest (All)']
    cot[name] = net
    print(f'{name:16s} {len(net)} weeks {net.index[0].date()} -> {net.index[-1].date()}')
px = yf.download([v[1] for v in MK.values()], start='2018-01-01', end='2026-09-26', progress=False, auto_adjust=True)['Close']
px.columns = [{v[1]: v[0] for v in MK.values()}[c] for c in px.columns]
pickle.dump(dict(cot=cot, px=px), open('pit_data.pkl', 'wb')); print(px.dropna(how='all').index[[0, -1]])
