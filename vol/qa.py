"""Quality assurance (design note section 9).

Checks 1-2 (arbitrage-free, fit error) are the acceptance gate; 3-4 (VIX cross-check,
reprice error) are monitoring. Each returns a row (check, result, detail) that build.py
stores and prints, so a surface is never published silently.
"""
import numpy as np
import svi

FIT_RMSE_LIMIT = 1.5          # vol points, per slice
VIX_GAP_LIMIT = 3.0           # vol points, 30-day ATM vs VIX


def checks(surface, slices, vix=None):
    """slices: list of dicts {T, params, rmse, arb_ok, quotes:[{strike,right,sigma}]}."""
    out = []

    # 1. Butterfly (within expiry) + calendar (across expiries). Hard gate.
    k_grid = np.linspace(-0.6, 0.4, 120)
    bad_fly = [round(s['T'], 4) for s in slices
               if not svi.butterfly_ok(s['params'], k_grid)]
    Ts = surface.Ts
    cal_bad = 0
    for i in range(1, len(Ts)):
        if np.any(svi.w(surface.params[Ts[i - 1]], k_grid)
                  - svi.w(surface.params[Ts[i]], k_grid) > 1e-6):
            cal_bad += 1
    ok = (not bad_fly) and cal_bad == 0
    out.append({'check': 'arbitrage_free', 'result': 'pass' if ok else 'FAIL',
                'detail': f'butterfly_violations={bad_fly or 0}; calendar_crossings={cal_bad}'})

    # 2. Fit error per slice.
    worst = max((s['rmse'] for s in slices), default=0.0)
    flagged = [round(s['T'], 4) for s in slices if s['rmse'] > FIT_RMSE_LIMIT]
    out.append({'check': 'fit_rmse_volpts',
                'result': 'pass' if not flagged else 'flag',
                'detail': f'worst={worst:.2f}; limit={FIT_RMSE_LIMIT}; flagged_T={flagged or 0}'})

    # 3. VIX cross-check: the surface's own 30-day variance-swap vol against VIX.
    # VIX is a variance-swap measure over the whole strip, not ATM vol, so this is the
    # like-for-like comparison. ATM is reported too, to show the skew/convexity premium.
    if vix is not None:
        vs30 = surface.var_swap_vol(30 / 365.0) * 100
        atm30 = surface.atm_vol(30 / 365.0) * 100
        gap = vs30 - vix
        out.append({'check': 'vix_cross_check',
                    'result': 'pass' if abs(gap) <= VIX_GAP_LIMIT else 'flag',
                    'detail': f'surface_varswap_30d={vs30:.2f}; atm_30d={atm30:.2f}; '
                              f'vix={vix:.2f}; gap={gap:+.2f}'})

    # 4. Reprice error: surface vol vs market implied vol, in vol points.
    errs = []
    for s in slices:
        for q in s['quotes']:
            errs.append(abs(surface.vol(q['strike'], s['T']) - q['sigma']) * 100)
    if errs:
        out.append({'check': 'reprice_vol_error',
                    'result': 'pass',
                    'detail': f'median={np.median(errs):.3f}; p95={np.percentile(errs, 95):.3f} vol pts'})
    return out
