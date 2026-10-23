-- vol module tables, added to delta1.db. Point-in-time: rows are appended, never updated.
-- Applied with CREATE TABLE IF NOT EXISTS, so it is safe to run against the existing book db.

CREATE TABLE IF NOT EXISTS runs (run_id INTEGER PRIMARY KEY, command TEXT, started_at TEXT, finished_at TEXT, status TEXT, rows_added INTEGER, notes TEXT);

-- Raw option chain, exactly as fetched.
CREATE TABLE IF NOT EXISTS option_quotes (
  as_of TEXT, underlying TEXT, expiry TEXT, strike REAL, right TEXT,
  bid REAL, ask REAL, last REAL, volume REAL, open_interest REAL,
  spot REAL, source TEXT, retrieved_at TEXT,
  PRIMARY KEY (as_of, underlying, expiry, strike, right, source));

-- Implied forward and discount per expiry (from put-call parity).
CREATE TABLE IF NOT EXISTS vol_forwards (
  as_of TEXT, underlying TEXT, expiry TEXT, t_years REAL,
  forward REAL, discount REAL, n_pairs INTEGER, source TEXT,
  PRIMARY KEY (as_of, underlying, expiry, source));

-- Fitted SVI parameters per expiry.
CREATE TABLE IF NOT EXISTS vol_surface_params (
  as_of TEXT, underlying TEXT, expiry TEXT, t_years REAL,
  a REAL, b REAL, rho REAL, m REAL, sigma REAL,
  rmse_volpts REAL, n_quotes INTEGER, arb_ok INTEGER, source TEXT,
  PRIMARY KEY (as_of, underlying, expiry, source));

-- QA results per run.
CREATE TABLE IF NOT EXISTS vol_surface_qa (
  as_of TEXT, underlying TEXT, check_name TEXT, result TEXT, detail TEXT, source TEXT,
  PRIMARY KEY (as_of, underlying, check_name, source));

-- Cleaning diagnostics: how many quotes each rule removed. expiry='ALL' for whole-chain rules.
CREATE TABLE IF NOT EXISTS vol_clean_log (
  as_of TEXT, underlying TEXT, expiry TEXT, metric TEXT, value REAL, source TEXT,
  PRIMARY KEY (as_of, underlying, expiry, metric, source));

-- Constant-maturity 30-day summary, for the day-over-day stability check.
CREATE TABLE IF NOT EXISTS vol_surface_summary (
  as_of TEXT, underlying TEXT, cm30_atm REAL, cm30_varswap REAL,
  cm30_rr25 REAL, cm30_bf25 REAL, spot REAL, source TEXT,
  PRIMARY KEY (as_of, underlying, source));

CREATE INDEX IF NOT EXISTS ix_option_quotes ON option_quotes(as_of, underlying, expiry);
