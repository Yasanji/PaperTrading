"""Pre-registered contrarian test (positioning working notes, then numbered Part 4, recorded 29 Sep 2026).
Short when speculators' net share of open interest rose over the week, long when it fell; held one week.
Six markets, 10% vol each, equal weight, 1bp per trade. Main: Friday close after publication; also Monday close.
Test period 2010-2018 (2009 warm-up). 2019-2026 reported separately as already seen. Pass: positive and t > 2 in 2010-2018."""
import pandas as pd, numpy as np, pickle
D = pickle.load(open('pit_data.pkl', 'rb')); cot, px = D['cot'], D['px'].ffill()
r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252); days = px.index
COST, TARGET = 1e-4, 0.10
def nxt(t): i = days.searchsorted(t); return days[i] if i < len(days) else None
def run(lag_days):
    rows = []
    for m, net in cot.items():
        sig = -np.sign(net.diff()).dropna()                                    # contrarian
        ent = [nxt(a + pd.Timedelta(days=lag_days)) for a in sig.index]
        keep = [i for i, e in enumerate(ent) if e is not None]
        s = pd.Series(sig.values[keep], index=pd.DatetimeIndex([ent[i] for i in keep])); s = s[~s.index.duplicated()]
        d = list(s.index); prev_w = 0.0
        for i in range(len(d) - 1):
            e, x = d[i], d[i + 1]; v = vol[m].loc[e]
            if not np.isfinite(v) or v <= 0: prev_w = 0.0; continue
            w = TARGET / v * s.iloc[i]; ret = px[m].loc[x] / px[m].loc[e] - 1
            rows.append(dict(market=m, entry=e, gross=w * ret, turn=abs(w - prev_w))); prev_w = w
    t = pd.DataFrame(rows); t['net'] = t.gross - t.turn * COST
    return t
def stats(t, a, b):
    t = t[(t.entry >= a) & (t.entry <= b)]
    wk = t.groupby(t.entry.dt.to_period('W'))['net'].sum() / 6
    yrs = len(wk) / 52
    return dict(ret_pct=wk.mean() * 52 * 100, vol_pct=wk.std() * np.sqrt(52) * 100, sharpe=wk.mean() / wk.std() * np.sqrt(52),
                t=wk.mean() / wk.std() * np.sqrt(len(wk)), weeks=len(wk),
                breakeven_bps=t.gross.sum() / t.turn.sum() * 1e4,
                **{f'{m}_pct': t[t.market == m].net.sum() / 6 / yrs * 100 for m in cot}), wk
out, weekly = {}, {}
for name, lag in [('Friday close (main)', 3), ('Monday close', 6)]:
    t = run(lag)
    for per, a, b in [('2010-2018 TEST', '2010-01-01', '2018-12-31'), ('2019-2026 seen', '2019-01-01', '2026-12-31')]:
        s, wk = stats(t, a, b); out[f'{name} | {per}'] = s; weekly[f'{name} | {per}'] = wk
T = pd.DataFrame(out); pd.set_option('display.width', 250); print(T.round(2).to_string())
m = out['Friday close (main) | 2010-2018 TEST']
print('\nPRE-REGISTERED PASS MARK (Friday, 2010-2018: positive and t > 2):', 'PASS' if (m['ret_pct'] > 0 and m['t'] > 2) else 'FAIL', f"(return {m['ret_pct']:.2f}%, t {m['t']:.2f})")
pickle.dump(dict(T=T, weekly=weekly), open('pit_contra_results.pkl', 'wb'))
