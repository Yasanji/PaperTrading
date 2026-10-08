"""delta1 collector. Usage: python collect.py init | sx5e | divs | msci_europe | estr | levels | divfcst | all, or fexd EXPIRY PRICE
Appends to delta1.db (point in time: rows are added, never updated). Keep delta1.db off GitHub and back it up."""
import io, sys, sqlite3, datetime as dt, requests, numpy as np, pandas as pd, yfinance as yf
DB, H = 'delta1.db', {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36'}
NOW, TODAY = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'), dt.date.today().isoformat()
con = sqlite3.connect(DB); con.execute('PRAGMA foreign_keys = ON')

def run(command):
    cur = con.execute('INSERT INTO runs (command, started_at, status) VALUES (?,?,?)', (command, NOW, 'started')); return cur.lastrowid
def finish(run_id, n, status='ok', notes=''):
    con.execute('UPDATE runs SET finished_at=?, status=?, rows_added=?, notes=? WHERE run_id=?', (dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'), status, n, notes, run_id)); con.commit()
def inst(ticker, **kw):
    con.execute('INSERT OR IGNORE INTO instruments (ticker, isin, name, country, sector, currency, first_seen) VALUES (?,?,?,?,?,?,?)',
                (ticker, kw.get('isin'), kw.get('name'), kw.get('country'), kw.get('sector'), kw.get('currency'), TODAY))
    return con.execute('SELECT instrument_id FROM instruments WHERE ticker=?', (ticker,)).fetchone()[0]
def add(table, row):
    cols = ','.join(row); q = ','.join('?' * len(row))
    return con.execute(f'INSERT OR IGNORE INTO {table} ({cols}) VALUES ({q})', tuple(row.values())).rowcount

def init():
    con.executescript(open('schema.sql').read()); print('database ready:', DB)

def sx5e():
    """EURO STOXX 50 members and free-float weights (10% cap), as a dated snapshot."""
    r = run('sx5e'); n = 0
    c = pd.read_html(io.StringIO(requests.get('https://en.wikipedia.org/wiki/EURO_STOXX_50', headers=H, timeout=60).text))[3]
    c['Ticker'] = c.Ticker.replace({'VOW.DE': 'VOW3.DE'})          # the index holds Volkswagen's preference shares
    rows = []
    for _, x in c.iterrows():
        i = yf.Ticker(x.Ticker).info; px = i.get('currentPrice') or i.get('regularMarketPrice') or i.get('previousClose')
        ff = (i.get('floatShares') or 0) * (px or 0) or i.get('marketCap') or 0
        rows.append((x.Ticker, x.Name, x['Registered office'], x.Sector, i.get('currency'), ff))
    w = pd.Series([z[5] for z in rows], dtype=float); w = w / w.sum()
    for _ in range(20):                                              # 10% cap, excess spread in proportion
        over = w > 0.10
        if not over.any(): break
        ex = (w[over] - 0.10).sum(); w[over] = 0.10; w[~over] += ex * w[~over] / w[~over].sum()
    for (t, name, country, sector, ccy, _), wt in zip(rows, w):
        n += add('index_membership', dict(as_of=TODAY, index_code='SX5E', instrument_id=inst(t, name=name, country=country, sector=sector, currency=ccy), weight=float(wt), source='wikipedia+yahoo free float, 10% cap', run_id=r))
    finish(r, n); print('sx5e rows added:', n)

def divs():
    """Actual dividend history and Yahoo's forward dividend, for every instrument in the latest SX5E snapshot."""
    r = run('divs'); n = 0
    tick = [t for (t,) in con.execute("SELECT i.ticker FROM index_membership m JOIN instruments i USING(instrument_id) WHERE m.index_code='SX5E' AND m.as_of=(SELECT MAX(as_of) FROM index_membership WHERE index_code='SX5E')")]
    for t in tick:
        iid = inst(t); tk = yf.Ticker(t); d = tk.dividends; i = tk.info
        for ex, amt in d.items():
            n += add('dividends_actual', dict(instrument_id=iid, ex_date=pd.Timestamp(ex).date().isoformat(), amount=float(amt), currency=i.get('currency'), kind='as reported', source='yahoo', retrieved_at=NOW))
        exd = i.get('exDividendDate')
        n += add('dividend_snapshots', dict(as_of=TODAY, instrument_id=iid, forward_rate=i.get('dividendRate'), next_ex_date=dt.datetime.fromtimestamp(exd, dt.timezone.utc).date().isoformat() if exd else None, last_value=i.get('lastDividendValue'), source='yahoo'))
    finish(r, n); print('divs rows added:', n)

def msci_europe():
    """MSCI Europe members and weights from the Xtrackers MSCI Europe fund (LU0274209237)."""
    r = run('msci_europe'); n = 0
    raw = requests.get('https://etf.dws.com/etfdata/export/GBR/ENG/excel/product/constituent/LU0274209237/', headers=H, timeout=90).content
    d = pd.read_excel(io.BytesIO(raw), header=None); hdr = next(k for k in range(10) if 'ISIN' in [str(v) for v in d.iloc[k]])
    h = pd.read_excel(io.BytesIO(raw), header=hdr).dropna(subset=['ISIN'])
    for _, x in h.iterrows():
        iid = inst('ISIN:' + x.ISIN, isin=x.ISIN, name=x.Name, country=x.Country, sector=x['Industry Classification'], currency=x.Currency)
        n += add('index_membership', dict(as_of=TODAY, index_code='MSCI_EUROPE', instrument_id=iid, weight=float(x.Weighting), source='xtrackers holdings', run_id=r))
    finish(r, n); print('msci_europe rows added:', n)

def estr():
    """Euro short-term rate from the ECB."""
    r = run('estr'); n = 0
    e = pd.read_csv(io.StringIO(requests.get('https://data-api.ecb.europa.eu/service/data/EST/B.EU000A2X2A25.WT?format=csvdata&lastNObservations=30', timeout=60).text))
    for _, x in e.iterrows(): n += add('rates', dict(date=x.TIME_PERIOD, series='ESTR', value=float(x.OBS_VALUE), source='ecb', retrieved_at=NOW))
    finish(r, n); print('estr rows added:', n)

def levels():
    """EURO STOXX 50 index level (spot), last month."""
    r = run('levels'); n = 0
    s = yf.download('^STOXX50E', period='1mo', progress=False, auto_adjust=False)['Close'].squeeze().dropna()
    for d, v in s.items(): n += add('index_levels', dict(date=d.date().isoformat(), index_code='SX5E', value=float(v), source='yahoo', retrieved_at=NOW))
    finish(r, n); print('levels rows added:', n)

def divfcst():
    """EURO STOXX 50 dividend points: this futures year (realised and expected) and next year (flat and bottom-up)."""
    sys.path.insert(0, 'dividends'); import model
    r = run('divfcst'); n = 0
    s, out, _ = model.run(g_rest=0.05)
    for measure, yr, pts, note in [('realised', s['current_year'], s['current_realised'], 'ex-dates to date'),
                                   ('expected', s['current_year'], s['current_expected'], "realised plus last year's remaining payments"),
                                   ('flat', s['current_year'] + 1, s['next_flat'], 'last 12 months repeated'),
                                   ('bottom_up', s['current_year'] + 1, s['next_bottom_up'], 'dps_inputs.csv; others +5%')]:
        n += add('dividend_forecast_summary', dict(as_of=TODAY, index_code='SX5E', futures_year=yr, measure=measure, points=pts, assumption=note, run_id=r))
    for sym, x in out.iterrows():
        iid = inst(sym)
        for basis in ['flat', 'bottom_up']:
            n += add('forecasts', dict(as_of=TODAY, index_code='SX5E', period=str(s['current_year'] + 1), instrument_id=iid, expected_ex_date='', amount=None, index_points=float(x[basis]), basis=basis))
    finish(r, n); print('divfcst rows added:', n, s)

def fexd():
    """Record a EURO STOXX 50 dividend futures price by hand: python collect.py fexd 2027-12-17 189.10 [source]"""
    r = run('fexd'); exp, px = sys.argv[2], float(sys.argv[3]); src = sys.argv[4] if len(sys.argv) > 4 else 'manual'
    n = add('futures_prices', dict(date=TODAY, product='FEXD', expiry=exp, settle=px, source=src, retrieved_at=NOW))
    finish(r, n); print('fexd rows added:', n)

JOBS = dict(init=init, sx5e=sx5e, divs=divs, msci_europe=msci_europe, estr=estr, levels=levels, divfcst=divfcst, fexd=fexd)
if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'all'
    for job in (['init', 'sx5e', 'divs', 'msci_europe', 'estr', 'levels', 'divfcst'] if cmd == 'all' else [cmd]):
        try: JOBS[job]()
        except Exception as e:
            print(f'{job} failed: {e}'); con.execute('INSERT INTO events (at, kind, detail) VALUES (?,?,?)', (NOW, 'collector_error', f'{job}: {e}')); con.commit()
