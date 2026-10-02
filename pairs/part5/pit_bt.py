import pandas as pd, numpy as np, pickle
D = pickle.load(open('pit_data.pkl', 'rb')); cot, px = D['cot'], D['px'].ffill()
r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252); days = px.index
COST = 1e-4; TARGET = 0.10   # 10% vol per market, equal risk
def first_on_or_after(t): i = days.searchsorted(t); return days[i] if i < len(days) else None
def run(lag_days):
    rows = []
    for m, net in cot.items():
        chg = np.sign(net.diff()).dropna()
        ent = [first_on_or_after(a + pd.Timedelta(days=lag_days)) for a in chg.index]
        keep = [i for i, e in enumerate(ent) if e is not None]
        s = pd.Series(chg.values[keep], index=pd.DatetimeIndex([ent[i] for i in keep])); s = s[~s.index.duplicated()]
        dates = list(s.index)
        for i in range(len(dates) - 1):
            e, x = dates[i], dates[i + 1]
            v = vol[m].loc[e]
            if not np.isfinite(v) or v <= 0: continue
            w = TARGET / v * s.iloc[i]
            prev = TARGET / vol[m].loc[dates[i - 1]] * s.iloc[i - 1] if i and np.isfinite(vol[m].loc[dates[i - 1]]) else 0.0
            ret = px[m].loc[x] / px[m].loc[e] - 1
            rows.append(dict(market=m, entry=e, exit=x, pnl=w * ret - abs(w - prev) * COST))
    t = pd.DataFrame(rows); t = t[t.entry >= '2019-01-01']
    wk = t.groupby(t.entry.dt.to_period('W'))['pnl'].mean()        # equal weight across markets each week
    return t, wk
out = {}
for name, lag in [('Tuesday (hindsight)', 0), ('Friday close (earliest possible)', 3), ('Monday close (cautious)', 6)]:
    t, wk = run(lag); ann = wk.mean() * 52; vo = wk.std() * np.sqrt(52)
    out[name] = dict(ret_pct=ann * 100, vol_pct=vo * 100, sharpe=ann / vo, t=wk.mean() / wk.std() * np.sqrt(len(wk)), weeks=len(wk),
                     **{f'{m}_pct': t[t.market == m].pnl.sum() / (len(wk) / 52) * 100 / 6 for m in cot})
    out[name]['_wk'] = wk
T = pd.DataFrame({k: {kk: vv for kk, vv in v.items() if kk != '_wk'} for k, v in out.items()})
print(T.round(2).to_string())
pickle.dump(out, open('pit_results.pkl', 'wb'))
