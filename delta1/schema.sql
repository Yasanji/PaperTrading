-- delta1.db: point-in-time store. Rows are appended, never updated; every row records when it was collected.
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS runs (run_id INTEGER PRIMARY KEY, command TEXT, started_at TEXT, finished_at TEXT, status TEXT, rows_added INTEGER, notes TEXT);
CREATE TABLE IF NOT EXISTS instruments (instrument_id INTEGER PRIMARY KEY, ticker TEXT UNIQUE, isin TEXT, name TEXT, country TEXT, sector TEXT, currency TEXT, first_seen TEXT);
CREATE TABLE IF NOT EXISTS index_membership (as_of TEXT, index_code TEXT, instrument_id INTEGER REFERENCES instruments, weight REAL, source TEXT, run_id INTEGER REFERENCES runs, PRIMARY KEY (as_of, index_code, instrument_id));
CREATE TABLE IF NOT EXISTS prices (date TEXT, instrument_id INTEGER REFERENCES instruments, close REAL, adj_close REAL, volume REAL, source TEXT, retrieved_at TEXT, PRIMARY KEY (date, instrument_id, source));
CREATE TABLE IF NOT EXISTS index_levels (date TEXT, index_code TEXT, value REAL, source TEXT, retrieved_at TEXT, PRIMARY KEY (date, index_code, source));
CREATE TABLE IF NOT EXISTS rates (date TEXT, series TEXT, value REAL, source TEXT, retrieved_at TEXT, PRIMARY KEY (date, series, source));
CREATE TABLE IF NOT EXISTS futures_prices (date TEXT, product TEXT, expiry TEXT, settle REAL, source TEXT, retrieved_at TEXT, PRIMARY KEY (date, product, expiry, source));
CREATE TABLE IF NOT EXISTS dividends_actual (instrument_id INTEGER REFERENCES instruments, ex_date TEXT, amount REAL, currency TEXT, kind TEXT, source TEXT, retrieved_at TEXT, PRIMARY KEY (instrument_id, ex_date, source));
CREATE TABLE IF NOT EXISTS dividend_snapshots (as_of TEXT, instrument_id INTEGER REFERENCES instruments, forward_rate REAL, next_ex_date TEXT, last_value REAL, source TEXT, PRIMARY KEY (as_of, instrument_id, source));
CREATE TABLE IF NOT EXISTS announcements (doc_id INTEGER PRIMARY KEY, instrument_id INTEGER REFERENCES instruments, published_at TEXT, source TEXT, url TEXT, title TEXT, sha256 TEXT UNIQUE, retrieved_at TEXT);
CREATE TABLE IF NOT EXISTS dividend_facts (fact_id INTEGER PRIMARY KEY, doc_id INTEGER REFERENCES announcements, instrument_id INTEGER REFERENCES instruments, kind TEXT, amount REAL, currency TEXT, ex_date TEXT, pay_date TEXT, quote TEXT, extracted_by TEXT, extracted_at TEXT, reviewed INTEGER DEFAULT 0, reviewed_at TEXT, review_note TEXT);
CREATE TABLE IF NOT EXISTS forecasts (as_of TEXT, index_code TEXT, period TEXT, instrument_id INTEGER REFERENCES instruments, expected_ex_date TEXT, amount REAL, index_points REAL, basis TEXT, PRIMARY KEY (as_of, index_code, period, instrument_id, expected_ex_date));
CREATE TABLE IF NOT EXISTS implied_dividends (as_of TEXT, index_code TEXT, period TEXT, source TEXT, points REAL, rate_used REAL, PRIMARY KEY (as_of, index_code, period, source));
CREATE TABLE IF NOT EXISTS index_predictions (review TEXT, index_code TEXT, instrument_id INTEGER REFERENCES instruments, action TEXT, rule TEXT, margin REAL, committed_at TEXT, git_commit TEXT, PRIMARY KEY (review, index_code, instrument_id));
CREATE TABLE IF NOT EXISTS index_changes_actual (review TEXT, index_code TEXT, instrument_id INTEGER REFERENCES instruments, action TEXT, announced_at TEXT, effective_date TEXT, PRIMARY KEY (review, index_code, instrument_id));
-- Paper book (filled by the daily job)
CREATE TABLE IF NOT EXISTS targets (date TEXT, pod TEXT, instrument_id INTEGER REFERENCES instruments, target_qty REAL, target_weight REAL, git_commit TEXT, PRIMARY KEY (date, pod, instrument_id));
CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY, date TEXT, pod TEXT, instrument_id INTEGER REFERENCES instruments, qty REAL, order_type TEXT, sent_at TEXT, status TEXT);
CREATE TABLE IF NOT EXISTS fills (fill_id TEXT PRIMARY KEY, order_id INTEGER REFERENCES orders, date TEXT, instrument_id INTEGER REFERENCES instruments, qty REAL, price REAL, commission REAL, source TEXT);
CREATE TABLE IF NOT EXISTS positions (date TEXT, pod TEXT, instrument_id INTEGER REFERENCES instruments, qty REAL, market_value REAL, PRIMARY KEY (date, pod, instrument_id));
CREATE TABLE IF NOT EXISTS account (date TEXT PRIMARY KEY, nav REAL, cash REAL, margin REAL, buffer REAL);
CREATE TABLE IF NOT EXISTS risk (date TEXT, pod TEXT, vol REAL, drawdown REAL, gross REAL, limit_status TEXT, PRIMARY KEY (date, pod));
CREATE TABLE IF NOT EXISTS reconciliation (date TEXT, instrument_id INTEGER REFERENCES instruments, target_qty REAL, actual_qty REAL, difference REAL, passed INTEGER, PRIMARY KEY (date, instrument_id));
CREATE TABLE IF NOT EXISTS events (event_id INTEGER PRIMARY KEY, at TEXT, kind TEXT, detail TEXT, resolution TEXT);
CREATE INDEX IF NOT EXISTS ix_prices_inst ON prices(instrument_id, date);
CREATE INDEX IF NOT EXISTS ix_divs_inst ON dividends_actual(instrument_id, ex_date);
