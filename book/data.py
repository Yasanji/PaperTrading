"""Price and rate inputs for the pods.

Live: daily closes of continuous futures from delta1.db (futures_prices, product = contract-check symbol, written by
futures_ib.py from Interactive Brokers). Dry runs without the Mac: Yahoo continuous futures, flagged as such."""
import sqlite3, pandas as pd, yfinance as yf
import config as C

YAHOO = {'MES': 'ES=F', 'ZT': 'ZT=F', 'ZN': 'ZN=F', 'MCL': 'CL=F', 'MHNG': 'NG=F', 'SIC': 'SI=F', 'MHG': 'HG=F',
         'M6E': '6E=F', 'MJY': '6J=F', 'M6B': '6B=F', 'M6A': '6A=F', 'MCD': '6C=F', 'MSF': '6S=F', 'NZD': '6N=F'}


def prices_db(start='2024-01-01'):
    con = sqlite3.connect(C.DB)
    d = pd.read_sql("SELECT date, product, settle FROM futures_prices WHERE source='ib_continuous' AND date >= ?", con, params=(start,))
    if d.empty: return {}
    w = d.pivot_table(index='date', columns='product', values='settle'); w.index = pd.to_datetime(w.index)
    return {c: w[c].dropna() for c in w}


def prices_yahoo(start='2024-01-01', end=None):
    d = yf.download(list(YAHOO.values()), start=start, end=end, progress=False, auto_adjust=False)['Close']
    return {k: d[v].dropna() for k, v in YAHOO.items() if v in d}


def prices(source='db', **kw):
    return prices_db(**kw) if source == 'db' else prices_yahoo(**kw)
