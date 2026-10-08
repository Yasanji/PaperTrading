"""Daily closes for every symbol in the universe file, plus FX and URTH (MSCI World proxy). Usage: python prices.py CSV OUT START"""
import sys, pandas as pd, yfinance as yf
u = pd.read_csv(sys.argv[1]); syms = sorted(set(u.symbol.dropna()))
fx = ['EURUSD=X', 'GBPUSD=X', 'CHFUSD=X', 'SEKUSD=X', 'DKKUSD=X', 'NOKUSD=X', 'URTH']
frames = []
for i in range(0, len(syms + fx), 100):
    b = (syms + fx)[i:i + 100]
    d = yf.download(b, start=sys.argv[3], progress=False, auto_adjust=False, threads=True)['Close']
    frames.append(d)
p = pd.concat(frames, axis=1); p.to_pickle(sys.argv[2]); print(p.shape, p.index.min(), p.index.max())
