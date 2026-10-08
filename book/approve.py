"""Approve or reject the day's orders (DESIGN.md s.12.7). Writes book/orders/<date>.approved.json; execute.py sends
only approved rows of an approved batch. Every decision is recorded in delta1.db events.

  python approve.py DATE                  show the batch
  python approve.py DATE all              approve every order
  python approve.py DATE none             reject the batch
  python approve.py DATE except SYM,SYM   approve all but the listed symbols
Add  --reason "text"  to approve a batch held for being over the 50% turnover cap."""
import os, sys, json, hashlib, datetime as dt, pandas as pd
import config as C, kill

date = sys.argv[1]; f = os.path.join(C.ORDERS_DIR, f'{date}.csv')
o = pd.read_csv(f); meta = json.load(open(os.path.join(C.TARGETS_DIR, f'{date}.json')))
pd.set_option('display.width', 200)
print(o[['pod', 'symbol', 'sec_type', 'order_qty', 'order_type', 'order_notional_usd', 'flag', 'reason']].to_string(index=False))
print(f"\nturnover ${o.order_notional_usd.sum():,.0f} ({o.order_notional_usd.sum() / C.NAV:.0%} of NAV); problems: {meta['problems'] or 'none'}; "
      f"kill switch: {'ON' if kill.is_killed() else 'off'}")
if len(sys.argv) < 3: sys.exit()
mode = sys.argv[2]; reason = sys.argv[sys.argv.index('--reason') + 1] if '--reason' in sys.argv else ''
held = any('50%' in p for p in meta['problems'])
if held and mode != 'none' and not reason: sys.exit('Batch is over the 50% turnover cap: add --reason "..." to approve it.')
skip = set(sys.argv[3].split(',')) if mode == 'except' else set()
ok = [] if mode == 'none' else [s for s in o.symbol if s not in skip]
rec = dict(date=date, batch_id=str(o.batch_id.iloc[0]) if len(o) else '', approved=ok, rejected=[s for s in o.symbol if s not in ok],
           orders_sha256=hashlib.sha256(open(f, 'rb').read()).hexdigest(), reason=reason, at=dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'))
json.dump(rec, open(os.path.join(C.ORDERS_DIR, f'{date}.approved.json'), 'w'), indent=1)
kill._con().execute('INSERT INTO events (at, kind, detail) VALUES (?,?,?)', (rec['at'], 'approval', json.dumps(rec))).connection.commit()
print(f"approved {len(ok)}, rejected {len(rec['rejected'])}")
