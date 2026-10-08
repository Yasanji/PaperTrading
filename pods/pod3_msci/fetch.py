"""Fetch MSCI Europe and MSCI Europe Small Cap holdings (Xtrackers), then full and free-float market caps from Yahoo by ISIN.
Usage: python fetch.py OUTDIR"""
import io, sys, json, datetime as dt, requests, pandas as pd, yfinance as yf
from concurrent.futures import ThreadPoolExecutor
H = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36'}
FUNDS = {'STANDARD': 'LU0274209237', 'SMALL': 'LU0322253906'}
out = sys.argv[1]; today = dt.date.today().isoformat()

def holdings(isin):
    raw = requests.get(f'https://etf.dws.com/etfdata/export/GBR/ENG/excel/product/constituent/{isin}/', headers=H, timeout=90).content
    d = pd.read_excel(io.BytesIO(raw), header=None); hdr = next(k for k in range(10) if 'ISIN' in [str(v) for v in d.iloc[k]])
    h = pd.read_excel(io.BytesIO(raw), header=hdr).dropna(subset=['ISIN'])
    return h[h['Type of Security'] == 'Equities']

frames = []
for seg, isin in FUNDS.items():
    h = holdings(isin); h['segment'] = seg; frames.append(h)
u = pd.concat(frames, ignore_index=True)[['segment', 'Name', 'ISIN', 'Country', 'Currency', 'Exchange', 'Primary Listing', 'Industry Classification', 'Weighting']]
u.columns = ['segment', 'name', 'isin', 'domicile', 'currency', 'exchange', 'primary_listing', 'sector', 'weight']
u = u[u.weight > 1e-6]                       # drop suspended stubs (e.g. weight 7e-10)

def info(isin):
    try:
        i = yf.Ticker(isin).info
        return dict(isin=isin, symbol=i.get('symbol'), mcap=i.get('marketCap'), y_ccy=i.get('currency'), fin_ccy=i.get('financialCurrency'),
                    float_shares=i.get('floatShares'), shares=i.get('sharesOutstanding'), implied_shares=i.get('impliedSharesOutstanding'),
                    price=i.get('currentPrice') or i.get('regularMarketPrice') or i.get('previousClose'), adv3m=i.get('averageDailyVolume3Month'),
                    y_country=i.get('country'), exch=i.get('exchange'))
    except Exception as e:
        return dict(isin=isin, error=str(e)[:200])

with ThreadPoolExecutor(8) as ex: rows = list(ex.map(info, u['isin'].tolist()))
m = u.merge(pd.DataFrame(rows), on='isin', how='left'); m['as_of'] = today
m.to_csv(f'{out}/universe_{today}.csv', index=False)
print(len(m), 'securities;', m.mcap.notna().sum(), 'with market cap')
