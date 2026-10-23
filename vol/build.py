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


def build(as_of=None, underlying='SPY', db_path=None, max_expiries=None, store=True):
    as_of = as_of or dt.date.today().isoformat()
    as_of_date = dt.date.fromisoformat(as_of)
    con = db.connect(db_path)
    db.ensure_schema(con)
    run_id = db.run(con, f'vol_build {underlying} {as_of}')

    spot, raw, retrieved_at = chain.fetch(underlying, max_expiries=max_expiries)
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
        tv = imply.slice_total_variance(quotes, F, D, T)
        if len(tv) < 5:
            continue
        k = np.array([r['k'] for r in tv])
        w = np.array([r['w'] for r in tv])
        vega = np.array([r['vega'] for r in tv])
        params, rmse, arb_ok = svi.fit_slice(k, w, vega, T)
        slices.append((T, params))
        forwards[T] = (F, D)
        slice_meta.append({'T': T, 'expiry': expiry, 'F': F, 'D': D, 'rmse': rmse,
                           'arb_ok': arb_ok, 'n': len(tv),
                           'quotes': [{'strike': r['strike'], 'right': r['right'],
                                       'sigma': r['sigma']} for r in tv]})

    # Calendar repair, then build the surface on the adjusted slices.
    slices, n_fixed = svi.enforce_calendar(slices)
    params_by_T = {T: p for T, p in slices}
    for m in slice_meta:
        m['params'] = params_by_T[m['T']]
    surface = surfmod.Surface(spot, slices, forwards, as_of, underlying)

    vix = chain.vix()
    checks = qa.checks(surface, slice_meta, vix)

    if store:
        _store(con, as_of, underlying, slice_meta, checks)
    db.finish(con, run_id, n_raw,
              notes=f'{len(slice_meta)} slices, calendar_fixes={n_fixed}, spot={spot:.2f}')
    con.close()
    return surface, slice_meta, checks, {'spot': spot, 'vix': vix, 'basic_filter': flog,
                                         'n_raw': n_raw, 'calendar_fixes': n_fixed}


def _store(con, as_of, underlying, slice_meta, checks):
    for m in slice_meta:
        con.execute('INSERT OR IGNORE INTO vol_forwards '
                    '(as_of,underlying,expiry,t_years,forward,discount,n_pairs,source) VALUES (?,?,?,?,?,?,?,?)',
                    (as_of, underlying, m['expiry'], m['T'], m['F'], m['D'], m['n'], 'yahoo'))
        p = m['params']
        con.execute('INSERT OR IGNORE INTO vol_surface_params '
                    '(as_of,underlying,expiry,t_years,a,b,rho,m,sigma,rmse_volpts,n_quotes,arb_ok,source) '
                    'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (as_of, underlying, m['expiry'], m['T'], p['a'], p['b'], p['rho'], p['m'],
                     p['sigma'], m['rmse'], m['n'], int(m['arb_ok']), 'yahoo'))
    for c in checks:
        con.execute('INSERT OR IGNORE INTO vol_surface_qa '
                    '(as_of,underlying,check_name,result,detail,source) VALUES (?,?,?,?,?,?)',
                    (as_of, underlying, c['check'], c['result'], c['detail'], 'yahoo'))
    con.commit()


def _print(surface, slice_meta, checks, info):
    print(f"\nspot {info['spot']:.2f}   vix {info['vix']}   raw quotes stored {info['n_raw']}   "
          f"calendar fixes {info['calendar_fixes']}")
    print("\nexpiry        T(yr)   forward   atm_vol   25d_RR   25d_BF   rmse(vp)  n  arb")
    for m in sorted(slice_meta, key=lambda x: x['T']):
        T = m['T']
        rr, bf = surface.risk_reversal(T), surface.butterfly(T)
        rr = f"{rr*100:+6.2f}" if rr is not None else "   n/a"
        bf = f"{bf*100:+6.2f}" if bf is not None else "   n/a"
        print(f"{m['expiry']}  {T:6.3f}  {m['F']:8.2f}  {surface.atm_vol(T)*100:6.2f}  "
              f"{rr}   {bf}   {m['rmse']:6.2f}  {m['n']:2d}  {'ok' if m['arb_ok'] else 'NO'}")
    print("\nQA:")
    for c in checks:
        print(f"  {c['check']:20s} {c['result']:5s}  {c['detail']}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('as_of', nargs='?', default=None)
    ap.add_argument('underlying', nargs='?', default='SPY')
    ap.add_argument('--db', default=None)
    ap.add_argument('--max-expiries', type=int, default=None)
    ap.add_argument('--no-store', action='store_true')
    a = ap.parse_args()
    s, meta, checks, info = build(a.as_of, a.underlying, a.db, a.max_expiries, store=not a.no_store)
    _print(s, meta, checks, info)
