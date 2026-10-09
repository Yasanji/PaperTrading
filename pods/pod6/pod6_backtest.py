"""Pod 6 backtest, rules of POD6_PREREGISTRATION.md s.3. Usage: python pod6_backtest.py dev | holdout
Allocated capital: NAV x risk share = 1,000,000 / 6. Mini VIX multiplier 100. Daily return = P&L / allocated capital."""
import sys, numpy as np, pandas as pd, statsmodels.api as sm
CAP, MULT, COMM, SLIP = 1_000_000 / 6, 100, 1.50, 0.05
v = pd.read_csv('vx_settles.csv', parse_dates=['date', 'expiry']).drop_duplicates(['date', 'expiry'])
S = v.pivot_table(index='date', columns='expiry', values='settle')
ix = pd.read_csv('index.csv', index_col=0, parse_dates=True).dropna()
days = S.index.intersection(ix.index); S = S.loc[days]; ix = ix.loc[days]
rv = np.log(ix.spx).diff().rolling(21).std() * np.sqrt(252) * 100
expiries = sorted(S.columns)
def front(d): return next(e for e in expiries if e > d)
pnl = pd.Series(0.0, index=days); log = []
pos = None                                                     # dict(expiry, n, entry, stopped)
for i, d in enumerate(days[:-1]):
    nxt = days[i + 1]
    if pos is None:
        prev = days[i - 1] if i else None
        if prev is not None and any(prev <= e < d for e in expiries):        # d = first trading day after an expiry
            e = front(d); F = S.at[d, e]
            if np.isfinite(F) and F >= 1.05 * ix.vix[d] and ix.vix[d] > rv[d]:
                n = int(0.03 * CAP // (F * MULT))
                if n > 0:
                    pos = dict(expiry=e, n=n, entry=F, stop=False); pnl[d] -= n * (COMM + SLIP * MULT)
                    log.append(dict(entry=d, expiry=e, n=n, F=F, vix=ix.vix[d], rv=rv[d]))
            continue
    if pos is not None:
        e = pos['expiry']; F0, F1 = S.at[d, e], S.at[nxt, e]
        pnl[nxt] += -pos['n'] * MULT * (F1 - F0)
        tdays_left = ((days > nxt) & (days < e)).sum()                       # trading days after nxt before expiry
        exit_ = tdays_left < 3 or pos['stop']
        if not exit_ and F1 >= 1.25 * pos['entry']: pos['stop'] = True        # closed at the next close
        if exit_:
            pnl[nxt] -= pos['n'] * (COMM + SLIP * MULT); log[-1].update(exit=nxt, stopped=pos['stop']); pos = None
r = pnl / CAP
def stats(x):
    m = sm.OLS(x.values, np.ones(len(x))).fit(cov_type='HAC', cov_kwds={'maxlags': 10})
    return dict(ann_return=x.mean() * 252, ann_vol=x.std() * np.sqrt(252), sharpe=x.mean() / x.std() * np.sqrt(252), t_nw=m.tvalues[0])
P = {'dev': [('2006-01-01', '2015-12-31'), ('2006-01-01', '2010-12-31'), ('2011-01-01', '2015-12-31')],
     'holdout': [('2016-01-01', '2026-09-30'), ('2016-01-01', '2020-12-31'), ('2021-01-01', '2026-09-30')]}[sys.argv[1]]
out = pd.DataFrame({f'{a[:4]}-{b[:4]}': stats(r[a:b]) for a, b in P}).T.round(4); print(out)
L = pd.DataFrame(log); L = L[(L.entry >= P[0][0]) & (L.entry <= P[0][1])]
print(f"\ntrades {len(L)}, stopped {int(L.stopped.sum())}, months flat {sum(1 for _ in range(0))}")
r.to_csv(f'pod6_daily_{sys.argv[1]}.csv'); L.to_csv(f'pod6_trades_{sys.argv[1]}.csv', index=False)
