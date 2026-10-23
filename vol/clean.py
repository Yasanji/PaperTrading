"""Cleaning rules (design note section 4).

Two stages. basic_filter() removes bad quotes before anything that needs the forward.
select_otm() runs per expiry, after the forward is known: it keeps out-of-the-money
options and removes static-arbitrage outliers. Every rule logs how many quotes it drops,
so the effect of each is visible.
"""


def basic_filter(df, max_rel_spread=0.60, require_liquidity=False):
    """df columns: expiry, strike, right, bid, ask, last, volume, open_interest.

    Returns (clean_df_with_mid, log). Rules 1-3 of the design note.
    """
    log, n0 = {}, len(df)
    df = df[(df.bid > 0) & (df.ask > 0) & (df.ask >= df.bid)].copy()
    log['dropped_nonpositive_or_crossed'] = n0 - len(df)

    df['mid'] = 0.5 * (df.bid + df.ask)
    n1 = len(df)
    df = df[(df.ask - df.bid) / df.mid <= max_rel_spread].copy()
    log['dropped_wide_spread'] = n1 - len(df)

    if require_liquidity:
        n2 = len(df)
        df = df[(df.volume.fillna(0) > 0) | (df.open_interest.fillna(0) > 0)].copy()
        log['dropped_illiquid'] = n2 - len(df)

    log['kept'] = len(df)
    return df, log


def _monotone(points, increasing):
    """Greedily drop points that break monotonicity of price in strike.

    points: list of (strike, quote_dict) sorted by strike. Keeps the first point and
    each later one that does not violate the required direction. Removes bad prints
    without fitting through them.
    """
    kept, last = [], None
    for strike, q in points:
        if last is None or (q['mid'] >= last if increasing else q['mid'] <= last):
            kept.append((strike, q))
            last = q['mid']
    return kept


def select_otm(expiry_df, F, D, min_strikes=5):
    """Keep OTM options (puts below F, calls at/above F), apply the intrinsic and
    monotonicity filters, and require enough strikes. Returns (list_of_quotes, log).

    Each returned quote: {strike, right, mid}.
    """
    log = {}
    calls, puts = [], []
    for _, r in expiry_df.iterrows():
        q = {'strike': float(r.strike), 'right': r.right, 'mid': float(r.mid)}
        if r.right == 'C' and r.strike >= F:
            calls.append(q)
        elif r.right == 'P' and r.strike < F:
            puts.append(q)
    log['otm_calls'], log['otm_puts'] = len(calls), len(puts)

    # Intrinsic bound: a quote below discounted intrinsic cannot be inverted.
    calls = [q for q in calls if q['mid'] > D * max(F - q['strike'], 0.0) + 1e-9]
    puts = [q for q in puts if q['mid'] > D * max(q['strike'] - F, 0.0) + 1e-9]

    # Monotonicity: call prices fall with strike, put prices rise with strike.
    calls = _monotone(sorted([(q['strike'], q) for q in calls]), increasing=False)
    puts = _monotone(sorted([(q['strike'], q) for q in puts]), increasing=True)
    quotes = [q for _, q in puts] + [q for _, q in calls]
    log['kept'] = len(quotes)
    log['enough'] = len(quotes) >= min_strikes
    return (quotes if log['enough'] else []), log
