"""Black-Scholes pricing, in two forms.

Black-76 (forward form) is used for pricing and inversion: it takes the forward F
and discount factor D, which is exactly what put-call parity gives us (section 5 of
the design note), so dividends and borrow never have to be modelled separately.

The spot form (with continuous dividend yield q) is used only for the greeks, where
the desk wants sensitivities to the *spot* S, not the forward.
"""
import math
from math import log, sqrt, exp

SQRT2PI = math.sqrt(2.0 * math.pi)


def _n(x):      # standard normal pdf
    return math.exp(-0.5 * x * x) / SQRT2PI


def _N(x):      # standard normal cdf, via erf
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


# ---- Black-76: price and vega from the forward ----

def black76_price(F, K, T, sigma, D, right):
    """Price of a European option from forward F, discount D=exp(-rT), vol sigma."""
    if T <= 0 or sigma <= 0:
        intrinsic = max(F - K, 0.0) if right == 'C' else max(K - F, 0.0)
        return D * intrinsic
    v = sigma * sqrt(T)
    d1 = (log(F / K) + 0.5 * v * v) / v
    d2 = d1 - v
    if right == 'C':
        return D * (F * _N(d1) - K * _N(d2))
    return D * (K * _N(-d2) - F * _N(-d1))


def black76_vega(F, K, T, sigma, D):
    """dPrice/dSigma (same for call and put). Used to weight the calibration fit."""
    if T <= 0 or sigma <= 0:
        return 0.0
    v = sigma * sqrt(T)
    d1 = (log(F / K) + 0.5 * v * v) / v
    return D * F * sqrt(T) * _n(d1)


def european_spot(S, K, T, sigma, r, q, right):
    """European option price in spot terms (via Black-76 with F = S*exp((r-q)T))."""
    F, D = S * exp((r - q) * T), exp(-r * T)
    return black76_price(F, K, T, sigma, D, right)


# ---- Spot-form greeks (continuous dividend yield q) ----
# r and q are recovered from the implied forward and discount:
#   D = exp(-rT)          -> r = -ln(D)/T
#   F = S*exp((r-q)T)     -> q = r - ln(F/S)/T

def greeks(S, K, T, sigma, r, q, right):
    """First- and second-order greeks in the Black-Scholes spot model.

    Returns a dict. vega, vanna and volga are reported per *1 vol point* (0.01),
    theta per calendar day, rho per 1 percentage point of rate, as a desk quotes them.
    """
    if T <= 0 or sigma <= 0:
        return {k: 0.0 for k in ('delta', 'gamma', 'vega', 'theta', 'rho', 'vanna', 'volga')}
    v = sigma * sqrt(T)
    d1 = (log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / v
    d2 = d1 - v
    disc_q, disc_r = exp(-q * T), exp(-r * T)
    pdf = _n(d1)

    delta = disc_q * (_N(d1) if right == 'C' else _N(d1) - 1.0)
    gamma = disc_q * pdf / (S * v)
    vega = S * disc_q * pdf * sqrt(T)                      # per 1.00 of vol
    if right == 'C':
        theta = (-S * disc_q * pdf * sigma / (2 * sqrt(T))
                 - r * K * disc_r * _N(d2) + q * S * disc_q * _N(d1))
        rho = K * T * disc_r * _N(d2)
    else:
        theta = (-S * disc_q * pdf * sigma / (2 * sqrt(T))
                 + r * K * disc_r * _N(-d2) - q * S * disc_q * _N(-d1))
        rho = -K * T * disc_r * _N(-d2)
    vanna = -disc_q * pdf * d2 / sigma                     # dDelta/dSigma (per 1.00 vol)
    volga = vega * d1 * d2 / sigma                         # dVega/dSigma (per 1.00 vol)

    return {
        'delta': delta,
        'gamma': gamma,
        'vega': vega / 100.0,                              # per vol point
        'theta': theta / 365.0,                            # per calendar day
        'rho': rho / 100.0,                                # per 1% rate
        'vanna': vanna / 100.0,
        'volga': volga / 10000.0,                          # per vol point squared
    }
