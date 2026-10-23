"""American options: pricing and de-Americanization (design note section 3.5).

SPY options are American and the underlying pays dividends, so they carry an early-exercise
premium that the European (Black-76) model does not see. This module prices American options
with a Cox-Ross-Rubinstein binomial tree -- the most transparent method: at each node the
holder takes the larger of holding and exercising -- and uses it to:

  1. price an American option (price),
  2. measure the early-exercise premium (premium = American - European on the same tree),
  3. de-Americanize a market quote (implied_vol): back out the vol consistent with the
     American price, which is the European-equivalent implied vol the surface should use.

Barone-Adesi-Whaley is the faster closed-form approximation used in production; the binomial
is chosen here because it is self-evidently correct and easy to explain.

Continuous dividend yield q and rate r are taken from the forward and discount implied by
put-call parity (r = -ln D / T, q = r - ln(F/S) / T), consistent with the European path.
"""
import numpy as np
from math import exp, sqrt, log
from scipy.optimize import brentq

VOL_LO, VOL_HI = 1e-4, 5.0


def _crr(S, K, T, sigma, r, q, right, american, n):
    """One CRR binomial valuation. Returns the option value at the root."""
    dt = T / n
    u = exp(sigma * sqrt(dt))
    d = 1.0 / u
    p = (exp((r - q) * dt) - d) / (u - d)
    disc = exp(-r * dt)
    # Terminal stock prices and payoffs.
    j = np.arange(n + 1)
    ST = S * u ** j * d ** (n - j)
    V = np.maximum(ST - K, 0.0) if right == 'C' else np.maximum(K - ST, 0.0)
    # Backward induction.
    for i in range(n - 1, -1, -1):
        V = disc * (p * V[1:i + 2] + (1 - p) * V[0:i + 1])
        if american:
            Si = S * u ** np.arange(i + 1) * d ** (i - np.arange(i + 1))
            ex = (Si - K) if right == 'C' else (K - Si)
            V = np.maximum(V, ex)
    return float(V[0])


def price(S, K, T, sigma, r, q, right, n=160):
    return _crr(S, K, T, sigma, r, q, right, True, n)


def european_price(S, K, T, sigma, r, q, right, n=160):
    """European value on the same tree, so the premium isolates early exercise (not discretisation)."""
    return _crr(S, K, T, sigma, r, q, right, False, n)


def premium(S, K, T, sigma, r, q, right, n=160):
    """Early-exercise premium in price terms: American minus European on the same tree."""
    return (_crr(S, K, T, sigma, r, q, right, True, n)
            - _crr(S, K, T, sigma, r, q, right, False, n))


def implied_vol(price_am, S, K, T, r, q, right, n=160):
    """De-Americanize: the vol that makes the binomial American price match the market price.
    Returns None if it cannot be inverted (e.g. price below intrinsic)."""
    if T <= 0 or price_am <= 0:
        return None
    lo = _crr(S, K, T, VOL_LO, r, q, right, True, n)
    hi = _crr(S, K, T, VOL_HI, r, q, right, True, n)
    if not (lo - 1e-9 <= price_am <= hi + 1e-9):
        return None
    try:
        return brentq(lambda s: _crr(S, K, T, s, r, q, right, True, n) - price_am,
                      VOL_LO, VOL_HI, xtol=1e-6, maxiter=100)
    except (ValueError, RuntimeError):
        return None
