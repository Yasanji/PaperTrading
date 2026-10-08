"""Evening job: daily bars for every contract-check market from Interactive Brokers, into delta1.db.

Stores continuous-contract closes (source 'ib_continuous', for signals) and the front contract's details
(source 'ib_front', for sizing and rolls). Read-only API is enough. Usage: python futures_ib.py"""
import datetime as dt, sqlite3, pandas as pd
from ib_async import IB, ContFuture, Future
import config as C

def main():
    cc = pd.read_csv(C.CONTRACTS); cc = cc[cc.found.notna()]
    ib = IB(); ib.connect('127.0.0.1', C.PAPER_PORT, clientId=11, readonly=True)
    con = sqlite3.connect(C.DB); now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'); n = 0
    for _, r in cc.iterrows():
        cf = ContFuture(r.found, r.exchange, currency=r.currency)
        if not ib.qualifyContracts(cf): print('not found:', r.found); continue
        bars = ib.reqHistoricalData(cf, '', '2 Y', '1 day', 'TRADES', useRTH=False, formatDate=1)
        for b in bars:
            n += con.execute('INSERT OR IGNORE INTO futures_prices (date, product, expiry, settle, source, retrieved_at) VALUES (?,?,?,?,?,?)',
                             (str(b.date), r.found, '', b.close, 'ib_continuous', now)).rowcount
        ib.sleep(1)
    con.commit(); ib.disconnect(); print('futures_ib rows added:', n)

if __name__ == '__main__':
    main()
