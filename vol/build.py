"""Build the volatility surface for one day and store it (design note section 10).

Pipeline:  fetch -> store raw -> clean -> forward -> imply -> calibrate -> calendar
           -> QA -> store params/forwards/QA.  Sends nothing; market data and analytics only.

Usage:
    python build.py                 # today, SPY, into the book's delta1.db
    python build.py 2026-10-23 SPY  # a given date and underlying
    python build.py --db /tmp/x.db --max-expiries 12
"""
import sys, argparse, datetime as dt
import numpy as np
import db, chain, clean, forward, imply, svi, surface as surfmod, qa


def build(as_of=None, underlying='SPY', db_path=None, max_expiries=None, store=True, exercise=None):
    as_of = as_of or dt.date.today().isoformat()
    as_of_date = dt.date.fromisoformat(as_of)
    symbol, default_exercise = chain.resolve(underlying)
    exercise = exercise or default_exercise         # 'european' (SPX) or 'american' (SPY)
    con = db.connect(db_path or (':memory:' if not store else None))
    db.ensure_schema(con)
    run_id = db.run(con, f'vol_build {underlying} {as_of} {exercise}')

    spot, raw, retrieved_at = chain.fetch(symbol, max_expiries=max_expiries)
    n_raw = chain.store(con, as_of, underlying, spot, raw, 'yahoo', retrieved_at) if store else 0
    filt, flog = clean.basic_filter(raw)

    slices, forwards, slice_meta = [], {}, []
    for expiry, edf in filt.groupby('expiry'):
        T = (dt.date.fromisoformat(expiry) - as_of_date).days / 365.0
        if T <= 0:
            continue
        calls = {float(r.strike): float(r.mid) for r in edf[edf.right == 'C'].itertuples()}
        puts = {float(r.strike): float(r.mid) for r in edf[edf.right == 'P'].itertuples()}
        F, D, n_pairs = forward.implied_forward(calls, puts)
        if F is None:
            continue
        quotes, slog = clean.select_otm(edf, F, D)
        if not quotes:
            continue
        tv = imply.slice_total_variance(quotes, F, D, T, exercise=exercise, S=spot)
        if len(tv) < 5:
            continue
        ex_prem = float(np.mean([r['ex_premium'] for r in tv])) if exercise == 'american' else 0.0
        k = np.array([r['k'] for r in tv])
        w = np.array([r['w'] for r in tv])
        vega = np.array([r['vega'] for r in tv])
        params, rmse, arb_ok = svi.fit_slice(k, w, vega, T)
        slices.append((T, params))
        forwards[T] = (F, D)
        slice_meta.append({'T': T, 'expiry': expiry, 'F': F, 'D': D, 'rmse': rmse,
                           'arb_ok': arb_ok, 'n': len(tv), 'ex_premium_px': ex_prem,
                           'n_pairs': n_pairs, 'otm_calls': slog['otm_calls'],
                           'otm_puts': slog['otm_puts'], 'otm_kept': slog['kept'],
                           'quotes': [{'strike': r['strike'], 'right': r['right'],
                                       'sigma': r['sigma']} for r in tv]})

    # Calendar repair, then build the surface on the adjusted slices.
    slices, n_fixed = svi.enforce_calendar(slices)
    params_by_T = {T: p for T, p in slices}
    for m in slice_meta:
        m['params'] = params_by_T[m['T']]
    surface = surfmod.Surface(spot, slices, forwards, as_of, underlying)

    vix = chain.vix()
    prev_summary = _prev_summary(con, underlying, as_of)
    coverage = {'n_expiries': len(slice_meta), 'n_quotes': sum(m['n'] for m in slice_meta)}
    checks = qa.checks(surface, slice_meta, vix, prev_summary, coverage)

    if store:
        _store(con, as_of, underlying, slice_meta, checks, flog, surface)
    db.finish(con, run_id, n_raw,
              notes=f'{len(slice_meta)} slices, calendar_fixes={n_fixed}, spot={spot:.2f}')
    con.close()
    return surface, slice_meta, checks, {'spot': spot, 'vix': vix, 'basic_filter': flog,
                                         'n_raw': n_raw, 'calendar_fixes': n_fixed,
                                         'exercise': exercise, 'underlying': underlying}


def _prev_summary(con, underlying, as_of):
    """Most recent stored constant-maturity summary before as_of, for the stability check."""
    row = con.execute(
        'SELECT cm30_atm, cm30_varswap, cm30_rr25, cm30_bf25, spot FROM vol_surface_summary '
        'WHERE underlying=? AND as_of<? ORDER BY as_of DESC LIMIT 1', (underlying, as_of)).fetchone()
    if not row:
        return None
    keys = ('cm30_atm', 'cm30_varswap', 'cm30_rr25', 'cm30_bf25', 'spot')
    return dict(zip(keys, row))


def _store(con, as_of, underlying, slice_meta, checks, flog, surface):
    for m in slice_meta:
        con.execute('INSERT OR IGNORE INTO vol_forwards '
                    '(as_of,underlying,expiry,t_years,forward,discount,n_pairs,source) VALUES (?,?,?,?,?,?,?,?)',
                    (as_of, underlying, m['expiry'], m['T'], m['F'], m['D'], m['n_pairs'], 'yahoo'))
        p = m['params']
        con.execute('INSERT OR IGNORE INTO vol_surface_params '
                    '(as_of,underlying,expiry,t_years,a,b,rho,m,sigma,rmse_volpts,n_quotes,arb_ok,source) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (as_of, underlying, m['expiry'], m['T'], p['a'], p['b'], p['rho'], p['m'],
                     p['sigma'], m['rmse'], m['n'], int(m['arb_ok']), 'yahoo'))
        # per-expiry cleaning counts
        for metric, value in (('otm_calls', m['otm_calls']), ('otm_puts', m['otm_puts']),
                              ('otm_kept', m['otm_kept']), ('forward_pairs', m['n_pairs']),
                              ('fitted_quotes', m['n']), ('mean_ex_premium_px', m['ex_premium_px'])):
            con.execute('INSERT OR IGNORE INTO vol_clean_log '
                        '(as_of,underlying,expiry,metric,value,source) VALUES (?,?,?,?,?,?)',
                        (as_of, underlying, m['expiry'], metric, value, 'yahoo'))
    # whole-chain cleaning counts
    for metric, value in flog.items():
        con.execute('INSERT OR IGNORE INTO vol_clean_log '
                    '(as_of,underlying,expiry,metric,value,source) VALUES (?,?,?,?,?,?)',
                    (as_of, underlying, 'ALL', metric, float(value), 'yahoo'))
    for c in checks:
        con.execute('INSERT OR IGNORE INTO vol_surface_qa '
                    '(as_of,underlying,check_name,result,detail,source) VALUES (?,?,?,?,?,?)',
                    (as_of, underlying, c['check'], c['result'], c['detail'], 'yahoo'))
    s = surface.summary()
    con.execute('INSERT OR IGNORE INTO vol_surface_summary '
                '(as_of,underlying,cm30_atm,cm30_varswap,cm30_rr25,cm30_bf25,spot,source) '
                'VALUES (?,?,?,?,?,?,?,?)',
                (as_of, underlying, s['cm30_atm'], s['cm30_varswap'], s['cm30_rr25'],
                 s['cm30_bf25'], s['spot'], 'yahoo'))
    con.commit()


def _print(surface, slice_meta, checks, info):
    print(f"\n{info['underlying']} ({info['exercise']})   spot {info['spot']:.2f}   vix {info['vix']}   "
          f"raw quotes stored {info['n_raw']}   calendar fixes {info['calendar_fixes']}")
    prem = info['exercise'] == 'american'
    print("\nexpiry        T(yr)   forward   atm_vol   25d_RR   25d_BF   rmse(vp)  n  arb"
          + ("   exPrem$" if prem else ""))
    for m in sorted(slice_meta, key=lambda x: x['T']):
        T = m['T']
        rr, bf = surface.risk_reversal(T), surface.butterfly(T)
        rr = f"{rr*100:+6.2f}" if rr is not None else "   n/a"
        bf = f"{bf*100:+6.2f}" if bf is not None else "   n/a"
        extra = f"   {m['ex_premium_px']:7.4f}" if prem else ""
        print(f"{m['expiry']}  {T:6.3f}  {m['F']:8.2f}  {surface.atm_vol(T)*100:6.2f}  "
              f"{rr}   {bf}   {m['rmse']:6.2f}  {m['n']:2d}  {'ok' if m['arb_ok'] else 'NO'}{extra}")
    print("\nQA:")
    for c in checks:
        print(f"  {c['check']:20s} {c['result']:5s}  {c['detail']}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('tokens', nargs='*',
                    help='a date (YYYY-MM-DD) and/or an underlying (SPY, SPX, XSP), in any order')
    ap.add_argument('--db', default=None)
    ap.add_argument('--max-expiries', type=int, default=None)
    ap.add_argument('--no-store', action='store_true')
    ap.add_argument('--exercise', choices=['european', 'american'], default=None,
                    help='override the default (SPX=european, SPY=american)')
    a = ap.parse_args()
    # Classify positionals: anything that parses as a date is the as_of, else the underlying.
    as_of, underlying = None, 'SPY'
    for tok in a.tokens:
        try:
            dt.date.fromisoformat(tok)
            as_of = tok
        except ValueError:
            underlying = tok
    s, meta, checks, info = build(as_of, underlying, a.db, a.max_expiries,
                                  store=not a.no_store, exercise=a.exercise)
    _print(s, meta, checks, info)
