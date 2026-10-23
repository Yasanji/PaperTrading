"""The calibrated surface: query vol, price and greeks (design note section 8).

A Surface holds the fitted SVI slices and the forward/discount for each expiry.
Between listed expiries it interpolates total variance linearly in T at fixed
log-moneyness, which keeps the result free of calendar arbitrage; outside the listed
range it holds vol flat and the query flags it.
"""
import math
from math import log, sqrt, exp
import numpy as np
from scipy.optimize import brentq
import bs
import svi


class Surface:
    def __init__(self, spot, slices, forwards, as_of=None, underlying=None):
        """slices: list of (T, svi_params). forwards: dict T -> (F, D)."""
        slices = sorted(slices, key=lambda s: s[0])
        self.spot = spot
        self.as_of, self.underlying = as_of, underlying
        self.Ts = [T for T, _ in slices]
        self.params = {T: p for T, p in slices}
        self.forwards = forwards

    # ---- forward / discount at any T ----
    def _forward(self, T):
        Ts = self.Ts
        if T in self.forwards:
            return self.forwards[T]
        if T <= Ts[0]:
            return self.forwards[Ts[0]]
        if T >= Ts[-1]:
            return self.forwards[Ts[-1]]
        i = np.searchsorted(Ts, T)
        T0, T1 = Ts[i - 1], Ts[i]
        (F0, D0), (F1, D1) = self.forwards[T0], self.forwards[T1]
        a = (T - T0) / (T1 - T0)
        return F0 + a * (F1 - F0), D0 + a * (D1 - D0)

    # ---- total variance at (k, T) ----
    def total_var(self, k, T):
        Ts = self.Ts
        if T <= Ts[0]:                                   # flat vol below first expiry
            return float(svi.w(self.params[Ts[0]], k)) * T / Ts[0]
        if T >= Ts[-1]:                                  # flat vol beyond last expiry
            return float(svi.w(self.params[Ts[-1]], k)) * T / Ts[-1]
        i = np.searchsorted(Ts, T)
        T0, T1 = Ts[i - 1], Ts[i]
        w0 = float(svi.w(self.params[T0], k))
        w1 = float(svi.w(self.params[T1], k))
        return w0 + (w1 - w0) * (T - T0) / (T1 - T0)

    def extrapolated(self, T):
        if not self.Ts:
            return True
        return T < self.Ts[0] or T > self.Ts[-1]

    # ---- vol, price, greeks at a strike ----
    def vol(self, K, T):
        F, _ = self._forward(T)
        return sqrt(max(self.total_var(log(K / F), T), 1e-12) / T)

    def _r_q(self, T):
        F, D = self._forward(T)
        r = -log(D) / T
        q = r - log(F / self.spot) / T
        return r, q

    def price(self, K, T, right):
        F, D = self._forward(T)
        return bs.black76_price(F, K, T, self.vol(K, T), D, right)

    def greeks(self, K, T, right):
        r, q = self._r_q(T)
        return bs.greeks(self.spot, K, T, self.vol(K, T), r, q, right)

    # ---- desk views ----
    def atm_vol(self, T):
        return sqrt(max(self.total_var(0.0, T), 1e-12) / T)

    def atm_term(self):
        return [(T, self.atm_vol(T)) for T in self.Ts]

    def _delta_strike(self, T, target, right):
        """Strike whose option has the given (spot) delta, using surface vol at K."""
        F, _ = self._forward(T)
        r, q = self._r_q(T)

        def f(K):
            return bs.greeks(self.spot, K, T, self.vol(K, T), r, q, right)['delta'] - target
        lo, hi = (F, F * 3.0) if right == 'C' else (F * 0.3, F)
        try:
            return brentq(f, lo, hi, xtol=1e-4, maxiter=200)
        except ValueError:
            return None

    def risk_reversal(self, T, delta=0.25):
        """25-delta risk reversal: put vol minus call vol (the desk's skew measure)."""
        Kc = self._delta_strike(T, delta, 'C')
        Kp = self._delta_strike(T, -delta, 'P')
        if Kc is None or Kp is None:
            return None
        return self.vol(Kp, T) - self.vol(Kc, T)

    def butterfly(self, T, delta=0.25):
        """25-delta butterfly: average wing vol minus ATM vol (smile curvature)."""
        Kc = self._delta_strike(T, delta, 'C')
        Kp = self._delta_strike(T, -delta, 'P')
        if Kc is None or Kp is None:
            return None
        return 0.5 * (self.vol(Kc, T) + self.vol(Kp, T)) - self.atm_vol(T)

    def skew(self, T, h=0.01):
        """ATM skew: d(vol)/d(log-moneyness) at the money, by finite difference."""
        F, _ = self._forward(T)
        return (self.vol(F * exp(h), T) - self.vol(F * exp(-h), T)) / (2 * h)

    def forward_vol(self, T1, T2):
        """Annualised vol between two future dates, from the difference in total variance."""
        w1, w2 = self.total_var(0.0, T1), self.total_var(0.0, T2)
        return sqrt(max(w2 - w1, 0.0) / (T2 - T1))

    def summary(self, T=30 / 365.0):
        """Constant-maturity snapshot (default 30 days) for storage and the stability check.
        Constant maturity, so it is comparable day to day even as listed expiries roll off."""
        rr, bf = self.risk_reversal(T), self.butterfly(T)
        return {
            'cm30_atm': self.atm_vol(T) * 100,
            'cm30_varswap': self.var_swap_vol(T) * 100,
            'cm30_rr25': rr * 100 if rr is not None else None,
            'cm30_bf25': bf * 100 if bf is not None else None,
            'spot': self.spot,
        }

    def var_swap_vol(self, T, n=400):
        """Fair variance-swap vol at horizon T, by the VIX/variance-swap static replication:
        a strip of OTM option prices weighted 1/K^2. This is what VIX measures, so it is
        the right thing to compare to VIX (and it sits above ATM vol by the skew/convexity
        premium). Integrated over the surface's own arbitrage-free prices, so it does not
        depend on the far wings of the raw quotes.

            sigma^2 = (2/T) * integral[ OTM(K)/K^2 dK ] / D  -  (1/T)*(F/K0 - 1)^2
        """
        F, D = self._forward(T)
        Ks = np.linspace(0.3 * F, 3.0 * F, n)
        dK = Ks[1] - Ks[0]
        acc = 0.0
        for K in Ks:
            right = 'P' if K < F else 'C'
            acc += self.price(K, T, right) / (K * K) * dK
        K0 = F
        var = (2.0 / T) * acc / D - (1.0 / T) * (F / K0 - 1.0) ** 2
        return sqrt(max(var, 1e-12))
