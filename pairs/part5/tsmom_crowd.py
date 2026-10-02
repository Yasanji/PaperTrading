"""Pre-registered test (positioning notes, then numbered Part 4, fixed 1 Oct 2026): does crowding hurt trend following?
Trend: sign of past 12-month return, 10% vol per market, weekly, 1bp. Crowded: speculators' net share of open interest
more than 1.5 sd from its previous three years (156 weeks), in the trend's direction, used from Friday publication.
Outcome: four-week returns of crowded vs uncrowded trend positions (overlapping cohorts). Period Jan 2010 - Sep 2026.
Pass: crowded earns less, t < -2 over the whole period, same sign in 2010-2017 and 2018-2026."""
import pandas as pd, numpy as np, pickle
D = pickle.load(open('tsmom_data.pkl', 'rb')); cot, px = D['cot'], D['px'].ffill()
days = px.index; r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252)
TARGET, COST, Z, WIN, H = 0.10, 1e-4, 1.5, 156, 4
def nxt(t): i = days.searchsorted(t); return days[i] if i < len(days) else None
rows = []
for m, net in cot.items():
    mu = net.shift(1).rolling(WIN).mean(); sd = net.shift(1).rolling(WIN).std(); z = (net - mu) / sd   # previous 3 years only
    for a in net.index:
        e = nxt(a + pd.Timedelta(days=3))                                     # Friday close after publication
        if e is None or not np.isfinite(z.loc[a]): continue
        i = days.get_loc(e)
        if i < 252: continue
        trend = np.sign(px[m].iloc[i] / px[m].iloc[i - 252] - 1); v = vol[m].iloc[i]
        if trend == 0 or not np.isfinite(v) or v <= 0: continue
        rows.append(dict(market=m, entry=e, trend=trend, w=TARGET / v * trend, crowded=bool(z.loc[a] * trend > Z), z=z.loc[a]))
P = pd.DataFrame(rows).sort_values(['market', 'entry']).reset_index(drop=True)
P['exit'] = P.groupby('market').entry.shift(-1); P = P.dropna(subset=['exit'])
P['ret'] = [px[m].loc[x] / px[m].loc[e] - 1 for m, e, x in zip(P.market, P.entry, P.exit)]
P['pnl'] = P.w * P.ret
P['turn'] = P.groupby('market').w.diff().abs().fillna(P.w.abs()); P['net'] = P.pnl - P.turn * COST
P = P[P.entry >= '2010-01-01']
# overlapping four-week cohorts: a position flagged at week t contributes its next four weekly returns to its group
P['wk'] = P.entry.dt.to_period('W'); weeks = sorted(P.wk.unique()); widx = {w: i for i, w in enumerate(weeks)}
P['wi'] = P.wk.map(widx)
fwd = {}
for m, g in P.groupby('market'):
    g = g.set_index('wi').sort_index()
    for wi, row in g.iterrows():
        for k in range(H):
            j = wi + k
            if j in g.index: fwd.setdefault((j, row.crowded), []).append(row.trend * TARGET / abs(row.w) * row.trend * 0 + g.loc[j, 'pnl'] * np.sign(g.loc[j, 'w']) * row.trend)
crowd = pd.Series({j: np.mean(v) for (j, c), v in fwd.items() if c}).sort_index()
unc = pd.Series({j: np.mean(v) for (j, c), v in fwd.items() if not c}).sort_index()
diff = (crowd - unc).dropna()
def tstat(s): return s.mean() / s.std() * np.sqrt(len(s))
cut = widx[min(w for w in weeks if w.start_time >= pd.Timestamp('2018-01-01'))]
res = {}
for name, s in [('All 2010-2026', diff), ('2010-2017', diff[diff.index < cut]), ('2018-2026', diff[diff.index >= cut])]:
    res[name] = dict(crowded_minus_uncrowded_pct_yr=s.mean() * 52 * 100, t=tstat(s), weeks=len(s))
R = pd.DataFrame(res).T; print(R.round(2).to_string())
print(f"\nShare of position-weeks flagged crowded: {P.crowded.mean() * 100:.1f}%  ({P.crowded.sum()} of {len(P)})")
print('by market (% crowded):', (P.groupby('market').crowded.mean() * 100).round(0).to_dict())
wk = P.groupby('wk').net.sum() / len(cot); a = wk.mean() * 52; s = wk.std() * np.sqrt(52)
print(f"\nTrend model alone, 2010-2026: {a * 100:.2f}% a year, vol {s * 100:.2f}%, Sharpe {a / s:.2f}, t {tstat(wk):.2f}")
cr = P[P.crowded].pnl.mean() * 52 * 100; un = P[~P.crowded].pnl.mean() * 52 * 100
print(f"Average one-week trend return per position (annualised): crowded {cr:.2f}%, uncrowded {un:.2f}%")
a_ = res['All 2010-2026']; h1, h2 = res['2010-2017'], res['2018-2026']
ok = a_['t'] < -2 and np.sign(h1['crowded_minus_uncrowded_pct_yr']) == np.sign(h2['crowded_minus_uncrowded_pct_yr']) == -1
print('\nPRE-REGISTERED PASS MARK (t < -2 overall, negative in both halves):', 'PASS' if ok else 'FAIL')
pickle.dump(dict(R=R, P=P, diff=diff, crowd=crowd, unc=unc, wk=wk), open('tsmom_crowd_results.pkl', 'wb'))
