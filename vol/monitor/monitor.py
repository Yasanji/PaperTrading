"""Skew & term-structure monitor: the live surface cross-section plus where today's vol
signals sit versus their own history — the screen a trader scans for relative value.

Live (from our SPX surface): ATM vol, 25-delta risk reversal (skew) and butterfly per expiry.
History (CBOE VIX-complex indices, which have years of data where option-surface history does not):
  - ATM term structure at fixed tenors: VIX9D (9d), VIX (30d), VIX3M (93d), VIX6M (180d)
  - term-structure slope = VIX3M - VIX (contango positive / backwardation negative)
  - SKEW index as the historical skew proxy
For each signal we report the current value and its percentile and z-score versus 1- and 5-year history.

Usage:  python monitor.py [out.json]
"""
import os, sys, json, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TENORS = {'^VIX9D': 9, '^VIX': 30, '^VIX3M': 93, '^VIX6M': 180}


def _series(sym, start='2012-01-01'):
    import yfinance as yf
    return yf.download(sym, start=start, progress=False, auto_adjust=False)['Close'].squeeze().dropna()


def _pct_z(series, value):
    """Percentile rank (0-100) and z-score of value within series."""
    s = series.dropna().values
    if len(s) < 20:
        return None, None
    pct = float((s < value).mean() * 100)
    z = float((value - s.mean()) / s.std()) if s.std() > 0 else 0.0
    return round(pct, 0), round(z, 2)


def _read(pct, kind):
    if pct is None:
        return 'n/a'
    if kind == 'skew':   # high percentile = skew/vol rich
        return 'rich' if pct >= 80 else ('cheap' if pct <= 20 else 'normal')
    if kind == 'slope':  # high = steep contango (calm); low/neg = backwardation (stress)
        return 'steep contango' if pct >= 80 else ('backwardation/stress' if pct <= 20 else 'normal')
    return 'high' if pct >= 80 else ('low' if pct <= 20 else 'normal')


def _surface_cross_section(max_expiries=12):
    """Live SPX surface cross-section, with retry (the free feed is occasionally rate-limited)."""
    import time
    import build
    for _ in range(4):
        try:
            surface, meta, checks, info = build.build(underlying='SPX', max_expiries=max_expiries, store=False)
            if meta:
                return [{'expiry': m['expiry'], 'dte': round(m['T'] * 365), 'atm_vol': round(surface.atm_vol(m['T']) * 100, 2),
                         'rr25': round((surface.risk_reversal(m['T']) or 0) * 100, 2),
                         'bf25': round((surface.butterfly(m['T']) or 0) * 100, 2)} for m in sorted(meta, key=lambda x: x['T'])]
        except Exception:
            pass
        time.sleep(4)
    return []


def run(out_path=None):
    vix = {s: _series(s) for s in TENORS}
    skew = _series('^SKEW')
    df = pd.DataFrame({TENORS[s]: v for s, v in vix.items()}).dropna()
    slope = df[93] - df[30]                    # VIX3M - VIX

    cur = {d: float(df[d].iloc[-1]) for d in sorted(df.columns)}
    cur_slope = float(slope.iloc[-1])
    cur_skew = float(skew.iloc[-1])
    last_date = df.index[-1].strftime('%Y-%m-%d')

    def sig(name, series, value, kind):
        p1, z1 = _pct_z(series.tail(252), value)
        p5, z5 = _pct_z(series.tail(1260), value)
        return {'name': name, 'value': round(value, 2), 'pct_1y': p1, 'pct_5y': p5,
                'z_1y': z1, 'read': _read(p1, kind)}

    signals = [
        sig('VIX (30d ATM)', df[30], cur[30], 'level'),
        sig('Term slope (VIX3M-VIX)', slope, cur_slope, 'slope'),
        sig('SKEW index', skew, cur_skew, 'skew'),
    ]

    # history series for charts (downsample to keep size modest)
    hist = df.join(slope.rename('slope')).join(skew.rename('skew')).dropna()
    step = max(1, len(hist) // 1500)
    hist = hist.iloc[::step]
    history = [{'date': d.strftime('%Y-%m-%d'), 'vix': round(float(r[30]), 2), 'vix3m': round(float(r[93]), 2),
                'slope': round(float(r['slope']), 2), 'skew': round(float(r['skew']), 2)}
               for d, r in hist.iterrows()]

    def band(series):
        s = series.tail(1260).dropna().values
        return {k: round(float(np.percentile(s, q)), 2) for k, q in
                [('p5', 5), ('p25', 25), ('p50', 50), ('p75', 75), ('p95', 95)]}

    result = {
        'meta': {'generated': dt.datetime.utcnow().isoformat(timespec='seconds'), 'as_of': last_date,
                 'update_mode': 'end-of-day batch (static snapshot embedded at build time)',
                 'note': 'live cross-section from the SPX surface; history from CBOE VIX-complex indices'},
        'term_now': [{'tenor_days': d, 'vol': round(cur[d], 2)} for d in sorted(cur)],
        'surface_term': _surface_cross_section(),
        'signals': signals,
        'bands': {'slope': band(slope), 'skew': band(skew)},
        'history': history,
    }
    if out_path:
        json.dump(result, open(out_path, 'w'))
    _print(signals, cur, cur_slope, cur_skew)
    return result


def _print(signals, cur, cur_slope, cur_skew):
    print("\n=== Skew & term-structure monitor ===")
    print(f"term structure: 9d {cur[9]:.2f}  30d {cur[30]:.2f}  3m {cur[93]:.2f}  6m {cur[180]:.2f}  "
          f"({'contango' if cur_slope>0 else 'backwardation'}, slope {cur_slope:+.2f})")
    print(f"SKEW {cur_skew:.1f}\n")
    for s in signals:
        print(f"  {s['name']:26s} {s['value']:>7.2f}   1y %ile {str(s['pct_1y']):>5}  5y %ile {str(s['pct_5y']):>5}"
              f"  z {str(s['z_1y']):>6}   {s['read']}")


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else None)
