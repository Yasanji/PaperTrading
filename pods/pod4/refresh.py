"""Pod 4: refresh the data the daily run needs. Run once a day before the evening chain (it takes several minutes).

Writes to delta1/pod4/ (not committed):
  prices.csv, volume.csv   last 400 days of split-adjusted closes and volume for the Sleeve B universe
  dividends.csv            dividends by ex-date over three years (Yahoo, split-adjusted), merged with the frozen history if present
  indices.csv              ^STOXX, ^GSPC, ^HSI and EURUSD, HKDUSD for the last 400 days
  exdates.csv              announced next ex-dividend dates (Yahoo calendar) for the stocks the pod holds or may enter soon
Usage: python refresh.py [--exdates-only TICKER,...]"""
import os, sys, time, pandas as pd, yfinance as yf
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(ROOT, 'delta1', 'pod4'); UNIVERSE = os.path.join(ROOT, 'carry', 'sleeveB', 'universe_frozen.csv')


def exdates(tickers):
    rows = []
    for t in tickers:
        try:
            v = yf.Ticker(t).calendar.get('Ex-Dividend Date')
            rows.append(dict(yahoo=t, exdate=pd.Timestamp(v).date().isoformat() if v else None))
        except Exception:
            rows.append(dict(yahoo=t, exdate=None))
        time.sleep(0.2)
    return pd.DataFrame(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    if '--exdates-only' in sys.argv:
        exdates(sys.argv[sys.argv.index('--exdates-only') + 1].split(',')).to_csv(os.path.join(OUT, 'exdates.csv'), index=False); return
    T = list(pd.read_csv(UNIVERSE).yahoo); P, V, D = [], [], []
    for i in range(0, len(T), 80):
        for attempt in range(3):
            try:
                x = yf.download(T[i:i + 80], period='3y', auto_adjust=False, actions=True, progress=False); break
            except Exception:
                time.sleep(20)
        P.append(x['Close']); V.append(x['Volume'])
        D.append(x['Dividends'].stack().rename('dividend').reset_index().query('dividend > 0'))
    pd.concat(P, axis=1).iloc[-400:].to_csv(os.path.join(OUT, 'prices.csv'))
    pd.concat(V, axis=1).iloc[-400:].to_csv(os.path.join(OUT, 'volume.csv'))
    new = pd.concat(D); new.columns = ['date', 'yahoo', 'dividend']
    hist = os.path.join(ROOT, 'carry', 'sleeveB', 'data', 'dividends.csv')     # older history from the frozen download
    old = pd.read_csv(hist) if os.path.exists(hist) else pd.DataFrame(columns=new.columns)
    dv = pd.concat([old, new.assign(date=new.date.astype(str).str[:10])]).drop_duplicates(['date', 'yahoo'], keep='last')
    dv.to_csv(os.path.join(OUT, 'dividends.csv'), index=False)
    ix = yf.download(['^STOXX', '^GSPC', '^HSI', 'EURUSD=X', 'HKDUSD=X'], period='2y', progress=False, auto_adjust=True)['Close']
    ix.iloc[-400:].to_csv(os.path.join(OUT, 'indices.csv'))
    print(f'pod4 refresh: {len(T)} stocks, {len(dv)} dividends, prices to {pd.concat(P, axis=1).index[-1].date()}')


if __name__ == '__main__':
    main()
