"""The book: collects each pod's targets, applies the portfolio rules, and writes the day's targets and orders.

Rules applied here (PORTFOLIO_PREREGISTRATION.md s.3): the 25% no-trade band, the 15-trading-day minimum holding
period, the order limit (10% of NAV) and the daily turnover cap (50% of NAV, DESIGN.md s.6.4). Pods size themselves
at their incubation or forward-test scale (config.SCALE). The 6% volatility overlay starts once the book has 126 days
of its own returns; until then the pods' target risks stand.

Outputs: book/targets/<date>.csv (committed to GitHub before any order) and book/orders/<date>.csv (for approve.py).
Usage: python book.py AS_OF [--source db|yahoo] [--positions FILE]"""
import os, sys, json, hashlib, argparse, sqlite3, datetime as dt, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import config as C, data
import importlib.util
def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
pod1 = _load('pod1', os.path.join(C.ROOT, 'pods', 'pod1', 'pod.py'))
sleeve_c = _load('sleeve_c', os.path.join(C.ROOT, 'pods', 'pod1', 'sleeve_c.py'))
pod4 = _load('pod4', os.path.join(C.ROOT, 'pods', 'pod4', 'pod.py'))
sys.path.insert(0, os.path.join(C.ROOT, 'pods', 'pod3'))            # pod3/orders.py imports its own pod.py as 'pod'
import pod as pod3
pod3_orders = _load('pod3_orders', os.path.join(C.ROOT, 'pods', 'pod3', 'orders.py'))

CC = pd.read_csv(C.CONTRACTS).set_index('found')
COLS = ['pod', 'symbol', 'sec_type', 'exchange', 'primary_exchange', 'currency', 'multiplier', 'target_qty', 'ref_price', 'notional_usd', 'reason',
        'sleeve_c', 'sleeve_c_prev']


def current_positions(path=None):
    """Latest reconciled positions, with the date each was opened. Columns: pod, symbol, qty, opened."""
    if path and os.path.exists(path): return pd.read_csv(path, parse_dates=['opened'])
    try:
        con = sqlite3.connect(C.DB)
        p = pd.read_sql("""SELECT p.date, p.pod, i.ticker AS symbol, p.qty FROM positions p JOIN instruments i USING(instrument_id)
                           WHERE p.date = (SELECT MAX(date) FROM positions)""", con)
        if p.empty: return pd.DataFrame(columns=['pod', 'symbol', 'qty', 'opened'])
        h = pd.read_sql("SELECT p.date, p.pod, i.ticker AS symbol, p.qty FROM positions p JOIN instruments i USING(instrument_id)", con)
        h['date'] = pd.to_datetime(h.date); opened = {}
        for (pd_, s), g in h.sort_values('date').groupby(['pod', 'symbol']):
            sign = np.sign(g.qty); start = g.date[(sign != sign.shift())].iloc[-1]; opened[(pd_, s)] = start
        p['opened'] = [opened.get((a, b)) for a, b in zip(p.pod, p.symbol)]
        return p
    except Exception:
        return pd.DataFrame(columns=['pod', 'symbol', 'qty', 'opened'])


def previous_signs(pos):
    return {r.symbol: int(np.sign(r.qty)) for r in pos.itertuples() if r.pod == 1 and r.qty != 0}


def pod1_rows(as_of, prices, pos):
    rates = pod1.oecd_rates((pd.Timestamp(as_of) - pd.DateOffset(months=6)).strftime('%Y-%m'))
    sc = sleeve_c.targets(as_of)
    t = pod1.targets(as_of, prices, rates, previous_signs(pos), sleeve=sc)
    rows = []
    for r in t.itertuples():
        c = CC.loc[r.market]; px = float(prices[r.market].iloc[-1])
        reason = f"trend {r.trend_sign if pd.notna(r.trend_sign) else '-'} (z {r.trend_z}), carry {r.carry_sign if pd.notna(r.carry_sign) else '-'}, exact {r.exact}"
        if r.sleeve_c or r.sleeve_c_prev: reason += f", sleeve C {r.sleeve_c:+d} (signal {sc['cal']:+.4f})"
        rows.append(dict(pod=1, symbol=r.market, sec_type='FUT', exchange=c.exchange, primary_exchange=c.exchange, currency=c.currency,
                         multiplier=c.multiplier, target_qty=r.contracts, ref_price=px, notional_usd=r.contracts * px * c.multiplier, reason=reason,
                         sleeve_c=r.sleeve_c, sleeve_c_prev=r.sleeve_c_prev))
    return rows


def pod3_rows(as_of):
    trade_day = (pd.Timestamp(as_of) + pd.tseries.offsets.BDay(1)).date().isoformat()   # orders fill at the next close
    tg, _ = pod3_orders.build(trade_day)
    rows = []
    for r in tg.itertuples():
        rows.append(dict(pod=3, symbol=r.ib_symbol, sec_type=r.sec_type, exchange=r.exchange, primary_exchange=r.primary_exchange,
                         currency=r.currency, multiplier=50 if r.sec_type == 'FUT' else 1, target_qty=r.target_qty, ref_price=r.price,
                         notional_usd=r.target_notional_usd, reason=r.reason))
    return rows


def apply_rules(t, pos, as_of):
    """No-trade band and minimum holding period, against current positions."""
    cur = {(r.pod, r.symbol): r for r in pos.itertuples()}
    out = []
    for r in t.itertuples(index=False):
        r = r._asdict(); c = cur.get((r['pod'], r['symbol']))
        num = lambda v: int(v) if pd.notna(v) else 0
        sc_now, sc_prev = num(r.get('sleeve_c')), num(r.get('sleeve_c_prev'))
        if sc_now or sc_prev:                        # rules apply to trend and carry only; Sleeve C passes through (sleeve s.4.1)
            r['target_qty'] -= sc_now
            if c is not None: c = c._replace(qty=c.qty - sc_prev)
        if c is not None and c.qty != 0:
            held = len(pd.bdate_range(c.opened, as_of)) - 1 if pd.notna(c.opened) else 99
            if held < C.MIN_HOLD_DAYS and (np.sign(r['target_qty']) != np.sign(c.qty) or abs(r['target_qty']) < abs(c.qty)) \
                    and 'exit' not in r['reason'] and r['pod'] not in (3, 4):   # Pods 3 and 4 exit by their own rules
                r['reason'] += f'; held {held} days < {C.MIN_HOLD_DAYS}: kept {c.qty}'; r['target_qty'] = c.qty
            elif np.sign(r['target_qty']) == np.sign(c.qty) and abs(r['target_qty'] - c.qty) <= C.NO_TRADE_BAND * abs(c.qty):
                r['reason'] += f'; within 25% band: kept {c.qty}'; r['target_qty'] = c.qty
        r['target_qty'] += sc_now
        out.append(r)
    for k, c in cur.items():                                   # positions no pod targets any more go to zero
        if c.qty != 0 and not any(o['pod'] == k[0] and o['symbol'] == k[1] for o in out):
            out.append(dict(pod=k[0], symbol=k[1], sec_type='', exchange='', primary_exchange='', currency='', multiplier=None,
                            target_qty=0, ref_price=None, notional_usd=0, reason='no longer targeted'))
    return pd.DataFrame(out, columns=COLS)


def orders(t, pos, nav=C.NAV):
    cur = {(r.pod, r.symbol): r.qty for r in pos.itertuples()}
    o = t.copy(); o['current_qty'] = [cur.get((a, b), 0) for a, b in zip(o.pod, o.symbol)]
    o['order_qty'] = o.target_qty - o.current_qty; o = o[o.order_qty != 0].copy()
    unit = (o.notional_usd / o.target_qty).replace([np.inf, -np.inf], np.nan)
    o['order_notional_usd'] = (o.order_qty * unit).abs()
    o['order_type'] = np.where(o.sec_type == 'FUT', 'MKT 10 min before settlement', 'MOC')
    o['flag'] = np.where(o.order_notional_usd > C.ORDER_LIMIT * nav, 'over 10% of NAV', '')
    return o


def run(as_of, source='db', positions=None, write=True):
    pos = current_positions(positions)
    prices = data.prices(source, start=(pd.Timestamp(as_of) - pd.DateOffset(months=18)).strftime('%Y-%m-%d'))
    problems = pod1.checks(prices, as_of) if source == 'db' else []
    rows = pod1_rows(as_of, prices, pos) + pod3_rows(as_of) + pod4.book_rows(as_of, pos)
    problems += pod4.checks(as_of)
    t = apply_rules(pd.DataFrame(rows, columns=COLS), pos, pd.Timestamp(as_of))
    o = orders(t, pos)
    turnover = o.order_notional_usd.sum()
    if turnover > C.DAILY_LIMIT * C.NAV: problems.append(f'turnover {turnover:,.0f} over 50% of NAV: batch held for review')
    meta = dict(as_of=str(as_of), source=source, pods={1: pod1.status(), 3: pod3.status(), 4: pod4.status()}, problems=problems,
                created=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'))
    if write:
        os.makedirs(C.TARGETS_DIR, exist_ok=True); os.makedirs(C.ORDERS_DIR, exist_ok=True)
        tf = os.path.join(C.TARGETS_DIR, f'{as_of}.csv'); t.to_csv(tf, index=False)
        meta['targets_sha256'] = hashlib.sha256(open(tf, 'rb').read()).hexdigest()
        json.dump(meta, open(os.path.join(C.TARGETS_DIR, f'{as_of}.json'), 'w'), indent=1)
        o.assign(batch_id=f'{as_of}-{meta["targets_sha256"][:8]}').to_csv(os.path.join(C.ORDERS_DIR, f'{as_of}.csv'), index=False)
    return t, o, meta


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('as_of'); a.add_argument('--source', default='db'); a.add_argument('--positions')
    a.add_argument('--no-write', action='store_true'); x = a.parse_args()
    t, o, meta = run(x.as_of, x.source, x.positions, not x.no_write)
    pd.set_option('display.width', 200)
    print(t[['pod', 'symbol', 'sec_type', 'target_qty', 'notional_usd', 'reason']].to_string(index=False))
    print('\nORDERS'); print(o[['pod', 'symbol', 'order_qty', 'order_type', 'order_notional_usd', 'flag']].round(0).to_string(index=False) if len(o) else 'none')
    print('\nproblems:', meta['problems'] or 'none')
