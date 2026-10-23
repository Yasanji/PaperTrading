"""Forward and discount from put-call parity (design note section 5).

Put-call parity:  C(K) - P(K) = D * (F - K).
Across strikes that have both a call and a put, (C - P) is a straight line in K:
its slope is -D and its intercept is D*F. A least-squares line through those points
gives the discount D and the forward F, with dividends and borrow already inside F.
"""
import numpy as np


def implied_forward(calls, puts):
    """calls, puts: dict strike -> mid price for one expiry.

    Returns (F, D, n_pairs) or (None, None, 0) if too few paired strikes.
    """
    common = sorted(set(calls) & set(puts))
    if len(common) < 3:
        return None, None, 0
    K = np.array(common, dtype=float)
    y = np.array([calls[k] - puts[k] for k in common])     # C - P
    # Fit y = slope*K + intercept ; slope = -D, intercept = D*F.
    slope, intercept = np.polyfit(K, y, 1)
    D = -slope
    if D <= 0:
        return None, None, len(common)
    F = intercept / D
    return float(F), float(D), len(common)
