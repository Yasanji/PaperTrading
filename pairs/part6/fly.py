"""Part 5 pre-registered test (fixed 1 Oct 2026). Stage 1: synthetic BFLY vs Cboe BFLY. Stage 2: weekly GLD short iron butterfly."""
import pandas as pd, numpy as np, yfinance as yf, pickle, warnings; warnings.filterwarnings('ignore')
from scipy.stats import norm
def bs(S, K, T, v, call):
    d1 = (np.log(S / K) + 0.5 * v * v * T) / (v * np.sqrt(T)); d2 = d1 - v * np.sqrt(T)
    return S * norm.cdf(d1) - K * norm.cdf(d2) if call else K * norm.cdf(-d2) - S * norm.cdf(-d1)
WING, PUT_SKEW, CALL_SKEW = 0.05, 1.10, 0.95
def fly(S, T, iv):
    atm_c, atm_p = bs(S, S, T, iv, True), bs(S, S, T, iv, False)
    wc, wp = bs(S, S * (1 + WING), T, iv * CALL_SKEW, True), bs(S, S * (1 - WING), T, iv * PUT_SKEW, False)
    return atm_c + atm_p - wc - wp, atm_c + atm_p + wc + wp            # net credit, gross premium (for costs)
px = yf.download(['^GSPC', '^VIX', 'GLD', '^GVZ'], start='2008-01-01', end='2026-09-30', progress=False, auto_adjust=False)['Close'].ffill()
# ---- Stage 1: monthly, third-Friday expiries
days = px.index
def third_fridays():
    out = []
    for y in range(2009, 2027):
        for m in range(1, 13):
            d = pd.Timestamp(y, m, 15); d += pd.Timedelta(days=(4 - d.weekday()) % 7)        # third Friday
            i = days.searchsorted(d); 
            if i < len(days) and days[i] <= pd.Timestamp('2026-09-29'):
                j = i if days[i] == d else i - 1                                              # holiday: previous trading day
                out.append(days[j])
    return sorted(set(out))
tf = third_fridays(); rows = []
for a, b in zip(tf[:-1], tf[1:]):
    S, ST, iv = px['^GSPC'].loc[a], px['^GSPC'].loc[b], px['^VIX'].loc[a] / 100; T = (b - a).days / 365
    credit, _ = fly(S, T, iv); loss = min(abs(ST - S), WING * S)
    rows.append(dict(date=b, ours=(credit - loss) / S))
s1 = pd.DataFrame(rows).set_index('date')
bf = pd.read_csv('bfly.csv'); bf['DATE'] = pd.to_datetime(bf['DATE']); bf = bf.set_index('DATE')['BFLY']
bfm = bf.reindex(pd.DatetimeIndex(tf), method='ffill').pct_change().reindex(s1.index)
s1['bfly'] = bfm; s1 = s1.dropna(); corr = s1.ours.corr(s1.bfly)
print(f'STAGE 1: {len(s1)} months 2009-2026 | correlation with Cboe BFLY = {corr:.2f} | pass mark 0.80 -> {"PASS" if corr >= 0.8 else "FAIL"}')
print(f'   annual: ours {s1.ours.mean()*12*100:.2f}% of notional, BFLY {s1.bfly.mean()*12*100:.2f}% (BFLY includes cash interest)')
# ---- Stage 2: weekly GLD
COST, RISK = 0.02, 0.005
fr = [d for d in days if d.weekday() == 4 and pd.Timestamp('2010-01-01') <= d]
trades = []
for d in fr:
    i = days.get_loc(d)
    if i + 20 >= len(days): break
    e = days[i + 20]                                                                         # about one month (20 trading days)
    S, ST, iv = px['GLD'].loc[d], px['GLD'].loc[e], px['^GVZ'].loc[d] / 100
    if not np.isfinite(iv): continue
    T = (e - d).days / 365; credit, gross = fly(S, T, iv); cost = COST * gross
    maxloss = WING * S - credit + cost; n = RISK / (maxloss / S)                              # notional multiple for 0.5% worst case
    pnl = n * (credit - cost - min(abs(ST - S), WING * S)) / S
    trades.append(dict(entry=d, expiry=e, credit_pct=credit / S * 100, cost_pct=cost / S * 100, pnl=pnl, maxloss_hit=abs(ST - S) >= WING * S, iv=iv))
t = pd.DataFrame(trades)
wk = t.groupby(t.expiry.dt.to_period('W')).pnl.sum(); wk.index = wk.index.to_timestamp()
def st(w):
    a = w.mean() * 52; v = w.std() * np.sqrt(52); return a * 100, v * 100, a / v, w.mean() / w.std() * np.sqrt(len(w))
res = {}
for name, w in [('2010-2026', wk), ('2010-2017', wk[wk.index < '2018-01-01']), ('2018-2026', wk[wk.index >= '2018-01-01'])]:
    r, v, sh, tt = st(w); res[name] = dict(return_pct=r, vol_pct=v, sharpe=sh, t=tt, weeks=len(w))
R = pd.DataFrame(res).T; print('\nSTAGE 2 (GLD weekly short iron butterfly):'); print(R.round(2).to_string())
cum = wk.cumsum(); dd = (cum - cum.cummax()).min() * 100; mon = wk.resample('ME').sum()
print(f'   worst drawdown {dd:.2f}% | worst month {mon.min()*100:.2f}% | max-loss hit {t.maxloss_hit.mean()*100:.0f}% of {len(t)} trades')
print(f'   average credit {t.credit_pct.mean():.2f}% of GLD, average cost {t.cost_pct.mean():.2f}% (cost / credit {t.cost_pct.mean()/t.credit_pct.mean()*100:.0f}%)')
ok = res['2010-2026']['return_pct'] > 0 and res['2010-2026']['t'] > 2 and res['2010-2017']['return_pct'] > 0 and res['2018-2026']['return_pct'] > 0
print('PRE-REGISTERED PASS MARK (positive, t > 2, positive in both halves):', 'PASS' if ok else 'FAIL')
pickle.dump(dict(s1=s1, corr=corr, t=t, wk=wk, R=R), open('fly_results.pkl', 'wb'))
