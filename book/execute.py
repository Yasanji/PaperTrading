"""Send the day's approved orders to the Interactive Brokers paper account (DESIGN.md s.4 and s.6).

Dry run by default: every check runs and the orders are built, but nothing is placed. Sending needs --send, and also
needs the API out of read-only mode in both IB Gateway and IBC (only after the 10-day dry run, DESIGN.md s.12.10).

Checks, in order (any failure stops the batch and is recorded):
  1. no open kill event;  2. the targets file is committed and pushed, and its checksum matches;
  3. an approval exists for this exact orders file;  4. the batch has not been sent before;
  5. connected through the paper port to the paper account stored in ~/.delta1/paper_account (and it starts with DU);
  6. per order: reference price within 10% of the last close, size no more than twice the target, notional <= 10% of NAV.
Futures go to the front contract that is not within 5 business days of its last trade date (or of the first day of
its delivery month for physically delivered contracts); open positions in an older contract are rolled.

Usage: python execute.py DATE [--send] [--offline]"""
import os, sys, json, hashlib, subprocess, sqlite3, datetime as dt, argparse
from zoneinfo import ZoneInfo
import pandas as pd
import config as C, kill

PHYSICAL = {'ZT', 'ZN', 'SIC'}                     # roll before the delivery month
SETTLE = {  # product: (exchange time zone, settlement time)
    'MES': ('America/Chicago', '15:00'), 'ZT': ('America/Chicago', '14:00'), 'ZN': ('America/Chicago', '14:00'),
    'MCL': ('America/Chicago', '13:30'), 'MHNG': ('America/Chicago', '13:30'), 'SIC': ('America/Chicago', '12:25'),
    'MHG': ('America/Chicago', '12:00'), 'M6E': ('America/Chicago', '14:00'), 'MJY': ('America/Chicago', '14:00'),
    'M6B': ('America/Chicago', '14:00'), 'M6A': ('America/Chicago', '14:00'), 'MCD': ('America/Chicago', '14:00'),
    'MSF': ('America/Chicago', '14:00'), 'NZD': ('America/Chicago', '14:00'), 'DJ600': ('Europe/Berlin', '17:30'),
    'VXM': ('America/Chicago', '15:00')}


def stop(msg):
    eid = kill.trip(f'execute.py: {msg}'); sys.exit(f'STOPPED (kill event {eid}): {msg}')


def sha(path): return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def git(*a): return subprocess.run(['git', '-C', C.ROOT, *a], capture_output=True, text=True)


def committed(path):
    """The file as committed equals the file on disk, and that commit is on origin/main."""
    rel = os.path.relpath(path, C.ROOT)
    c = git('log', '-1', '--format=%H', '--', rel).stdout.strip()
    if not c or git('diff', '--quiet', c, '--', rel).returncode != 0: return None
    git('fetch', '-q', 'origin')
    return c if git('merge-base', '--is-ancestor', c, 'origin/main').returncode == 0 else None


def roll_date(last_trade, symbol):
    lt = pd.Timestamp(last_trade[:8])
    anchor = lt.replace(day=1) if symbol in PHYSICAL else lt
    return anchor - pd.tseries.offsets.BDay(C.ROLL_BDAYS)


def front(ib, symbol, exchange, currency, today):
    from ib_async import Future
    ds = ib.reqContractDetails(Future(symbol, exchange=exchange, currency=currency))
    ds = sorted(ds, key=lambda d: d.contract.lastTradeDateOrContractMonth)
    for d in ds:
        if roll_date(d.contract.lastTradeDateOrContractMonth, symbol) > today: return d.contract
    raise RuntimeError(f'no contract for {symbol}')


def good_after(symbol, date):
    tz, t = SETTLE[symbol]
    ts = pd.Timestamp(f'{date} {t}').tz_localize(ZoneInfo(tz)) - pd.Timedelta(minutes=10)
    return ts.tz_convert('UTC').strftime('%Y%m%d-%H:%M:%S')


def main():
    a = argparse.ArgumentParser(); a.add_argument('date'); a.add_argument('--send', action='store_true'); a.add_argument('--offline', action='store_true')
    x = a.parse_args(); date = x.date; today = pd.Timestamp(date)
    of, tf = os.path.join(C.ORDERS_DIR, f'{date}.csv'), os.path.join(C.TARGETS_DIR, f'{date}.csv')
    if kill.is_killed(): sys.exit(f'Kill switch on: {kill.open_events()}. Nothing sent.')
    meta = json.load(open(os.path.join(C.TARGETS_DIR, f'{date}.json')))
    if sha(tf) != meta['targets_sha256']: stop('targets file changed since it was written')
    commit = committed(tf)
    if not commit and not x.offline: stop('targets file is not committed and pushed to origin/main')
    ap = os.path.join(C.ORDERS_DIR, f'{date}.approved.json')
    if not os.path.exists(ap): sys.exit('No approval for this batch: run approve.py. Nothing sent.')
    approval = json.load(open(ap))
    if approval['orders_sha256'] != sha(of): stop('orders file changed after approval')
    o = pd.read_csv(of); o = o[o.symbol.isin(approval['approved'])]
    batch = str(o.batch_id.iloc[0]) if len(o) else f'{date}-empty'
    con = sqlite3.connect(C.DB)
    if con.execute("SELECT COUNT(*) FROM events WHERE kind='batch_sent' AND detail LIKE ?", (f'%{batch}%',)).fetchone()[0]:
        sys.exit(f'Batch {batch} was already sent. Nothing sent.')
    if meta['problems'] and not approval.get('reason'): stop(f"unresolved problems: {meta['problems']}")
    t = pd.read_csv(tf).set_index(['pod', 'symbol'])
    for r in o.itertuples():
        tq = t.loc[(r.pod, r.symbol), 'target_qty'] if (r.pod, r.symbol) in t.index else 0
        if abs(r.order_qty) > 2 * max(abs(tq), abs(r.current_qty)): stop(f'{r.symbol}: order {r.order_qty} more than twice the target')
        if r.order_notional_usd > C.ORDER_LIMIT * C.NAV: stop(f'{r.symbol}: order over 10% of NAV')
    if x.offline:
        print(f'OFFLINE dry run, batch {batch}, targets commit {commit or "not pushed"}:'); print(o[['pod', 'symbol', 'order_qty', 'order_type']].to_string(index=False)); return

    from ib_async import IB, Stock, Future, Order
    ib = IB(); ib.connect('127.0.0.1', C.PAPER_PORT, clientId=21, readonly=not x.send)
    acct = open(C.ACCOUNT_FILE).read().strip()
    if ib.managedAccounts() != [acct] or not acct.startswith('DU'): stop(f'connected to {ib.managedAccounts()}, expected paper account')
    plan = []
    held = {p.contract.conId: p for p in ib.positions(acct)}
    for r in o.itertuples():
        if r.sec_type == 'FUT':
            c = front(ib, r.symbol, r.exchange, r.currency, today)
            for p in held.values():                                    # roll: close older contracts of this product
                if p.contract.symbol == c.symbol and p.contract.conId != c.conId and p.position:
                    plan.append((p.contract, -p.position, 'roll out', r))
            o_qty = r.order_qty
        else:
            c = Stock(r.symbol, 'SMART', r.currency, primaryExchange=r.primary_exchange); o_qty = r.order_qty
        ib.qualifyContracts(c)
        bars = ib.reqHistoricalData(c, '', '5 D', '1 day', 'TRADES', useRTH=True)
        last = bars[-1].close if bars else None
        ref = r.ref_price
        if last and r.currency == 'GBP' and pd.notna(ref) and last / ref > 50: last /= 100      # London quoted in pence
        if last and pd.notna(ref) and abs(last / ref - 1) > C.PRICE_SANITY:
            stop(f'{r.symbol}: reference price {ref} vs last close {last}')
        plan.append((c, o_qty, r.order_type, r))
    print(f'batch {batch}: {len(plan)} orders'); sent = []
    for c, qty, kind, r in plan:
        side = 'BUY' if qty > 0 else 'SELL'
        if c.secType == 'STK': order = Order(action=side, totalQuantity=abs(qty), orderType='MOC', account=acct)
        else: order = Order(action=side, totalQuantity=abs(qty), orderType='MKT', goodAfterTime=good_after(r.symbol, date), tif='DAY', account=acct)
        order.orderRef = f'{batch}|pod{r.pod}|{kind}'
        print(f'{"SEND" if x.send else "DRY"} {side} {abs(qty)} {c.localSymbol or c.symbol} {order.orderType} {getattr(order, "goodAfterTime", "")}')
        if x.send:
            tr = ib.placeOrder(c, order); sent.append(tr.order.orderId)
            con.execute('INSERT INTO orders (date, pod, instrument_id, qty, order_type, sent_at, status) VALUES (?,?,?,?,?,?,?)',
                        (date, r.pod, None, qty, order.orderType, dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'), 'sent'))
    if x.send:
        con.execute('INSERT INTO events (at, kind, detail) VALUES (?,?,?)',
                    (dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'), 'batch_sent', json.dumps(dict(batch=batch, orders=sent, commit=commit))))
        con.commit()
    ib.disconnect()


if __name__ == '__main__':
    main()
