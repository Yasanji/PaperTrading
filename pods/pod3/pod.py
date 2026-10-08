"""Pod 3: index events. Turns committed review predictions into target positions, under POD3_PREREGISTRATION.md s.4.

  Entry:  close 15 trading days before the effective date. Long predicted additions, short predicted deletions.
  Exit:   close on the effective date. A prediction missing from the official announcement is closed at the next close.
  Size:   10% of the pod's allocated capital each, at most 20; ranked by rule margin (furthest past the threshold first).
  Hedge:  net beta exposure (252-day beta to the STOXX Europe 600) with STOXX Europe 600 futures, whole contracts only.
  Scale:  the pod trades at 25% of its target risk while in its forward test (portfolio pre-registration s.2).

Pod interface (DESIGN.md s.3): targets(as_of), status(), checks().
Usage (dry run): python pod.py 2026-11-26 [NAV]"""
import os, sys, datetime as dt, numpy as np, pandas as pd, yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
NAV = 1_000_000; N_PODS = 6; FORWARD_SCALE = 0.25; POS_SHARE = 0.10; MAX_POS = 20; ENTRY_LAG = 15
HEDGE = dict(symbol='DJ600', yahoo='^STOXX', multiplier=50, currency='EUR')
HOLIDAYS = ['2026-12-24', '2026-12-25', '2026-12-31', '2027-01-01', '2027-04-02', '2027-04-05']   # Eurex closures used for counting


def tdays(a, b):
    return pd.bdate_range(a, b, freq='C', holidays=HOLIDAYS)


def entry_date(effective):
    d = tdays(pd.Timestamp(effective) - pd.Timedelta(days=40), effective)
    return d[d < pd.Timestamp(effective)][-ENTRY_LAG]


def load_predictions(r):
    f = os.path.join(HERE, r.prediction_file)
    if os.environ.get('POD3_PRELIMINARY'):                    # dry runs only: use the latest preliminary list
        import glob
        g = sorted(glob.glob(os.path.join(os.path.dirname(f), 'prediction_preliminary_*.csv')))
        f = g[-1] if g else f
    if not os.path.exists(f): return None
    p = pd.read_csv(f)
    p = p[p['call'].isin(['ADD', 'DELETE'])].copy()
    p['side'] = np.where(p['call'] == 'ADD', 1, -1)
    for i in p.index[p.symbol.isna()]:                        # look up a missing Yahoo symbol by ISIN
        q = yf.Search(str(p.at[i, 'isin']), max_results=1).quotes
        p.at[i, 'symbol'] = q[0]['symbol'] if q else None
    p = p.dropna(subset=['symbol'])
    # rule margin: how far past the threshold, comparable across both indexes
    if 'ratio' in p:  # MSCI: additions ratio >= 0.97, deletions ratio < 1.05
        p['margin'] = np.where(p.side == 1, p.ratio - 0.97, 1.05 - p.ratio)
    else:             # STOXX: rank inside 550 for additions, outside the selected 600 for deletions
        p['margin'] = np.where(p.side == 1, 550 - p['rank'], p['rank'] - 600)
    return p.sort_values(['margin', 'symbol'], ascending=[False, True]).head(MAX_POS)


def allocated_capital(nav=NAV):
    return nav / N_PODS


def targets(as_of, nav=NAV):
    """Target notional (USD, signed) per instrument after the close on as_of."""
    as_of = pd.Timestamp(as_of); out = []
    for _, r in pd.read_csv(os.path.join(HERE, 'reviews.csv')).iterrows():
        eff = pd.Timestamp(r.effective_date); ent = entry_date(eff)
        if not (ent <= as_of < eff): continue
        p = load_predictions(r)
        if p is None: continue
        af = os.path.join(HERE, r.actual_file)
        if as_of > pd.Timestamp(r.announce_date) and os.path.exists(af):        # wrong calls closed after the announcement
            a = pd.read_csv(af); key = lambda s: str(s).upper().split()[0]
            ok = {(key(n), c) for n, c in zip(a['name'], a['change'])}
            p = p[[(key(n), c) in ok for n, c in zip(p['name'], p['call'])]]
        size = POS_SHARE * allocated_capital(nav) * FORWARD_SCALE
        for _, x in p.iterrows():
            out.append(dict(review=r.review, symbol=x.symbol, name=x['name'], side=int(x.side), notional_usd=x.side * size,
                            margin=float(x.margin), entry=ent.date(), exit=eff.date()))
    return pd.DataFrame(out)


def hedge(t):
    """Whole STOXX 600 futures contracts against the net beta-weighted notional."""
    if t.empty: return 0, 0.0, {}
    px = yf.download(list(t.symbol) + [HEDGE['yahoo'], 'EURUSD=X'], period='14mo', progress=False, auto_adjust=True)['Close'].ffill()
    r = px.pct_change().iloc[-252:]
    beta = {s: float(r[s].cov(r[HEDGE['yahoo']]) / r[HEDGE['yahoo']].var()) for s in t.symbol}
    net = float(sum(beta[s] * n for s, n in zip(t.symbol, t.notional_usd)))
    per_contract = float(px[HEDGE['yahoo']].iloc[-1] * HEDGE['multiplier'] * px['EURUSD=X'].iloc[-1])
    return int(round(-net / per_contract)), net, beta


def status():
    return dict(pod=3, stage='forward test', scale=FORWARD_SCALE)


def checks(as_of):
    """Inputs that would stop the pod trading on as_of."""
    as_of = pd.Timestamp(as_of); problems = []
    for _, r in pd.read_csv(os.path.join(HERE, 'reviews.csv')).iterrows():
        if entry_date(r.effective_date) <= as_of < pd.Timestamp(r.effective_date):
            if not os.path.exists(os.path.join(HERE, r.prediction_file)):
                problems.append(f'{r.review}: no committed prediction file ({r.prediction_file})')
    return problems


if __name__ == '__main__':
    as_of = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().isoformat()
    nav = float(sys.argv[2]) if len(sys.argv) > 2 else NAV
    for _, r in pd.read_csv(os.path.join(HERE, 'reviews.csv')).iterrows():
        print(f'{r.review}: entry {entry_date(r.effective_date).date()}, announcement {r.announce_date}, exit {r.effective_date}')
    print('checks:', checks(as_of) or 'none')
    t = targets(as_of, nav)
    print(f'\nDRY RUN targets after the close on {as_of} (allocated capital ${allocated_capital(nav):,.0f}, forward-test scale {FORWARD_SCALE:.0%}):')
    if t.empty: print('no positions')
    else:
        print(t[['review', 'name', 'symbol', 'side', 'notional_usd', 'margin', 'exit']].round(1).to_string(index=False))
        n, net, beta = hedge(t)
        print(f'net beta-weighted notional ${net:,.0f} -> {HEDGE["symbol"]} contracts: {n}')
