"""Evening job: daily closes for every traded contract-check market, into delta1.db (futures_prices).

Tries Interactive Brokers first (continuous contract, read-only), one market at a time with a longer timeout.
A market IB does not return (no data permission on the paper account, or a timeout) falls back to Yahoo's continuous
future, stored with source 'yahoo_continuous' and reported, so the signals can still be checked during the dry run.
Usage: python futures_ib.py [--yahoo-only]"""
import sys, datetime as dt, sqlite3, pandas as pd
import config as C

def store(con, rows, source, now):
    return sum(con.execute('INSERT OR IGNORE INTO futures_prices (date, product, expiry, settle, source, retrieved_at) VALUES (?,?,?,?,?,?)',
                           (d, p, '', float(v), source, now)).rowcount for d, p, v in rows)

def main():
    cc = pd.read_csv(C.CONTRACTS); cc = cc[cc.verdict.str.startswith('TRADED') | (cc.use == 'hedge')]
    con = sqlite3.connect(C.DB); now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')
    got, missing, n = set(), [], 0
    if '--yahoo-only' not in sys.argv:
        from ib_async import IB, ContFuture
        ib = IB(); ib.connect('127.0.0.1', C.PAPER_PORT, clientId=11, readonly=True)
        ib.RequestTimeout = 0
        for _, r in cc.iterrows():
            cf = ContFuture(r.found, r.exchange, currency=r.currency)
            try:
                if not ib.qualifyContracts(cf): raise RuntimeError('not qualified')
                bars = ib.reqHistoricalData(cf, '', '1 Y', '1 day', 'TRADES', useRTH=True, formatDate=1, timeout=180)
                if not bars: raise RuntimeError('no bars')
                n += store(con, [(str(b.date), r.found, b.close) for b in bars], 'ib_continuous', now); got.add(r.found)
                print(f'{r.found}: {len(bars)} bars from IB, last {bars[-1].date}')
            except Exception as e:
                missing.append(r.found); print(f'{r.found}: IB failed ({e})')
            ib.sleep(2)
        ib.disconnect()
    rest = [f for f in cc.found if f not in got]
    if rest:
        import data
        y = data.prices_yahoo(start=(dt.date.today() - dt.timedelta(days=550)).isoformat())
        for f in rest:
            if f in y:
                n += store(con, [(d.date().isoformat(), f, v) for d, v in y[f].items()], 'yahoo_continuous', now)
                print(f'{f}: {len(y[f])} closes from Yahoo (fallback)')
    con.commit(); print(f'rows added: {n}; from IB: {len(got)}; Yahoo fallback: {len(rest)}')

if __name__ == '__main__':
    main()
