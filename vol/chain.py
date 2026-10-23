"""Fetch the option chain and store it point-in-time (design note section 3).

Default source is Yahoo Finance via yfinance, on SPY. This is the only module that
touches the data vendor; everything downstream works off the stored quotes, so a real
feed drops in here without changing the rest of the pipeline.
"""
import datetime as dt
import pandas as pd
import yfinance as yf

COLS = ['expiry', 'strike', 'right', 'bid', 'ask', 'last', 'volume', 'open_interest']

# Friendly name -> (Yahoo symbol, exercise style). SPX/XSP index options are European and
# cash-settled; SPY (ETF) options are American and pay dividends.
UNDERLYINGS = {
    'SPY': ('SPY', 'american'),
    'SPX': ('^SPX', 'european'),
    'XSP': ('^XSP', 'european'),
}


def resolve(name):
    """Return (yahoo_symbol, default_exercise) for a friendly underlying name."""
    return UNDERLYINGS.get(name.upper(), (name, 'american'))


def _spot(t):
    try:
        s = t.fast_info.last_price
        if s:
            return float(s)
    except Exception:
        pass
    h = t.history(period='1d')
    return float(h['Close'].iloc[-1])


def fetch(underlying='SPY', max_expiries=None):
    """Return (spot, DataFrame[COLS], retrieved_at). One snapshot, near when called."""
    t = yf.Ticker(underlying)
    spot = _spot(t)
    expiries = list(t.options or [])
    if max_expiries:
        expiries = expiries[:max_expiries]
    rows = []
    for e in expiries:
        oc = t.option_chain(e)
        for df, right in ((oc.calls, 'C'), (oc.puts, 'P')):
            for _, r in df.iterrows():
                rows.append((e, float(r.strike), right, float(r.bid), float(r.ask),
                             float(r.lastPrice), float(r.volume or 0), float(r.openInterest or 0)))
    out = pd.DataFrame(rows, columns=COLS)
    return spot, out, dt.datetime.utcnow().isoformat(timespec='seconds')


def vix():
    """Latest VIX level, for the QA cross-check. None if unavailable."""
    try:
        v = yf.Ticker('^VIX')
        s = v.fast_info.last_price
        return float(s) if s else float(v.history(period='1d')['Close'].iloc[-1])
    except Exception:
        return None


def store(con, as_of, underlying, spot, df, source, retrieved_at):
    rows = [(as_of, underlying, r.expiry, r.strike, r.right, r.bid, r.ask, r.last,
             r.volume, r.open_interest, spot, source, retrieved_at)
            for r in df.itertuples()]
    cur = con.executemany(
        'INSERT OR IGNORE INTO option_quotes '
        '(as_of,underlying,expiry,strike,right,bid,ask,last,volume,open_interest,spot,source,retrieved_at) '
        'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)', rows)
    con.commit()
    return cur.rowcount
