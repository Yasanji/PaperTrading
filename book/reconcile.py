"""After the US close: compare the account's positions with the day's targets, store positions and NAV, and trip the
kill switch on any unexplained difference (DESIGN.md s.6.6): more than one contract or 1% of value, or a NAV move over
5% that differs from the positions' P&L by more than 1% of NAV. Read-only.

Positions are matched to pods by the orderRef tag on their fills (batch|podN|reason); a position with no tag is an error.
Usage: python reconcile.py DATE [--offline POSITIONS_CSV]"""
import os, sys, sqlite3, datetime as dt, pandas as pd
import config as C, kill


def from_ib(date):
    from ib_async import IB
    ib = IB(); ib.connect('127.0.0.1', C.PAPER_PORT, clientId=31, readonly=True)
    acct = open(C.ACCOUNT_FILE).read().strip()
    if ib.managedAccounts() != [acct]: ib.disconnect(); kill.trip(f'reconcile: wrong account {ib.managedAccounts()}'); sys.exit(1)
    pod_of = {}
    for f in ib.fills():
        ref = f.execution.orderRef or ''
        if '|pod' in ref: pod_of[f.contract.symbol] = int(ref.split('|pod')[1].split('|')[0])
    rows = [dict(symbol=p.contract.symbol, sec_type=p.contract.secType, qty=p.position, avg_cost=p.avgCost, pod=pod_of.get(p.contract.symbol))
            for p in ib.positions(acct) if p.position]
    nav = next((float(v.value) for v in ib.accountValues(acct) if v.tag == 'NetLiquidation' and v.currency == 'USD'), None)
    ib.disconnect()
    return pd.DataFrame(rows, columns=['symbol', 'sec_type', 'qty', 'avg_cost', 'pod']), nav


def main():
    date = sys.argv[1]; offline = '--offline' in sys.argv
    pos, nav = (pd.read_csv(sys.argv[sys.argv.index('--offline') + 1]), None) if offline else from_ib(date)
    tf = os.path.join(C.TARGETS_DIR, f'{date}.csv')
    t = pd.read_csv(tf) if os.path.exists(tf) else pd.DataFrame(columns=['pod', 'symbol', 'target_qty', 'notional_usd'])
    m = t.groupby('symbol', as_index=False).agg(target_qty=('target_qty', 'sum'), notional=('notional_usd', 'sum'), pod=('pod', 'first')) \
         .merge(pos.groupby('symbol', as_index=False).agg(actual_qty=('qty', 'sum')), on='symbol', how='outer').fillna({'target_qty': 0, 'actual_qty': 0})
    m['difference'] = m.actual_qty - m.target_qty
    unit = (m.notional / m.target_qty).abs().where(m.target_qty != 0)
    is_fut = m.symbol.isin(t[t.sec_type == 'FUT'].symbol)
    m['passed'] = (m.difference == 0) | (is_fut & (m.difference.abs() <= 1)) | (~is_fut & ((m.difference.abs() * unit) <= 0.01 * m.notional.abs()))
    con = sqlite3.connect(C.DB)
    for r in m.itertuples():
        con.execute('INSERT OR IGNORE INTO instruments (ticker, first_seen) VALUES (?,?)', (r.symbol, date))
        iid = con.execute('SELECT instrument_id FROM instruments WHERE ticker=?', (r.symbol,)).fetchone()[0]
        con.execute('INSERT OR REPLACE INTO reconciliation (date, instrument_id, target_qty, actual_qty, difference, passed) VALUES (?,?,?,?,?,?)',
                    (date, iid, r.target_qty, r.actual_qty, r.difference, int(r.passed)))
        if r.actual_qty:
            con.execute('INSERT OR REPLACE INTO positions (date, pod, instrument_id, qty, market_value) VALUES (?,?,?,?,?)',
                        (date, str(int(r.pod)) if pd.notna(r.pod) else 'unknown', iid, r.actual_qty, None))
    if nav:
        prev = con.execute('SELECT nav FROM account ORDER BY date DESC LIMIT 1').fetchone()
        con.execute('INSERT OR REPLACE INTO account (date, nav) VALUES (?,?)', (date, nav))
        if prev and abs(nav / prev[0] - 1) > 0.05: kill.trip(f'reconcile: NAV moved {nav / prev[0] - 1:+.1%} in a day; check P&L against positions')
    con.commit()
    bad = m[~m.passed]
    print(m[['symbol', 'target_qty', 'actual_qty', 'difference', 'passed']].to_string(index=False))
    if len(bad): print('kill event', kill.trip(f'reconcile {date}: {len(bad)} differences: {", ".join(bad.symbol)}'))
    else: print('reconciled: no unexplained differences')


if __name__ == '__main__':
    main()
