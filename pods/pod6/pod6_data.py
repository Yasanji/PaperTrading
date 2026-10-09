"""Pod 6 data: Cboe daily settlements for every VIX futures contract, 2005 to 2026, the VIX index and the S&P 500.
Old contracts (to 2013) come from Cboe's CFE archive; later ones from the per-expiry files. Writes vx_settles.csv
(date, expiry, settle) and index.csv (VIX, S&P 500). VIX futures were quoted at ten times the index before 26 March 2007;
those settlements are divided by ten."""
import io, requests, pandas as pd, yfinance as yf
MC = 'FGHJKMNQUVXZ'; H = {'User-Agent': 'Mozilla/5.0'}; rows = []
def get(u):
    r = requests.get(u, headers=H, timeout=30)
    return pd.read_csv(io.StringIO(r.text), index_col=False, usecols=['Trade Date', 'Futures', 'Settle']) if r.status_code == 200 and r.text.startswith('Trade Date') else None
for y in range(2005, 2015):                                       # archive: CFE_<month code><yy>_VX.csv
    for m in MC:
        d = get(f'https://cdn.cboe.com/resources/futures/archive/volume-and-price/CFE_{m}{y % 100:02d}_VX.csv')
        if d is not None: d['src'] = 'archive'; rows.append(d)
# per-expiry files: try each Tuesday/Wednesday/Monday around the standard expiry (Wednesday 30 days before the next month's third Friday)
for y in range(2013, 2027):
    for mo in range(1, 13):
        nxt = pd.Timestamp(y, mo, 1) + pd.offsets.MonthBegin(1)
        f3 = pd.date_range(nxt, nxt + pd.offsets.MonthEnd(0), freq='W-FRI')[2]; exp = f3 - pd.Timedelta(days=30)
        for k in (0, -1, 1, -2):
            d = get(f'https://cdn.cboe.com/data/us/futures/market_statistics/historical_data/VX/VX_{(exp + pd.Timedelta(days=k)).date()}.csv')
            if d is not None: d['src'] = 'expiry'; rows.append(d); break
v = pd.concat(rows); v['date'] = pd.to_datetime(v['Trade Date'], format='mixed'); v = v[v.Settle > 0]
v['expiry'] = v.groupby('Futures').date.transform('max')          # last trade date in each contract's file
v['settle'] = v.Settle.where(v.date >= '2007-03-26', v.Settle / 10)
v = v.sort_values('src').drop_duplicates(['date', 'Futures'], keep='last')   # prefer the per-expiry file where both exist
v[['date', 'Futures', 'expiry', 'settle']].sort_values(['date', 'expiry']).to_csv('vx_settles.csv', index=False)
ix = yf.download(['^VIX', '^GSPC'], start='2004-06-01', end='2026-10-01', progress=False, auto_adjust=True)['Close']
ix.rename(columns={'^VIX': 'vix', '^GSPC': 'spx'}).to_csv('index.csv')
print(v.Futures.nunique(), 'contracts,', v.date.min().date(), 'to', v.date.max().date())
