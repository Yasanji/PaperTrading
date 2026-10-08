"""Kill switch (DESIGN.md s.6.6 and s.12.6). While any kill event is open, no orders are sent.

  python kill.py status                 list open kill events
  python kill.py trip "reason"          open one by hand
Cleared only with clear_kill.py."""
import sys, sqlite3, datetime as dt
import config as C


def _con():
    con = sqlite3.connect(C.DB)
    con.execute('CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY, at TEXT, kind TEXT, detail TEXT, resolution TEXT)')
    return con


def trip(detail, kind='kill'):
    con = _con(); now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')
    cur = con.execute('INSERT INTO events (at, kind, detail) VALUES (?,?,?)', (now, kind, detail)); con.commit()
    return cur.lastrowid


def open_events():
    return _con().execute("SELECT event_id, at, detail FROM events WHERE kind='kill' AND resolution IS NULL").fetchall()


def is_killed():
    return len(open_events()) > 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd == 'trip': print('kill event', trip(sys.argv[2]))
    for e in open_events(): print(e)
    if not open_events(): print('no open kill events')
