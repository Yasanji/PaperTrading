"""Quality assurance (design note section 9).

Checks 1-2 (arbitrage-free, fit error) are the acceptance gate; 3-4 (VIX cross-check,
reprice error) are monitoring. Each returns a row (check, result, detail) that build.py
stores and prints, so a surface is never published silently.
"""
import numpy as np
import svi

FIT_RMSE_LIMIT = 1.5          # vol points, per slice
VIX_GAP_LIMIT = 3.0           # vol points, 30-day var-swap vs VIX
REPRICE_MEDIAN_LIMIT = 1.0    # vol points
REPRICE_P95_LIMIT = 3.0       # vol points
STABILITY_ATM_LIMIT = 5.0     # vol points, day-over-day move in constant-maturity 30d vol
MIN_EXPIRIES = 4              # coverage: fitted slices
MIN_QUOTES = 40               # coverage: clean quotes used across the surface


def checks(surface, slices, vix=None, prev_summary=None, coverage=None):
    """slices: list of dicts {T, params, rmse, arb_ok, quotes:[{strike,right,sigma}]}.
    prev_summary: the most recent prior day's surface.summary(), or None.
    coverage: {'n_expiries': int, 'n_quotes': int} for the coverage gate, or None.
    """
    out = []

    # 0. Coverage: enough expiries and quotes survived cleaning to trust the surface.
    if coverage is not None:
        ok = coverage['n_expiries'] >= MIN_EXPIRIES and coverage['n_quotes'] >= MIN_QUOTES
        out.append({'check': 'coverage',
                    'result': 'pass' if ok else 'FAIL',
                    'detail': f"expiries={coverage['n_expiries']} (min {MIN_EXPIRIES}); "
                              f"clean_quotes={coverage['n_quotes']} (min {MIN_QUOTES})"})

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
        T30 = 30 / 365.0
        if surface.extrapolated(T30):
            out.append({'check': 'vix_cross_check', 'result': 'n/a',
                        'detail': '30d is beyond the last fitted expiry (extrapolated); '
                                  'need expiries past 30 days for a reliable check'})
        else:
            vs30 = surface.var_swap_vol(T30) * 100
            atm30 = surface.atm_vol(T30) * 100
            gap = vs30 - vix
            out.append({'check': 'vix_cross_check',
                        'result': 'pass' if abs(gap) <= VIX_GAP_LIMIT else 'flag',
                        'detail': f'surface_varswap_30d={vs30:.2f}; atm_30d={atm30:.2f}; '
                                  f'vix={vix:.2f}; gap={gap:+.2f}'})

    # 4. Reprice error: surface vol vs market implied vol, in vol points. Now flags.
    errs = []
    for s in slices:
        for q in s['quotes']:
            errs.append(abs(surface.vol(q['strike'], s['T']) - q['sigma']) * 100)
    if errs:
        med, p95 = float(np.median(errs)), float(np.percentile(errs, 95))
        flag = med > REPRICE_MEDIAN_LIMIT or p95 > REPRICE_P95_LIMIT
        out.append({'check': 'reprice_vol_error',
                    'result': 'flag' if flag else 'pass',
                    'detail': f'median={med:.3f} (limit {REPRICE_MEDIAN_LIMIT}); '
                              f'p95={p95:.3f} (limit {REPRICE_P95_LIMIT}) vol pts'})

    # 5. Day-over-day stability: constant-maturity 30d vol should move smoothly.
    if prev_summary is not None:
        today = surface.summary()
        d_atm = today['cm30_atm'] - prev_summary['cm30_atm']
        d_vs = today['cm30_varswap'] - prev_summary['cm30_varswap']
        big = abs(d_atm) > STABILITY_ATM_LIMIT or abs(d_vs) > STABILITY_ATM_LIMIT
        out.append({'check': 'stability_dod',
                    'result': 'flag' if big else 'pass',
                    'detail': f'cm30_atm {prev_summary["cm30_atm"]:.2f}->{today["cm30_atm"]:.2f} '
                              f'({d_atm:+.2f}); cm30_varswap ({d_vs:+.2f}); limit {STABILITY_ATM_LIMIT}'})
    return out
