# pip install yfinance pandas numpy statsmodels matplotlib
import numpy as np, pandas as pd, yfinance as yf
import statsmodels.tsa.stattools as ts
import matplotlib.pyplot as plt
from itertools import combinations

# the 50 current EURO STOXX 50 constituents
NAMES = ['ADS.DE','ADYEN.AS','AD.AS','AI.PA','AIR.PA','ALV.DE','ABI.BR','ARGX.BR',
         'ASML.AS','CS.PA','BAS.DE','BAYN.DE','BBVA.MC','SAN.MC','BMW.DE','BNP.PA',
         'BN.PA','DBK.DE','DB1.DE','DHL.DE','DTE.DE','ENEL.MI','ENI.MI','EL.PA',
         'RACE.MI','RMS.PA','IBE.MC','ITX.MC','IFX.DE','INGA.AS','ISP.MI','OR.PA',
         'MC.PA','MBG.DE','MUV2.DE','NDA-FI.HE','PRX.AS','RHM.DE','SAF.PA','SGO.PA',
         'SAN.PA','SAP.DE','SU.PA','SIE.DE','ENR.DE','TTE.PA','DG.PA','UCG.MI',
         'VOW.DE','WKL.AS']

def closes(sym):
    return yf.download(sym, start='2021-09-27', end='2026-09-25',
                       auto_adjust=False, progress=False)['Adj Close'].rename(sym)

px = {s: closes(s) for s in NAMES}

# screen every pair: correlation gate, then cointegration on RAW prices
n_corr = n_coint = 0
for a, b in combinations(NAMES, 2):
    d = pd.concat([px[a], px[b]], axis=1).dropna()
    if len(d) < 250 or abs(d[a].corr(d[b])) < 0.70:
        continue                                   # correlation gate
    n_corr += 1
    p = min(ts.coint(d[a], d[b])[1], ts.coint(d[b], d[a])[1])
    if p < 0.05:
        n_coint += 1
print(n_corr, 'pass correlation,', n_coint, 'cointegrate')   # 574, 81

# the most correlated pair in the index fails cointegration
d = pd.concat([px['BBVA.MC'], px['SAN.MC']], axis=1).dropna()
print('BBVA/SAN corr',    round(d['BBVA.MC'].corr(d['SAN.MC']), 3))          # 0.994
print('BBVA/SAN coint p', round(ts.coint(d['BBVA.MC'], d['SAN.MC'])[1], 3))  # 0.29 fails

# the pair the engine keeps
d = pd.concat([px['SAF.PA'], px['SIE.DE']], axis=1).dropna()
y, x = d['SAF.PA'], d['SIE.DE']
print('SAF/SIE coint p', round(ts.coint(y, x)[1], 3))             # 0.003 holds

# spread, half-life, Hurst
ly, lx = np.log(y), np.log(x)
spread = ly - lx
lag = spread.shift(1); dd = spread - lag
r = pd.concat([lag, dd], axis=1).dropna()
b = np.polyfit(r.iloc[:,0], r.iloc[:,1], 1)[0]
print('half-life (days)', round(-np.log(2)/b))                    # 89

def hurst(v):
    lags = range(2, 40)
    tau = [np.sqrt(np.std(v[l:] - v[:-l])) for l in lags]
    return np.polyfit(np.log(list(lags)), np.log(tau), 1)[0] * 2
print('Hurst', round(hurst(spread.values), 3))                   # 0.46

# point-in-time backtest: rolling z, dollar-neutral, net of costs
W, ENTRY, EXIT, COST = 90, 2.0, 0.5, 1.0          # window near the half-life, 1 bp per leg
mu = spread.rolling(W).mean().shift(1)
sd = spread.rolling(W).std().shift(1)
z = (spread - mu) / sd

pos = pd.Series(0.0, index=spread.index); cur = 0.0
for i in range(len(z)):
    zi = z.iloc[i]
    if np.isnan(zi):
        pos.iloc[i] = cur; continue
    if cur == 0:
        cur = -1.0 if zi >= ENTRY else (1.0 if zi <= -ENTRY else 0.0)
    else:
        if abs(zi) <= EXIT: cur = 0.0
        elif cur == 1 and zi >= ENTRY: cur = -1.0
        elif cur == -1 and zi <= -ENTRY: cur = 1.0
    pos.iloc[i] = cur

ret = (ly.diff() - lx.diff()) / 2.0                # dollar-neutral spread return
cost = pos.diff().abs().fillna(0) * 2 * (COST/1e4) / 2.0
net = (pos.shift(1) * ret - cost).dropna()

ann = np.sqrt(252)
print('Sharpe',        round(net.mean()/net.std()*ann, 2))        # 1.02
print('ann vol %',     round(net.std()*ann*100, 1))              # 7.9
print('max drawdown %',round((net.cumsum()-net.cumsum().cummax()).min()*100, 1))  # -13.3

# residual market beta, against the EURO STOXX 50 index itself
idx = yf.download('^STOXX50E', start='2021-09-27', end='2026-09-25',
                  progress=False)['Close']
mkt = np.log(idx).diff().reindex(net.index)
d2 = pd.concat([net, mkt], axis=1).dropna()
print('market beta', round(np.polyfit(d2.iloc[:,1], d2.iloc[:,0], 1)[0], 2))   # 0.03

plt.plot(100*(np.exp(net.cumsum())-1)); plt.ylabel('cumulative return %'); plt.show()
