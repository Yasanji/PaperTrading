"""Clear one kill event, with a written reason (DESIGN.md s.12.6). Trading resumes at the next scheduled run.
Refuses if the last reconciliation has an unexplained difference.
Usage: python clear_kill.py EVENT_ID "reason and what was fixed\""""
import sys, sqlite3, datetime as dt
import config as C

eid, reason = int(sys.argv[1]), sys.argv[2]
if len(reason) < 20: sys.exit('Write a reason of at least 20 characters: what happened and what was fixed.')
con = sqlite3.connect(C.DB)
try:
    bad = con.execute('SELECT COUNT(*) FROM reconciliation WHERE date = (SELECT MAX(date) FROM reconciliation) AND passed = 0').fetchone()[0]
except sqlite3.OperationalError:
    bad = 0
if bad: sys.exit(f'Not cleared: the last reconciliation has {bad} unexplained differences.')
now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')
n = con.execute("UPDATE events SET resolution=? WHERE event_id=? AND kind='kill' AND resolution IS NULL", (f'{now}: {reason}', eid)).rowcount
con.commit(); print('cleared' if n else 'no open kill event with that id')
