"""Download once (PREREGISTRATION.md s.3): Yahoo daily Close (auto_adjust off), Adj Close, Volume and dividends by
ex-date from 1 January 2004, and each stock's Yahoo sector. Writes data/prices_<field>.csv, data/dividends.csv,
data/sectors.csv and MANIFEST.md (file, rows, SHA-256), dated."""
import hashlib, time, datetime as dt, pandas as pd, yfinance as yf
u = pd.read_csv('data/universe.csv'); T = list(u.yahoo)
F = {k: [] for k in ('Close', 'Adj Close', 'Volume')}; D = []
for i in range(0, len(T), 60):
    b = T[i:i + 60]
    for attempt in range(3):
        try:
            x = yf.download(b, start='2004-01-01', end='2026-10-01', auto_adjust=False, actions=True, progress=False, threads=True); break
        except Exception as e: time.sleep(20)
    for k in F: F[k].append(x[k])
    D.append(x['Dividends'].stack().rename('dividend').reset_index().query('dividend > 0'))
    time.sleep(2)
for k, v in F.items(): pd.concat(v, axis=1).dropna(how='all', axis=1).to_csv(f'data/prices_{k.replace(" ", "_").lower()}.csv')
dv = pd.concat(D); dv.columns = ['date', 'yahoo', 'dividend']; dv.to_csv('data/dividends.csv', index=False)
sec = []
for t in T:
    s = None
    for attempt in range(3):
        try: s = yf.Ticker(t).info.get('sector'); break
        except Exception: time.sleep(5)
    sec.append(dict(yahoo=t, sector=s)); time.sleep(0.3)
pd.DataFrame(sec).to_csv('data/sectors.csv', index=False)
rows = []
for f in ['universe.csv', 'prices_close.csv', 'prices_adj_close.csv', 'prices_volume.csv', 'dividends.csv', 'sectors.csv']:
    b = open('data/' + f, 'rb').read(); rows.append(f'| {f} | {b.count(chr(10).encode()) - 1} | {hashlib.sha256(b).hexdigest()} |')
open('MANIFEST.md', 'w').write(f'# Sleeve B data manifest\n\nDownloaded {dt.date.today()} from Yahoo Finance (prices, dividends, sectors) and Wikipedia (revisions in sleeveB_universe.py). Data not redistributed.\n\n| File | Rows | SHA-256 |\n| --- | --- | --- |\n' + '\n'.join(rows) + '\n')
print(open('MANIFEST.md').read()); print('sectors missing:', sum(s['sector'] is None for s in sec))
