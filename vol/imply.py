"""Implied volatility by inversion of Black-76 (design note section 6).

Price is monotone increasing in sigma, so the implied vol is the unique root of
(model price - market price). We bracket it and solve with Brent's method, which
needs no derivative and cannot diverge. The working output is total implied
variance w = sigma^2 * T, the natural coordinate for calibration.
"""
from math import sqrt
from scipy.optimize import brentq
import bs

VOL_LO, VOL_HI = 1e-4, 5.0        # 0.01% to 500% annual vol: brackets any real quote


def implied_vol(price, F, K, T, D, right):
    """Return Black-76 implied vol for one option, or None if it cannot be inverted."""
    if T <= 0 or price <= 0:
        return None
    # A price below discounted intrinsic (or above the discounted forward/strike bound)
    # has no implied vol; these should already be filtered, but guard anyway.
    lo = bs.black76_price(F, K, T, VOL_LO, D, right)
    hi = bs.black76_price(F, K, T, VOL_HI, D, right)
    if not (lo - 1e-12 <= price <= hi + 1e-12):
        return None
    try:
        return brentq(lambda s: bs.black76_price(F, K, T, s, D, right) - price,
                      VOL_LO, VOL_HI, xtol=1e-8, maxiter=200)
    except (ValueError, RuntimeError):
        return None


def slice_total_variance(quotes, F, D, T):
    """For one expiry's clean OTM quotes, return rows of (k, w, sigma, vega).

    k = log-moneyness ln(K/F); w = total implied variance sigma^2 * T;
    vega is the Black-76 vega, used later to weight the fit.
    """
    from math import log
    rows = []
    for q in quotes:
        sigma = implied_vol(q['mid'], F, q['strike'], T, D, q['right'])
        if sigma is None:
            continue
        rows.append({
            'strike': q['strike'],
            'right': q['right'],
            'k': log(q['strike'] / F),
            'sigma': sigma,
            'w': sigma * sigma * T,
            'vega': bs.black76_vega(F, q['strike'], T, sigma, D),
        })
    return rows
