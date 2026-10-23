"""VRP backtest: delta-hedged short ATM straddle with daily greek attribution, a trade blotter,
and the current book composition.

Follows vol/vrp/VRP_PREREGISTRATION.md. Implied vol is VIX; realised is trailing 21-day S&P 500
vol. Each month a one-month ATM straddle is sold (when VIX > realised), delta-hedged daily, and
each day's P&L is attributed to the greeks. Records every trade (straddle rolls and the daily
delta hedges) and the live book so the numbers can be decomposed.

Quantities are scaled to a constant vega target ($10,000 per vol point), so straddle counts are
sized to risk, not exchange lots; the delta hedge is shown in S&P mini-future-equivalents ($50
per index point). Writes a JSON for the viewer and prints the dev/hold-out statistics.

Usage:  python backtest.py [out.json]
"""
import os, sys, json, datetime as dt
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bs
import pnl_attribution as pa

R, Q = 0.02, 0.018
V_TARGET = 10_000.0           # position vega target, $ per vol point
T0 = 30 / 365
ROLL_AT = 7 / 365
COST_VOLPTS = 0.10
ES_MULT = 50.0                # S&P mini future: $ per index point, for expressing the delta hedge


def _history():
    import yfinance as yf
    spx = yf.download('^GSPC', start='2005-06-01', progress=False, auto_adjust=False)['Close']
    vix = yf.download('^VIX', start='2005-06-01', progress=False, auto_adjust=False)['Close']
    df = pd.DataFrame({'spx': spx.squeeze(), 'vix': vix.squeeze()}).dropna()
    ret = np.log(df.spx / df.spx.shift(1))
    df['rvol'] = ret.rolling(21).std() * np.sqrt(252) * 100
    return df.dropna()


def _straddle_greeks(S, K, T, sig):
    c = bs.greeks(S, K, T, sig, R, Q, 'C')
    p = bs.greeks(S, K, T, sig, R, Q, 'P')
    return {k: c[k] + p[k] for k in c}


def _straddle_price(S, K, T, sig):
    return (bs.european_spot(S, K, T, sig, R, Q, 'C') + bs.european_spot(S, K, T, sig, R, Q, 'P'))


def run(out_path=None, curve=True):
    df = _history()
    dates = df.index.to_list()
    spx, vix, rvol = df.spx.values, df.vix.values, df.rvol.values

    pos = None                     # {'K','N','T','expiry','entry'}
    prev_net_delta = 0.0
    rows, trades = [], []
    for i in range(len(dates)):
        d = dates[i].strftime('%Y-%m-%d')
        S1, sig1 = spx[i], vix[i] / 100
        rec = {'date': d, 'spot': float(S1), 'vix': float(vix[i]), 'rvol': float(rvol[i]),
               'signal': 'flat', 'gamma': 0.0, 'theta': 0.0, 'vega': 0.0, 'vanna': 0.0,
               'volga': 0.0, 'residual': 0.0, 'gross': 0.0, 'cost': 0.0, 'net': 0.0,
               'delta': 0.0, 'hedge': 0.0}

        if i > 0 and pos is not None:
            S0, sig0 = spx[i - 1], vix[i - 1] / 100
            dt_days = (dates[i] - dates[i - 1]).days
            legs = [(-pos['N'], pos['K'], pos['T'], 'C'), (-pos['N'], pos['K'], pos['T'], 'P')]
            r = pa.explain(legs, S0, sig0, S1, sig1, dt_days, R, Q)
            hedged = r['actual'] - r['delta']
            rec.update(signal='short', gamma=r['gamma'], theta=r['theta'], vega=r['vega'],
                       vanna=r['vanna'], volga=r['volga'], residual=r['residual'], gross=hedged)
            pos['T'] -= dt_days / 365
            # Re-hedge to zero delta: trade the change in the book's net option delta.
            g = _straddle_greeks(S1, pos['K'], max(pos['T'], 1e-6), sig1)
            net_delta = -pos['N'] * g['delta']          # short straddle -> net option delta
            hedge_trade = -(net_delta - prev_net_delta)
            rec['delta'] = net_delta
            rec['hedge'] = hedge_trade
            trades.append({'date': d, 'action': 'DELTA HEDGE', 'instrument': 'S&P fut (hedge)',
                           'qty_es': hedge_trade / ES_MULT, 'price': float(S1),
                           'strike': None, 'expiry': None, 'vol': float(vix[i])})
            prev_net_delta = net_delta

        need_roll = (pos is None) or (pos['T'] <= ROLL_AT)
        if need_roll:
            if pos is not None:
                prem = _straddle_price(S1, pos['K'], max(pos['T'], 1e-6), sig1)
                rec['cost'] += COST_VOLPTS * V_TARGET
                trades.append({'date': d, 'action': 'CLOSE STRADDLE', 'instrument': f"SPX {pos['K']:.0f} straddle",
                               'qty_es': pos['N'], 'price': round(prem, 2), 'strike': pos['K'],
                               'expiry': pos['expiry'], 'vol': float(vix[i])})
                pos, prev_net_delta = None, 0.0
            if vix[i] - rvol[i] > 0:
                g1 = _straddle_greeks(S1, S1, T0, sig1)
                N = V_TARGET / g1['vega'] if g1['vega'] > 0 else 0.0
                if N > 0:
                    expiry = (dates[i] + pd.Timedelta(days=30)).strftime('%Y-%m-%d')
                    prem = _straddle_price(S1, S1, T0, sig1)
                    pos = {'K': float(S1), 'N': N, 'T': T0, 'expiry': expiry, 'entry': d}
                    rec['cost'] += COST_VOLPTS * V_TARGET
                    trades.append({'date': d, 'action': 'SELL STRADDLE', 'instrument': f"SPX {S1:.0f} straddle",
                                   'qty_es': N, 'price': round(prem, 2), 'strike': round(S1, 2),
                                   'expiry': expiry, 'vol': float(vix[i])})
        rec['net'] = rec['gross'] - rec['cost']
        rows.append(rec)

    out = pd.DataFrame(rows)
    out['cum_net'] = out['net'].cumsum()
    summary = _summaries(out)
    by_greek = {k: float(out[k].sum()) for k in ('gamma', 'theta', 'vega', 'vanna', 'volga', 'residual')}
    by_greek['costs'] = -float(out['cost'].sum())
    by_greek['net'] = float(out['net'].sum())

    result = {
        'meta': {'generated': dt.datetime.utcnow().isoformat(timespec='seconds'),
                 'period': f"{out.date.iloc[0]}..{out.date.iloc[-1]}", 'n_days': len(out),
                 'v_target_per_volpt': V_TARGET, 'cost_volpts_per_side': COST_VOLPTS, 'r': R, 'q': Q,
                 'update_mode': 'end-of-day batch (static snapshot embedded at build time)',
                 'note': 'implied=VIX; realised=21d SPX; delta-hedged short ATM straddle'},
        'summary': summary, 'by_greek': by_greek, 'drawdowns': _drawdowns(out),
        'book': _book(pos, spx[-1], vix[-1] / 100, dates[-1]),
        'trades': [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in t.items()}
                   for t in reversed(trades)],      # most recent first
        'daily': [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()}
                  for r in out.to_dict('records')],
    }
    result['curve'], result['surface'] = _spx_views() if curve else ([], {'moneyness_pct': [], 'expiries': []})
    if out_path:
        json.dump(result, open(out_path, 'w'))
    _print(summary, by_greek, result)
    return result


def _book(pos, S, sig, last_date):
    """Current book composition: the held straddle legs with greeks, the net, and the delta hedge."""
    if pos is None:
        return {'held': False}
    T = max(pos['T'], 1e-6)
    legs = []
    net = {k: 0.0 for k in ('delta', 'gamma', 'vega', 'theta', 'vanna', 'volga')}
    for right in ('C', 'P'):
        g = bs.greeks(S, pos['K'], T, sig, R, Q, right)
        px = bs.european_spot(S, pos['K'], T, sig, R, Q, right)
        leg = {'instrument': f"SPX {pos['K']:.0f} {'Call' if right=='C' else 'Put'}",
               'qty': round(-pos['N'], 1), 'dte': round(T * 365),
               'mark': round(px, 2), 'vol': round(sig * 100, 2)}
        for k in net:
            leg[k] = round(-pos['N'] * g[k], 1)
            net[k] += -pos['N'] * g[k]
        legs.append(leg)
    hedge = -net['delta']
    return {'held': True, 'as_of': last_date.strftime('%Y-%m-%d'),
            'strike': round(pos['K'], 2), 'expiry': pos['expiry'], 'entry': pos['entry'],
            'legs': legs, 'net': {k: round(v, 1) for k, v in net.items()},
            'hedge_delta': round(hedge, 1), 'hedge_es': round(hedge / ES_MULT, 1), 'spot': round(S, 2)}


def _nw_t(y, L=21):
    y = np.asarray(y, float); n = len(y); e = y - y.mean(); s = (e * e).mean()
    for k in range(1, L + 1):
        s += 2 * (1 - k / (L + 1)) * (e[k:] * e[:-k]).mean()
    se = np.sqrt(s / n)
    return float(y.mean() / se) if se > 0 else 0.0


def _stats(sub):
    net = sub['net'].values
    if len(net) < 30 or net.std() == 0:
        return None
    ann, vol = net.mean() * 252, net.std() * np.sqrt(252)
    cum = np.cumsum(net); dd = float((cum - np.maximum.accumulate(cum)).min()); half = len(sub) // 2
    return {'ann_pnl': float(ann), 'vol': float(vol), 'sharpe': float(ann / vol), 'nw_t': _nw_t(net),
            'max_dd': dd, 'pct_short': float((sub.signal == 'short').mean() * 100),
            'pos_h1': bool(net[:half].sum() > 0), 'pos_h2': bool(net[half:].sum() > 0)}


def _summaries(out):
    yr = out.date.str[:4].astype(int)
    return {'dev': _stats(out[(yr >= 2006) & (yr <= 2015)]),
            'holdout': _stats(out[yr >= 2016]), 'full': _stats(out)}


def _drawdowns(out, top=5):
    cum = out['cum_net'].values; peak = np.maximum.accumulate(cum); dd = cum - peak
    res, seen = [], []
    for idx in np.argsort(dd):
        if dd[idx] >= -1e-9:
            break
        if any(abs(idx - s) < 60 for s in seen):
            continue
        seen.append(idx); s = idx
        while s > 0 and cum[s] < peak[idx] - 1e-9:
            s -= 1
        res.append({'trough_date': out.date.iloc[idx], 'start_date': out.date.iloc[s], 'depth': float(dd[idx])})
        if len(res) >= top:
            break
    return res


def _spx_views(max_expiries=12):
    """Build the live SPX surface once and return (term-structure table, 3-D surface grid).
    Retries a few times because the free feed is occasionally rate-limited."""
    import time, math
    import build
    err = 'no slices'
    ks = [-0.15, -0.12, -0.10, -0.08, -0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06]
    for _ in range(4):
        try:
            surface, meta, checks, info = build.build(underlying='SPX', max_expiries=max_expiries, store=False)
            if meta:
                meta = sorted(meta, key=lambda x: x['T'])
                curve = [{'expiry': m['expiry'], 'T': round(m['T'], 4), 'forward': round(m['F'], 2),
                          'atm_vol': round(surface.atm_vol(m['T']) * 100, 2),
                          'rr25': round((surface.risk_reversal(m['T']) or 0) * 100, 2),
                          'bf25': round((surface.butterfly(m['T']) or 0) * 100, 2)} for m in meta]
                surf = {'moneyness_pct': [round((math.exp(k) - 1) * 100, 1) for k in ks],
                        'expiries': [{'expiry': m['expiry'], 'dte': round(m['T'] * 365),
                                      'iv': [round(surface.vol(m['F'] * math.exp(k), m['T']) * 100, 2) for k in ks]}
                                     for m in meta]}
                return curve, surf
        except Exception as e:
            err = str(e)[:120]
        time.sleep(4)
    return [{'error': err}], {'moneyness_pct': [], 'expiries': []}


def _print(summary, by_greek, result):
    print("\n=== VRP backtest: delta-hedged short ATM straddle, greek-attributed ===")
    for name in ('dev', 'holdout', 'full'):
        s = summary[name]
        if s:
            print(f"{name:8s}  annP&L ${s['ann_pnl']:>10,.0f}  Sharpe {s['sharpe']:+.2f}  "
                  f"NW-t {s['nw_t']:+.2f}  maxDD ${s['max_dd']:>11,.0f}  +H1 {s['pos_h1']} +H2 {s['pos_h2']}")
    print("\ncumulative P&L by greek (gross):")
    for k in ('theta', 'gamma', 'vega', 'vanna', 'volga', 'residual'):
        print(f"  {k:9s} ${by_greek[k]:>12,.0f}")
    print(f"  {'costs':9s} ${by_greek['costs']:>12,.0f}\n  {'NET':9s} ${by_greek['net']:>12,.0f}")
    print(f"  theta+gamma (VRP core) = ${by_greek['theta'] + by_greek['gamma']:>,.0f}")
    print(f"\ntrades recorded: {len(result['trades'])}  |  book held now: {result['book'].get('held')}"
          f"  |  curve rows: {len(result['curve'])}")


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else None)
