"""
Pairs Trading in Python, Part 2: The Moving Anchor
Kalman-filtered hedge ratio and mean, walk-forward out-of-sample,
drift/break filters, and a control test against manufactured reversion.

Plugs into Part 1: expects `px` (dict of Adj Close Series), NAMES, and `mkt`
(log returns of ^STOXX50E) from the Part 1 script.

Variants compared out of sample (formation Sep-21..Sep-24, trade Sep-24..Sep-26):
  part1_rolling   1:1 log spread, 90-day rolling mean   (the Part 1 baseline)
  static_ols      hedge ratio + mean frozen at formation
  kalman_2state   [beta, alpha] random walk, z = e/sqrt(Q)
  kalman_ecm      [beta, alpha] random walk + AR(1) spread state
Every variant fills a day after the signal and pays 1bp commission + 2bp slippage
per leg, including the rebalancing that a moving hedge ratio forces.
"""
import numpy as np, pandas as pd
import statsmodels.tsa.stattools as ts

# ---------------------------------------------------------------- Kalman ----
def kalman_pair(ly, lx, delta=1e-5, ve=1e-3, init=None, x_centre=None):
    """State = [beta, alpha], random walk.  ly_t = alpha_t + beta_t*(lx_t - c) + e_t.
    lx is centred on c (formation mean) - otherwise log prices sit near a constant,
    alpha and beta are nearly collinear, P blows up along that direction and Q
    swamps the signal.  init=(beta, alpha) from formation OLS avoids a burn-in.
    Returns point-in-time (prior) beta/alpha, forecast error e and its variance Q."""
    n = len(ly)
    c = lx.iloc[:250].mean() if x_centre is None else x_centre
    Vw = delta / (1 - delta) * np.eye(2)
    theta = np.zeros(2) if init is None else np.asarray(init, float)
    P = np.eye(2) if init is None else np.eye(2) * 1e-3
    out = np.full((n, 4), np.nan)               # beta, alpha, e, Q
    Y, X = ly.values, lx.values - c
    for t in range(n):
        H = np.array([X[t], 1.0])
        R = P + Vw
        Q = H @ R @ H + ve
        e = Y[t] - H @ theta
        out[t] = theta[0], theta[1], e, Q       # prior: known before today's update
        K = R @ H / Q
        theta = theta + K * e
        P = R - np.outer(K, H) @ R
    return pd.DataFrame(out, index=ly.index, columns=['beta', 'alpha', 'e', 'Q'])

def kalman_ecm(ly, lx, delta, phi, sig_eta, init, c, ve=1e-8):
    """Three-state filter that keeps the anchor and the reversion apart.
        ly_t  = alpha_t + beta_t*(lx_t - c) + u_t
        beta, alpha : random walks, variance delta/(1-delta)   (the moving anchor)
        u_t   = phi*u_{t-1} + eta_t                            (the spread we trade)
    With only [beta, alpha] in the state, a filter tuned for fit chases the
    spread itself and the reversion you wanted to trade gets absorbed into the
    'mean'. Giving u its own AR(1) state stops that. phi and sig_eta come
    from the formation-period half-life and residual - Part 1's numbers."""
    n = len(ly)
    q = delta / (1 - delta)
    F = np.diag([1.0, 1.0, phi])
    W = np.diag([q, q, sig_eta**2])
    theta = np.array([init[0], init[1], 0.0])
    P = np.diag([1e-3, 1e-3, sig_eta**2 / (1 - phi**2)])
    out = np.full((n, 5), np.nan)                # beta, alpha, u_filt, e, Q
    Y, X = ly.values, lx.values - c
    for t in range(n):
        theta = F @ theta; P = F @ P @ F.T + W   # predict
        H = np.array([X[t], 1.0, 1.0])
        Q = H @ P @ H + ve
        e = Y[t] - H @ theta
        K = P @ H / Q
        b_prior, a_prior = theta[0], theta[1]
        theta = theta + K * e; P = P - np.outer(K, H) @ P
        # hedge/anchor: prior (pre-update). u: filtered at today's close,
        # which is what Part 1's z-score also used.
        out[t] = b_prior, a_prior, theta[2], e, Q
    k = pd.DataFrame(out, index=ly.index, columns=['beta', 'alpha', 'u', 'e', 'Q'])
    k['z'] = k.u / (sig_eta / np.sqrt(1 - phi**2))
    return k

def fit_ecm(lyf, lxf, deltas=(1e-8, 1e-7, 1e-6, 1e-5, 1e-4)):
    """phi, sig_eta from formation OLS residual; delta by likelihood, formation only."""
    init, c = ols_init(lyf.iloc[:250], lxf.iloc[:250])
    bf, af = np.polyfit(lxf - c, lyf, 1)
    r = lyf - af - bf * (lxf - c)
    phi = np.clip(r.autocorr(), 0.5, 0.995)
    sig_eta = np.std(r.diff().dropna() + (1 - phi) * r.shift(1).dropna())
    ll = []
    for d in deltas:
        k = kalman_ecm(lyf, lxf, d, phi, sig_eta, init, c).iloc[60:]
        ll.append(-0.5 * np.sum(np.log(k.Q) + k.e**2 / k.Q))
    return deltas[int(np.argmax(ll))], phi, sig_eta, init, c

def ols_init(ly, lx):
    c = lx.mean(); b, a = np.polyfit(lx - c, ly, 1)
    return (b, a), c

def kalman_loglik(ly, lx, delta, ve, burn=60):
    init, c = ols_init(ly.iloc[:250], lx.iloc[:250])
    k = kalman_pair(ly, lx, delta, ve, init, c).iloc[burn:]
    return -0.5 * np.sum(np.log(2*np.pi*k.Q) + k.e**2 / k.Q)

def fit_kalman(ly, lx, deltas=(1e-7, 1e-6, 1e-5, 1e-4, 1e-3), ves=None):
    """Choose delta, ve by likelihood on FORMATION data only (not by Sharpe)."""
    if ves is None:
        s2 = np.var(ly - np.polyval(np.polyfit(lx, ly, 1), lx))
        ves = s2 * np.array([0.1, 0.3, 1.0, 3.0])
    grid = [(d, v, kalman_loglik(ly, lx, d, v)) for d in deltas for v in ves]
    d, v, _ = max(grid, key=lambda g: g[2])
    return d, v

# ------------------------------------------------------------ signal/book ---
def positions(z, entry=2.0, exit_=0.5, stop=None, allowed=None):
    """allowed: optional boolean Series; False forces the book flat that day
    (pair not selected this window, or regime outside the ones it reverts in)."""
    pos = np.zeros(len(z)); cur = 0.0
    ok = np.ones(len(z), bool) if allowed is None else allowed.reindex(z.index).fillna(False).values
    for i, zi in enumerate(z):
        if not ok[i]:
            cur = 0.0; pos[i] = 0.0; continue
        if np.isnan(zi):
            pos[i] = cur; continue
        if stop is not None and cur != 0 and abs(zi) >= stop:
            cur = 0.0                            # spread broke: get out
        elif cur == 0:
            cur = -1.0 if zi >= entry else (1.0 if zi <= -entry else 0.0)
        elif abs(zi) <= exit_:
            cur = 0.0
        pos[i] = cur
    return pd.Series(pos, index=z.index)

def backtest(y, x, pos, beta, cost_bps=1.0, slip_bps=2.0, lag=1):
    """Long spread = long y, short beta*x.  Gross exposure normalised to 1.
    lag=1 fills at the close after the signal (Part 1's realistic case)."""
    b = beta.ffill()
    wy = pos / (1 + b.abs())
    wx = -pos * b / (1 + b.abs())
    wy, wx = wy.shift(lag).fillna(0), wx.shift(lag).fillna(0)
    ry, rx = y.pct_change(), x.pct_change()
    gross = wy.shift(1) * ry + wx.shift(1) * rx
    turn = wy.diff().abs() + wx.diff().abs()     # includes hedge-ratio rebalancing
    net = (gross - turn * (cost_bps + slip_bps) / 1e4).dropna()
    return net

def stats(net, mkt=None):
    a = np.sqrt(252); cum = (1 + net).cumprod()
    s = {'sharpe': net.mean() / net.std() * a if net.std() > 0 else np.nan,
         'vol%': net.std() * a * 100,
         'ret%': (cum.iloc[-1] - 1) * 100,
         'mdd%': ((cum / cum.cummax()) - 1).min() * 100}
    if mkt is not None:
        d = pd.concat([net, mkt], axis=1).dropna()
        s['beta'] = np.polyfit(d.iloc[:, 1], d.iloc[:, 0], 1)[0]
    return pd.Series(s).round(2)

# ------------------------------------------------------- variants to compare
def variant_part1(y, x, W=90):
    """Part 1 baseline: 1:1 log spread, rolling mean/std."""
    s = np.log(y) - np.log(x)
    z = (s - s.rolling(W).mean().shift(1)) / s.rolling(W).std().shift(1)
    return z, pd.Series(1.0, index=y.index)

def variant_static_ols(y, x, y_form, x_form):
    """Hedge ratio and mean frozen from formation period."""
    b, a = np.polyfit(np.log(x_form), np.log(y_form), 1)
    s = np.log(y) - a - b * np.log(x)
    r = np.log(y_form) - a - b * np.log(x_form)
    z = (s - r.mean()) / r.std()
    return z, pd.Series(b, index=y.index)

def variant_kalman(y, x, y_form, x_form, burn=60):
    lyf, lxf = np.log(y_form), np.log(x_form)
    d, v = fit_kalman(lyf, lxf)
    init, c = ols_init(lyf.iloc[:250], lxf.iloc[:250])   # first year only: no peeking
    k = kalman_pair(np.log(y), np.log(x), d, v, init, c)
    z = k.e / np.sqrt(k.Q)
    z.iloc[:burn] = np.nan
    return z, k.beta, (d, v), k

def variant_ecm(y, x, y_form, x_form):
    lyf, lxf = np.log(y_form), np.log(x_form)
    d, phi, sig, init, c = fit_ecm(lyf, lxf)
    k = kalman_ecm(np.log(y), np.log(x), d, phi, sig, init, c)
    return k.z, k.beta, (d, phi, sig), k

# ------------------------------------------------------- drift / break checks
def rolling_coint_p(y, x, W=250, step=21):
    idx, p = [], []
    for i in range(W, len(y), step):
        p.append(ts.coint(np.log(y.iloc[i-W:i]), np.log(x.iloc[i-W:i]))[1])
        idx.append(y.index[i])
    return pd.Series(p, index=idx)

def half_life(s):
    lag = s.shift(1); r = pd.concat([lag, s - lag], axis=1).dropna()
    b = np.polyfit(r.iloc[:, 0], r.iloc[:, 1], 1)[0]
    return -np.log(2) / b if b < 0 else np.inf

# ------------------------------------------------------------- walk-forward
def screen(px, names, start, end, corr_min=0.70, p_max=0.05, hl_max=126):
    """Part 1 screen, run on formation data only."""
    from itertools import combinations
    keep = []
    for a, b in combinations(names, 2):
        d = pd.concat([px[a], px[b]], axis=1, keys=[a, b]).loc[start:end].dropna()
        if len(d) < 250 or abs(d[a].corr(d[b])) < corr_min:
            continue
        p1, p2 = ts.coint(d[a], d[b])[1], ts.coint(d[b], d[a])[1]
        if max(p1, p2) >= p_max:                 # both directions
            continue
        hl = half_life(np.log(d[a]) - np.log(d[b]))
        if hl <= hl_max:
            keep.append((a, b, max(p1, p2), hl))
    return pd.DataFrame(keep, columns=['a', 'b', 'p', 'half_life']).sort_values('p')

def walk_forward(px, a, b, form_start, form_end, trade_end, mkt=None):
    d = pd.concat([px[a], px[b]], axis=1, keys=[a, b]).loc[form_start:trade_end].dropna()
    y, x = d[a], d[b]
    yf, xf = y.loc[:form_end], x.loc[:form_end]
    fe = pd.Timestamp(form_end)
    oos = lambda r: r.loc[r.index > fe]          # score only the unseen period
    rows = {}
    for name, (z, beta) in {
        'part1_rolling': variant_part1(y, x),
        'static_ols':    variant_static_ols(y, x, yf, xf),
    }.items():
        rows[name] = stats(oos(backtest(y, x, positions(z), beta)), mkt)
    z, beta, params, k = variant_kalman(y, x, yf, xf)
    rows['kalman_2state'] = stats(oos(backtest(y, x, positions(z), beta)), mkt)
    z, beta, params, k = variant_ecm(y, x, yf, xf)
    rows['kalman_ecm'] = stats(oos(backtest(y, x, positions(z), beta)), mkt)
    rows['kalman_ecm_stop4'] = stats(oos(backtest(y, x, positions(z, stop=4.0), beta)), mkt)
    return pd.DataFrame(rows).T, params, k

if __name__ == '__main__':
    # after running Part 1 to build `px`:
    # 1) re-screen on formation only (does Safran/Siemens even survive?)
    # surv = screen(px, NAMES, '2021-09-27', '2024-09-27'); print(surv.head(20))
    # 2) out-of-sample comparison on the pair
    # tab, params, k = walk_forward(px, 'SAF.PA', 'SIE.DE',
    #                               '2021-09-27', '2024-09-27', '2026-09-25', mkt)
    # 3) control: the Part 1 reject should NOT start working under Kalman
    # walk_forward(px, 'BBVA.MC', 'SAN.MC', '2021-09-27', '2024-09-27', '2026-09-25', mkt)
    # 4) is the anchor still anchored? rolling 1y Engle-Granger p on the pair
    # print(rolling_coint_p(px['SAF.PA'], px['SIE.DE']).tail(12))
    pass


# =============================================================================
# SHORT LOOKBACK, REGIMES, ROLLING WALK-FORWARD, AND THE CASH LEG
# =============================================================================
# Re-screen every quarter on the trailing year only, trade the next quarter
# unseen, and only trade a pair when today's regime is one in which the pair
# was seen to revert during formation. Everything is point-in-time.

# ------------------------------------------------------------------ regimes --
def vol_regime(mkt, short=63, long=252):
    """'high'/'low' vol: trailing 3m realised vol vs its own trailing 1y median.
    Uses only returns up to t. (Avoid smoothed HMM probabilities here: they
    use the whole sample and leak the future into the label.)"""
    rv = mkt.rolling(short).std() * np.sqrt(252)
    med = rv.rolling(long, min_periods=long // 2).median()
    lab = pd.Series(np.where(rv > med, 'high_vol', 'low_vol'), index=mkt.index)
    return lab.where(rv.notna() & med.notna())

def rate_regime(estr, window=63, band=0.25):
    """'hiking'/'cutting'/'hold' from the 3m change in the cash rate (% pts)."""
    ch = estr - estr.shift(window)
    lab = pd.Series('hold', index=estr.index)
    lab[ch > band] = 'hiking'; lab[ch < -band] = 'cutting'
    return lab.where(ch.notna())

def regime_profile(y, x, labels, min_days=60):
    """Per regime: hedge ratio, half-life, corr, EG p. Run on FORMATION data.
    Regimes are rarely contiguous, so the per-regime spread is built from the
    whole-window hedge, and half-life comes from day-to-day changes that
    fall inside the regime (no stitching across gaps)."""
    ly, lx = np.log(y), np.log(x)
    b, a = np.polyfit(lx, ly, 1)
    s = ly - a - b * lx
    out = {}
    for r in labels.dropna().unique():
        m = (labels == r).reindex(s.index).fillna(False)
        if m.sum() < min_days:
            continue
        pair_m = m & m.shift(1, fill_value=False)       # both days in regime
        lag, ds = s.shift(1)[pair_m], s.diff()[pair_m]
        X = np.column_stack([lag, np.ones(len(lag))])
        coef, *_ = np.linalg.lstsq(X, ds.values, rcond=None); k = coef[0]
        res = ds.values - X @ coef
        se = np.sqrt(res @ res / (len(ds) - 2) * np.linalg.inv(X.T @ X)[0, 0])
        br = np.polyfit(lx[m], ly[m], 1)[0]
        out[r] = {'days': int(m.sum()), 'hedge': round(br, 2),
                  'half_life': round(-np.log(2) / k, 1) if k < 0 else np.inf,
                  'df_t': round(k / se, 2),
                  'corr': round(np.corrcoef(ly[m].diff().dropna(), lx[m].diff().dropna())[0, 1], 2)}
    return pd.DataFrame(out).T

# --------------------------------------------------------------------- cash --
# ECB deposit facility rate steps (effective dates). Fallback only - prefer the
# daily €STR fixing from the ECB. VERIFY anything after mid-2025 before publishing.
_DFR = [('2019-09-18', -0.50), ('2022-07-27', 0.00), ('2022-09-14', 0.75),
        ('2022-11-02', 1.50), ('2022-12-21', 2.00), ('2023-02-08', 2.50),
        ('2023-03-22', 3.00), ('2023-05-10', 3.25), ('2023-06-21', 3.50),
        ('2023-08-02', 3.75), ('2023-09-20', 4.00), ('2024-06-12', 3.75),
        ('2024-09-18', 3.50), ('2024-10-23', 3.25), ('2024-12-18', 3.00),
        ('2025-02-05', 2.75), ('2025-03-12', 2.50), ('2025-04-23', 2.25),
        ('2025-06-11', 2.00)]

def load_estr(index):
    """Daily €STR in % a year, aligned to `index`."""
    url = ('https://data-api.ecb.europa.eu/service/data/EST/'
           'B.EU000A2X2A25.WT?format=csvdata')
    try:
        df = pd.read_csv(url)
        s = pd.Series(df.OBS_VALUE.values, index=pd.to_datetime(df.TIME_PERIOD)).sort_index()
        src = 'ECB €STR'
    except Exception:
        d = pd.Series(dict(_DFR)); d.index = pd.to_datetime(d.index)
        s = d.reindex(pd.date_range(d.index[0], index[-1])).ffill() - 0.09  # €STR ≈ DFR - 9bp
        src = 'DFR fallback (approximate)'
    return s.reindex(s.index.union(index)).ffill().reindex(index), src

def cash_leg(index, estr, w_long, w_short, borrow_bps=35.0, rebate_haircut_bps=10.0):
    """Daily cash income per unit of capital, ACT/360.
    Unspent capital earns €STR. Short proceeds sit as collateral earning
    €STR less a haircut, and the short pays a stock-borrow fee.
    Flat book: all capital earns €STR (and paid it while rates were negative)."""
    days = pd.Series(index, index=index).diff().dt.days.fillna(1)
    r = estr / 100.0
    wl, ws = w_long.shift(1).fillna(0), w_short.shift(1).fillna(0).abs()   # held overnight
    rate = r * (1 - wl) + (r - rebate_haircut_bps / 1e4) * ws - (borrow_bps / 1e4) * ws
    rf = r * days / 360
    return rate * days / 360, rf

# ----------------------------------------------------------- walk-forward ----
def rolling_walk_forward(px, names, mkt, estr, form_days=252, trade_days=63,
                         top_k=3, regime='vol', entry=2.0, exit_=0.5, stop=4.0,
                         cost_bps=1.0, slip_bps=2.0, lag=1, **cash_kw):
    """Every `trade_days`, re-screen on the trailing `form_days` only, keep the
    best `top_k` pairs, freeze hedge/mean/std from formation, and trade the
    next window. The half-life gate scales with the window: you need several
    half-lives inside the lookback to measure one at all.
    A pair only trades on days whose regime label was seen >= 60 days in
    formation with a tradeable half-life. Positions carry across windows only
    if the pair is re-selected; otherwise they are closed."""
    prices = pd.concat({n: px[n] for n in names}, axis=1).dropna(how='all')
    dates = prices.index
    labels = (vol_regime(mkt) if regime == 'vol' else
              rate_regime(estr) if regime == 'rates' else
              pd.Series('all', index=mkt.index)).reindex(dates)
    hl_max = form_days / 3
    zs, bs, ok = {}, {}, {}
    log = []
    for s0 in range(form_days, len(dates) - 1, trade_days):
        f_idx, t_idx = dates[s0 - form_days:s0], dates[s0:s0 + trade_days]
        surv = _screen_frame(prices.loc[f_idx], names, hl_max,
                             labels.reindex(f_idx) if regime else None)
        picks = surv.head(top_k)
        for _, row in picks.iterrows():
            a, b = row.a, row.b; key = f'{a}|{b}'
            yf, xf = prices.loc[f_idx, a], prices.loc[f_idx, b]
            yt, xt = prices.loc[t_idx, a], prices.loc[t_idx, b]
            z, beta = variant_static_ols(yt, xt, yf, xf)
            if row.regimes == 'all' or not regime:
                gate = pd.Series(True, index=t_idx)
            else:
                good = row.regimes.split(',')
                gate = labels.reindex(t_idx).isin(good)
                # hedge/mean/std from the good-regime days only
                fm = labels.reindex(f_idx).isin(good)
                z, beta = variant_static_ols(yt, xt, yf[fm], xf[fm])
            zs.setdefault(key, []).append(z); bs.setdefault(key, []).append(beta)
            ok.setdefault(key, []).append(gate)
            log.append({'window': t_idx[0].date(), 'pair': key, 'p': round(row.p, 4),
                        'half_life': round(row.half_life, 1),
                        'regimes': row.regimes,
                        'traded_days%': round(100 * gate.mean(), 0)})
    # assemble per-pair series across windows; unselected days are forced flat
    W_long = pd.Series(0.0, index=dates); W_short = pd.Series(0.0, index=dates)
    spread_pnl = pd.Series(0.0, index=dates)
    spread_gross = pd.Series(0.0, index=dates); turnover = pd.Series(0.0, index=dates)
    for key in zs:
        a, b = key.split('|')
        z = pd.concat(zs[key]).reindex(dates)
        beta = pd.concat(bs[key]).reindex(dates).ffill()
        gate = pd.concat(ok[key]).reindex(dates).fillna(False).astype(bool)
        pos = positions(z, entry, exit_, stop, allowed=gate & z.notna())
        wy = pos / (1 + beta.abs()) / top_k
        wx = -pos * beta / (1 + beta.abs()) / top_k
        wy, wx = wy.shift(lag).fillna(0), wx.shift(lag).fillna(0)
        ry, rx = prices[a].pct_change(), prices[b].pct_change()
        gross = (wy.shift(1) * ry + wx.shift(1) * rx).fillna(0)
        turn = wy.diff().abs().fillna(0) + wx.diff().abs().fillna(0)
        spread_pnl += gross - turn * (cost_bps + slip_bps) / 1e4
        spread_gross += gross; turnover += turn
        W_long += wy.clip(lower=0) + wx.clip(lower=0)
        W_short += wy.clip(upper=0) + wx.clip(upper=0)
    cash, rf = cash_leg(dates, estr, W_long, W_short, **cash_kw)
    start = dates[form_days]
    book = pd.DataFrame({'spread': spread_pnl, 'cash': cash, 'rf': rf,
                         'gross': spread_gross, 'costs': spread_gross - spread_pnl,
                         'turnover': turnover, 'w_long': W_long, 'w_short': W_short.abs(),
                         'gross_exposure': W_long + W_short.abs()}).loc[start:]
    book['total'] = book.spread + book.cash
    book['excess'] = book.total - book.rf
    return book, pd.DataFrame(log)

EG_CRIT_1PCT = -3.90   # Engle-Granger, 2 variables, 1%. Stricter than 5% because
                       # testing each regime separately multiplies the tests run.

def _screen_frame(prices, names, hl_max, labels=None, corr_min=0.70, p_max=0.05,
                  min_days=60):
    """A pair passes if it cointegrates over the whole lookback (Part 1's test),
    OR if its spread reverts inside at least one regime seen for >= min_days.
    Returns the regimes in which it reverts, so trading can be gated on them.
    A pair that mean-reverts in calm markets and wanders in stressed ones
    usually FAILS the whole-window test - that is the case this is for."""
    from itertools import combinations
    keep = []
    for a, b in combinations(names, 2):
        d = prices[[a, b]].dropna()
        if len(d) < 120 or abs(d[a].corr(d[b])) < corr_min:
            continue
        p = max(ts.coint(d[a], d[b])[1], ts.coint(d[b], d[a])[1])
        hl = half_life(np.log(d[a]) - np.log(d[b]))
        whole = p < p_max and hl <= hl_max
        good = set()
        if labels is not None:
            prof = regime_profile(d[a], d[b], labels.reindex(d.index), min_days)
            if len(prof):
                good = set(prof.index[(prof.df_t <= EG_CRIT_1PCT) & (prof.half_life <= hl_max)])
        if whole or good:
            score = p if whole else 1.0 + min(prof.loc[list(good), 'df_t'])  # whole-window passes rank first
            keep.append((a, b, p, hl, 'all' if whole else ','.join(sorted(good)), score))
    return pd.DataFrame(keep, columns=['a', 'b', 'p', 'half_life', 'regimes', 'score']).sort_values('score')

def book_stats(book):
    a = np.sqrt(252)
    ann = lambda r: ((1 + r).prod() ** (252 / len(r)) - 1) * 100
    cum = (1 + book.total).cumprod()
    return pd.Series({
        'total_ret%/yr':  ann(book.total),
        'cash_ret%/yr':   ann(book.cash),
        'spread_ret%/yr': ann(book.spread),
        'rf%/yr':         ann(book.rf),
        'sharpe(excess)': book.excess.mean() / book.excess.std() * a,
        'vol%':           book.total.std() * a * 100,
        'mdd%':           ((cum / cum.cummax()) - 1).min() * 100,
        'time_invested%': (book.gross_exposure > 0).mean() * 100}).round(2)

# Usage (after Part 1 has built px, NAMES and mkt):
#   estr, src = load_estr(mkt.index); print('cash rate from', src)
#   for fd in (126, 252, 504):                           # lookback sensitivity
#       book, log = rolling_walk_forward(px, NAMES, mkt, estr, form_days=fd)
#       print(fd, book_stats(book).to_dict())
#   book, log = rolling_walk_forward(px, NAMES, mkt, estr, regime=None)   # no gate
#   print(log.groupby('pair').size().sort_values(ascending=False).head(10))
#   print(regime_profile(px['SAF.PA'], px['SIE.DE'], vol_regime(mkt)))    # the Part 1 pair



# =============================================================================
# PORTABLE ALPHA: CASH + MARKET + PAIR, AND STRIPPING BETA FROM ALPHA
# =============================================================================
# Capital sits in cash earning a base rate. On top of it run two overlays:
#   market overlay : w_mkt of S&P 500, FX-hedged to EUR -> earns (SPX - USD rate)
#   pair overlay   : the pair book's spread P&L, less borrow and funding spreads
# Total = cash + market excess + pair excess. Regressing the book's excess
# return on the market's excess return splits it into beta (what the S&P
# allocation and any leftover pair tilt earned) and alpha (what the decisions
# earned). Alpha before costs vs after costs shows what over-trading gives away.

# Fed funds effective, approximate step fallback. VERIFY post-2025 before publishing.
_EFFR = [('2020-03-16', 0.08), ('2022-03-17', 0.33), ('2022-05-05', 0.83),
         ('2022-06-16', 1.58), ('2022-07-28', 2.33), ('2022-09-22', 3.08),
         ('2022-11-03', 3.83), ('2022-12-15', 4.33), ('2023-02-02', 4.58),
         ('2023-03-23', 4.83), ('2023-05-04', 5.08), ('2023-07-27', 5.33),
         ('2024-09-19', 4.83), ('2024-11-08', 4.58), ('2024-12-19', 4.33),
         ('2025-09-18', 4.08), ('2025-10-30', 3.87), ('2025-12-11', 3.64)]

def load_usd_rate(index):
    url = 'https://fred.stlouisfed.org/graph/fredgraph.csv?id=EFFR'
    try:
        df = pd.read_csv(url, na_values='.')
        s = pd.Series(df.iloc[:, 1].values, index=pd.to_datetime(df.iloc[:, 0])).dropna()
        src = 'FRED EFFR'
    except Exception:
        d = pd.Series(dict(_EFFR)); d.index = pd.to_datetime(d.index)
        s = d.reindex(pd.date_range(d.index[0], index[-1])).ffill(); src = 'EFFR fallback (approximate)'
    return s.reindex(s.index.union(index)).ffill().reindex(index), src

def accrue(rate_pct, index):
    """Daily accrual of an annual % rate, ACT/360, on a business-day index."""
    days = pd.Series(index, index=index).diff().dt.days.fillna(1)
    return (rate_pct.reindex(index).ffill() / 100.0) * days / 360

def market_excess(prices, index, rate_pct, div_yield_pct=0.0):
    """Daily excess return of an index over its own currency's cash rate.
    For a foreign index this is the FX-hedged return (the hedge earns the rate
    differential). ^GSPC and ^STOXX50E are PRICE indices, so add the dividend
    yield back or the market leg is understated (~1.3%/yr S&P, ~3%/yr SX5E)."""
    r = prices.reindex(prices.index.union(index)).ffill().pct_change().reindex(index)
    return r + div_yield_pct / 100 / 252 - accrue(rate_pct, index)

def portable_alpha(book, markets, estr, base_rate=None, pair_scale=1.0,
                   borrow_bps=35.0, rebate_haircut_bps=10.0, funding_spread_bps=25.0):
    """Cash + market overlays + pair overlay.
    markets: {name: dict(px=closes, rate=cash-rate % series in that currency,
                         w=allocation, div=dividend yield %, lag=True/False)}
      lag=True for markets that close after Europe (S&P): the regression then
      adds yesterday's move too. EURO STOXX closes with the pairs, so lag=False.
    base_rate: None -> cash earns €STR; a number -> flat baseline %. The Sharpe
    hurdle is always €STR."""
    idx = book.index
    rf = accrue(estr, idx)
    cash = accrue(pd.Series(base_rate, index=idx) if base_rate is not None else estr, idx)
    wl, ws = book.w_long.shift(1).fillna(0), book.w_short.shift(1).fillna(0)
    carry = -(wl * funding_spread_bps + ws * (borrow_bps + rebate_haircut_bps)) / 1e4 / 252
    cols = {'cash': cash, 'rf': rf,
            'pair_gross': pair_scale * book.gross,
            'pair_costs': pair_scale * (book.costs - carry),
            'turnover': pair_scale * book.turnover}
    mkt_total = 0
    for name, m in markets.items():
        x = market_excess(m['px'], idx, m['rate'], m.get('div', 0.0))
        cols[f'x_{name}'] = x                          # factor: 100% of that market
        cols[f'mkt_{name}'] = m.get('w', 0.0) * x      # what the allocation earned
        mkt_total = mkt_total + cols[f'mkt_{name}']
    out = pd.DataFrame(cols)
    out['market'] = mkt_total
    out = out.dropna()
    out['pair_net'] = out.pair_gross - out.pair_costs
    out['total'] = out.cash + out.market + out.pair_net
    out['excess'] = out.total - out.rf
    out.attrs['lags'] = {n: m.get('lag', False) for n, m in markets.items()}
    return out

def _ols_nw(y, X, lags=5):
    """OLS with Newey-West standard errors (numpy only)."""
    X = np.column_stack([np.ones(len(X)), X]); b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b; XtX_inv = np.linalg.inv(X.T @ X)
    S = (X * e[:, None]).T @ (X * e[:, None])
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = (X[L:] * e[L:, None]).T @ (X[:-L] * e[:-L, None]); S += w * (G + G.T)
    se = np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))
    return b, se, e, 1 - e.var() / y.var()

def strip_beta(ret, pa, lags=5):
    """Alpha and a beta per market for `ret` (already excess of €STR).
    Markets flagged lag=True get a t-1 term too, and their beta is the sum
    (Dimson). With both indices in, the EURO STOXX beta is the European
    exposure and the S&P beta is what the US adds on top of it - they overlap,
    so read the pair's neutrality off the sum and the SX5E term, not S&P alone."""
    X = {}
    for n, lag in pa.attrs['lags'].items():
        X[n] = pa[f'x_{n}']
        if lag:
            X[f'{n}_lag'] = pa[f'x_{n}'].shift(1)
    X = pd.DataFrame(X)
    d = pd.concat([ret.rename('y'), X], axis=1).dropna()
    b, se, e, r2 = _ols_nw(d.y.values, d.drop(columns='y').values, lags)
    coef = dict(zip(['alpha'] + list(X.columns), b))
    out = {'alpha_%/yr': coef['alpha'] * 252 * 100, 'alpha_t': b[0] / se[0]}
    for n in pa.attrs['lags']:
        out[f'beta_{n}'] = coef[n] + coef.get(f'{n}_lag', 0.0)
    out['beta_total'] = sum(out[f'beta_{n}'] for n in pa.attrs['lags'])
    out.update({'r2': r2, 'resid_vol_%': e.std() * np.sqrt(252) * 100,
                'info_ratio': b[0] / e.std() * np.sqrt(252)})
    return out

def decision_report(pa):
    """What the book earned, what each market leg earned, and what the
    decisions earned before and after the cost of making them."""
    a = np.sqrt(252); yrs = len(pa) / 252
    cum = (1 + pa.total).cumprod()
    head = {'total_ret_%/yr': (cum.iloc[-1] ** (1 / yrs) - 1) * 100,
            'vol_%': pa.total.std() * a * 100,
            'return/vol (no rf, NOT Sharpe)': pa.total.mean() / pa.total.std() * a,
            'sharpe (excess of €STR)': pa.excess.mean() / pa.excess.std() * a,
            'max_dd_%': ((cum / cum.cummax()) - 1).min() * 100,
            'cash_%/yr': pa.cash.sum() / yrs * 100}
    for n in pa.attrs['lags']:
        head[f'{n}_leg_%/yr'] = pa[f'mkt_{n}'].sum() / yrs * 100
    head['pair_net_%/yr'] = pa.pair_net.sum() / yrs * 100
    book = strip_beta(pa.excess, pa)
    gross = strip_beta(pa.pair_gross, pa)
    net = strip_beta(pa.pair_net, pa)
    turn = pa.turnover.sum() / yrs
    dec = {'decision_alpha_gross_%/yr': gross['alpha_%/yr'],
           'cost_of_trading+carry_%/yr': pa.pair_costs.sum() / yrs * 100,
           'decision_alpha_net_%/yr': net['alpha_%/yr'],
           'net_alpha_t': net['alpha_t'],
           **{f'pair_leftover_beta_{n}': net[f'beta_{n}'] for n in pa.attrs['lags']},
           'info_ratio_net': net['info_ratio'],
           'turnover_x_capital/yr': turn,
           'breakeven_cost_bps': gross['alpha_%/yr'] * 100 / turn if turn > 0 else np.nan,
           'alpha_kept_%': 100 * net['alpha_%/yr'] / gross['alpha_%/yr'] if gross['alpha_%/yr'] > 0 else np.nan}
    return pd.Series(head).round(2), pd.Series(book).round(3), pd.Series(dec).round(2)

# Usage (after Part 1 / the walk-forward):
#   dl = lambda t: yf.download(t, start='2021-09-27', end='2026-09-25', progress=False)['Close'].squeeze()
#   spx, sx5e = dl('^GSPC'), dl('^STOXX50E')
#   estr, _ = load_estr(sx5e.index); usd, _ = load_usd_rate(sx5e.index)
#   book, log = rolling_walk_forward(px, NAMES, mkt, estr, form_days=504)
#   pa = portable_alpha(book, {
#       'spx':  dict(px=spx,  rate=usd,  w=0.20, div=1.3, lag=True),   # hedged to EUR
#       'sx5e': dict(px=sx5e, rate=estr, w=0.10, div=3.0, lag=False)}, estr)
#   head, book_ab, decisions = decision_report(pa)
#   print(head, book_ab, decisions, sep='\n\n')
