"""Pod 1, Sleeve C: month-end rebalancing (US). Rules: rebal/SLEEVE_C_PREREGISTRATION.md and its amendments.

Signal: equity weight minus 60% of a 60/40 portfolio of the S&P 500 price index and a constant-maturity 10-year
Treasury (price change at the daily par yield, no carry), reset to 60/40 at each month-end close. Only the current
month's data is needed, because the portfolio is reset at every month-end.

Position: in the window (the last five trading days of the month and the first trading day of the next), one MES against
one ZN, short equity and long bonds when the signal is above zero, the reverse below zero. Outside the window, flat.

Timing in the book's chain: the batch written on the evening of day D trades at the close of the next trading day E,
so the position held at E's close uses the signal at D's close (sleeve amendment 1).

The Threshold signal is computed for the log only and is not traded."""
import io, os, sys, numpy as np, pandas as pd, requests, yfinance as yf
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'book')); import config as C

# NYSE full-day closures, 2026 to 2027 (NYSE holiday calendar). Extend before 1 December 2027; checks() warns.
NYSE_HOLIDAYS = pd.to_datetime([
    '2026-01-01', '2026-01-19', '2026-02-16', '2026-04-03', '2026-05-25', '2026-06-19', '2026-07-03', '2026-09-07',
    '2026-11-26', '2026-12-25',
    '2027-01-01', '2027-01-18', '2027-02-15', '2027-03-26', '2027-05-31', '2027-06-18', '2027-07-05', '2027-09-06',
    '2027-11-25', '2027-12-24'])
DAYS = pd.offsets.CustomBusinessDay(holidays=NYSE_HOLIDAYS)
LOG = os.path.join(C.ROOT, 'book', 'sleeve_c_log.csv')
CACHE = os.path.join(C.ROOT, 'delta1', 'sleeve_c_inputs.csv')


def trading_days(month):
    m = pd.Period(month, 'M')
    return pd.date_range(m.start_time, m.end_time, freq=DAYS)


def in_window(day):
    """True if a position is held at the close of `day`: one of the last five trading days of its month."""
    day = pd.Timestamp(day).normalize(); td = trading_days(day.to_period('M'))
    return day in td[-5:]


def next_day(d):
    return (pd.Timestamp(d).normalize() + DAYS)


def treasury_10y(years):
    fr = []
    for y in years:
        u = (f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all'
             f'?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv')
        r = requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        if r.status_code == 200 and 'Date' in r.text[:40]: fr.append(pd.read_csv(io.StringIO(r.text))[['Date', '10 Yr']])
    t = pd.concat(fr); t['Date'] = pd.to_datetime(t.Date); return t.set_index('Date').sort_index()['10 Yr'].astype(float) / 100


def par_price(c, yy, n=20):
    i = np.arange(1, n + 1); return (c / 2 * (1 + yy / 2) ** -i).sum() + (1 + yy / 2) ** -n


def inputs(as_of, start_year=None):
    """S&P 500 closes and 10-year par yields to as_of. Falls back to the cached file if a download fails."""
    as_of = pd.Timestamp(as_of); start_year = start_year or as_of.year - 3
    try:
        px = yf.download('^GSPC', start=f'{start_year}-01-01', end=(as_of + pd.Timedelta(days=1)).date().isoformat(),
                         progress=False, auto_adjust=True)['Close'].squeeze().dropna()
        y = treasury_10y(range(start_year, as_of.year + 1))
        d = pd.concat([px.rename('px'), y.rename('y')], axis=1, join='inner').dropna()
        d.to_csv(CACHE)
    except Exception as e:
        print(f'sleeve C: download failed ({type(e).__name__}); using {CACHE}')
        d = pd.read_csv(CACHE, index_col=0, parse_dates=True)
    return d.loc[:as_of]


def signals(d):
    """Calendar and Threshold signals at each close (equity weight minus 60%)."""
    re = d.px.pct_change().values
    rb = np.r_[np.nan, [par_price(d.y.iloc[k - 1], d.y.iloc[k]) - 1 for k in range(1, len(d))]]
    drift = lambda w, a, b: w * (1 + a) / (w * (1 + a) + (1 - w) * (1 + b))
    idx = d.index; s_ = idx.to_series(); last_in_data = s_.groupby(idx.to_period('M')).transform('max') == s_
    # past months: the last close in the data; the latest month: only if the calendar says the next trading day is a new month
    month_end = last_in_data & ((idx.to_period('M') < idx[-1].to_period('M')) | ((idx + DAYS).month != idx.month))
    cal, w = np.full(len(d), np.nan), 0.6
    for t in range(1, len(d)):
        w = drift(w, re[t], rb[t]); cal[t] = w - 0.6
        if month_end.iloc[t]: w = 0.6
    thr_all = []
    for delta in np.arange(0, 0.02501, 0.001):
        w, s = 0.6, np.full(len(d), np.nan)
        for t in range(1, len(d)):
            w = drift(w, re[t], rb[t]); s[t] = w - 0.6
            if abs(w - 0.6) > delta: w = 0.6
        thr_all.append(s)
    return pd.DataFrame(dict(cal=cal, thr=np.mean(thr_all, axis=0)), index=idx)


def position(signal):
    """Contracts (MES, ZN) for a Calendar signal value."""
    if pd.isna(signal) or signal == 0: return 0, 0
    return (-1, 1) if signal > 0 else (1, -1)


def targets(as_of, d=None, write_log=True):
    """Sleeve C contracts to hold at the close of the next trading day, and the same for the previous batch.
    Returns dict(MES=, ZN=, MES_prev=, ZN_prev=, cal=, thr=, trade_day=)."""
    as_of = pd.Timestamp(as_of).normalize(); d = inputs(as_of) if d is None else d.loc[:as_of]
    s = signals(d); E = next_day(as_of)
    if s.index[-1] != as_of: raise RuntimeError(f'sleeve C: no S&P 500 or Treasury close for {as_of.date()}')
    now = position(s.cal.iloc[-1]) if in_window(E) else (0, 0)
    prev_day = s.index[-2]; prev = position(s.cal.iloc[-2]) if in_window(next_day(prev_day)) else (0, 0)
    out = dict(MES=now[0], ZN=now[1], MES_prev=prev[0], ZN_prev=prev[1], cal=float(s.cal.iloc[-1]), thr=float(s.thr.iloc[-1]),
               trade_day=E.date().isoformat(), in_window=bool(in_window(E)))
    if write_log:
        row = pd.DataFrame([dict(as_of=as_of.date().isoformat(), **out)])
        row.to_csv(LOG, mode='a', header=not os.path.exists(LOG), index=False)
    return out


def checks(as_of):
    return ['sleeve C: NYSE holiday list ends 2027; extend it'] if pd.Timestamp(as_of) >= pd.Timestamp('2027-12-01') else []


if __name__ == '__main__':
    as_of = sys.argv[1] if len(sys.argv) > 1 else pd.Timestamp.today().date().isoformat()
    print(targets(as_of, write_log=False))
