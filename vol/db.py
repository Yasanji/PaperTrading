"""delta1.db access for the vol module.

Mirrors the collector's conventions: append-only, every run logged in the runs table.
The vol tables are created from schema_vol.sql (CREATE TABLE IF NOT EXISTS), so this is
safe to point at the existing book database.
"""
import os, sqlite3, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_DB = os.environ.get('DELTA1_DB', os.path.join(ROOT, 'delta1', 'delta1.db'))


def _now():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')


def connect(db_path=None):
    con = sqlite3.connect(db_path or DEFAULT_DB)
    con.execute('PRAGMA foreign_keys = ON')
    return con


def ensure_schema(con):
    con.executescript(open(os.path.join(HERE, 'schema_vol.sql')).read())
    con.commit()


def run(con, command):
    cur = con.execute('INSERT INTO runs (command, started_at, status) VALUES (?,?,?)',
                      (command, _now(), 'started'))
    con.commit()
    return cur.lastrowid


def finish(con, run_id, n, status='ok', notes=''):
    con.execute('UPDATE runs SET finished_at=?, status=?, rows_added=?, notes=? WHERE run_id=?',
                (_now(), status, n, notes, run_id))
    con.commit()
