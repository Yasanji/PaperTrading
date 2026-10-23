"""SVI smile calibration with no-arbitrage checks (design note section 7).

Each expiry's total-variance smile is fitted with the raw SVI parameterization

    w(k) = a + b * ( rho*(k-m) + sqrt((k-m)^2 + sigma^2) )

Five interpretable parameters: a level, b wing slope, rho asymmetry (skew),
m horizontal shift, sigma smoothness near the money. The fit is vega-weighted so
liquid near-the-money quotes count most. After fitting we check Gatheral's butterfly
condition; across expiries we enforce that total variance never falls as T rises.
"""
import numpy as np
from scipy.optimize import least_squares

PARAMS = ('a', 'b', 'rho', 'm', 'sigma')


def w(p, k):
    """Total implied variance at log-moneyness k (k may be scalar or array)."""
    x = np.asarray(k) - p['m']
    return p['a'] + p['b'] * (p['rho'] * x + np.sqrt(x * x + p['sigma'] ** 2))


def _derivs(p, k):
    x = np.asarray(k) - p['m']
    R = np.sqrt(x * x + p['sigma'] ** 2)
    w0 = p['a'] + p['b'] * (p['rho'] * x + R)
    w1 = p['b'] * (p['rho'] + x / R)
    w2 = p['b'] * (p['sigma'] ** 2) / R ** 3
    return w0, w1, w2


def butterfly_g(p, k):
    """Gatheral's g(k); the risk-neutral density is non-negative iff g(k) >= 0."""
    w0, w1, w2 = _derivs(p, k)
    return (1 - k * w1 / (2 * w0)) ** 2 - (w1 ** 2 / 4) * (1 / w0 + 0.25) + w2 / 2


def butterfly_ok(p, k_grid, tol=-1e-6):
    return float(np.min(butterfly_g(p, k_grid))) >= tol


def fit_slice(k, w_mkt, vega, T, k_grid=None):
    """Fit SVI to one expiry. Returns (params_dict, rmse_vol_points, arb_ok)."""
    k, w_mkt, vega = np.asarray(k), np.asarray(w_mkt), np.asarray(vega)
    if k_grid is None:
        k_grid = np.linspace(k.min() - 0.1, k.max() + 0.1, 100)
    weight = np.sqrt(np.maximum(vega, 1e-8))

    def resid(theta):
        p = dict(zip(PARAMS, theta))
        return weight * (w(p, k) - w_mkt)

    x0 = [max(w_mkt.min(), 1e-6), 0.1, -0.3, 0.0, 0.1]
    lo = [1e-8, 1e-6, -0.999, k.min() - 0.5, 1e-4]
    hi = [w_mkt.max() * 2 + 1.0, 5.0, 0.999, k.max() + 0.5, 2.0]

    b_hi = hi[1]
    for _ in range(4):                       # shrink wing slope if butterfly fails
        hi[1] = b_hi
        sol = least_squares(resid, x0, bounds=(lo, hi), max_nfev=4000)
        p = dict(zip(PARAMS, sol.x))
        if butterfly_ok(p, k_grid):
            break
        b_hi *= 0.6                          # tighten and refit
    arb_ok = butterfly_ok(p, k_grid)

    model_vol = np.sqrt(np.maximum(w(p, k), 0) / T)
    mkt_vol = np.sqrt(np.maximum(w_mkt, 0) / T)
    rmse = float(np.sqrt(np.mean((model_vol - mkt_vol) ** 2)) * 100)
    return p, rmse, arb_ok


def enforce_calendar(slices, k_grid=None):
    """slices: list of (T, params) sorted by T. Lift any later total-variance curve
    that dips below an earlier one, by raising its level a. Returns (slices, n_fixed).

    Light repair: it removes calendar crossings without re-fitting the smile shape.
    QA records whether any fix was applied.
    """
    if k_grid is None:
        k_grid = np.linspace(-0.6, 0.4, 80)
    slices = sorted(slices, key=lambda s: s[0])
    n_fixed = 0
    for i in range(1, len(slices)):
        T_prev, p_prev = slices[i - 1]
        T_cur, p_cur = slices[i]
        gap = w(p_prev, k_grid) - w(p_cur, k_grid)
        worst = float(np.max(gap))
        if worst > 0:                        # current dips below previous somewhere
            p_cur = dict(p_cur, a=p_cur['a'] + worst + 1e-6)
            slices[i] = (T_cur, p_cur)
            n_fixed += 1
    return slices, n_fixed
