"""Daily P&L attribution into the greeks (VRP pre-registration, section 4).

Decomposes one day's change in an option position's value into the greek contributions by a
second-order Taylor expansion, using start-of-day greeks:

    dV ~= delta*dS + 1/2 gamma*dS^2 + theta*dt + vega*dSigma
          + vanna*dS*dSigma + 1/2 volga*dSigma^2 + residual

The residual is the full revaluation minus the explained terms, and should be small (it is the
third-order-and-higher remainder). This is the desk's "P&L explain": it says how much of the
day came from time decay, from the market moving (gamma), from implied vol moving (vega), and
from the cross and vol-of-vol effects.

Units follow bs.greeks: theta per calendar day, vega/vanna per vol point, volga per vol point
squared; so dSigma is passed in vol points and dt in days.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bs


def explain(position, S0, sig0, S1, sig1, dt_days, r, q):
    """position: list of legs (qty, K, T0_years, right). States: spot S, vol sigma (decimal).

    Returns a dict of summed P&L by component plus 'actual', 'explained', 'residual'.
    """
    dS = S1 - S0
    dsig_vp = (sig1 - sig0) * 100.0            # vol points
    dt_years = dt_days / 365.0
    out = {k: 0.0 for k in ('delta', 'gamma', 'theta', 'vega', 'vanna', 'volga')}
    actual = 0.0
    for qty, K, T0, right in position:
        T1 = max(T0 - dt_years, 1e-6)
        g = bs.greeks(S0, K, T0, sig0, r, q, right)
        out['delta'] += qty * g['delta'] * dS
        out['gamma'] += qty * 0.5 * g['gamma'] * dS * dS
        out['theta'] += qty * g['theta'] * dt_days
        out['vega'] += qty * g['vega'] * dsig_vp
        out['vanna'] += qty * g['vanna'] * dS * dsig_vp
        out['volga'] += qty * 0.5 * g['volga'] * dsig_vp * dsig_vp
        actual += qty * (bs.european_spot(S1, K, T1, sig1, r, q, right)
                         - bs.european_spot(S0, K, T0, sig0, r, q, right))
    out['explained'] = sum(out[k] for k in ('delta', 'gamma', 'theta', 'vega', 'vanna', 'volga'))
    out['actual'] = actual
    out['residual'] = actual - out['explained']
    return out
