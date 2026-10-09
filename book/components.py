"""Daily return series of the book's tested sleeves, for diversification tests of new pods.
trend(): rules of pairs/part4/trend_dev.py as coded in carry/sleeveA/sleeveA_diversification.py (15 futures, weekly
signal, 10% vol per market, scaled to 5%). carry(): rules of carry/sleeveA (G10 carry, month-end, scaled to 5%), as
coded in sleeveA_holdout.py without the 2026 SONIA splice. Both need carry/sleeveA/boe_fx.pkl and oecd_rates.pkl."""
import os, numpy as np, pandas as pd, yfinance as yf
A = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'carry', 'sleeveA')

def trend(start='2004-01-01', end='2016-01-10'):
    tick = ['ES=F', 'NQ=F', 'ZT=F', 'ZN=F', 'ZB=F', 'CL=F', 'NG=F', 'GC=F', 'SI=F', 'HG=F', '6E=F', '6J=F', '6B=F', '6A=F', '6C=F']
    px = yf.download(tick, start=start, end=end, progress=False, auto_adjust=True)['Close'].ffill(); days = px.index
    r = px.pct_change(); vol = r.rolling(63).std() * np.sqrt(252); W = {}
    for d in [d for d in days if d.weekday() == 4]:
        i = days.get_loc(d)
        if i + 1 >= len(days) or i < 252: continue
        W[days[i + 1]] = (0.10 / vol.iloc[i] * np.sign(px.iloc[i] / px.iloc[i - 252] - 1) / px.shape[1]).fillna(0)
    Wd = pd.DataFrame(W).T.reindex(days).ffill().fillna(0)[min(W):]; R = r.reindex(Wd.index).fillna(0)
    x = (Wd.shift(1) * R).sum(axis=1) - Wd.diff().abs().sum(axis=1) * 1e-4
    sv = x.rolling(126).std() * np.sqrt(252); sc = pd.Series(np.nan, index=x.index)
    for d in [d for d in x.index if d.weekday() == 4]:
        i = x.index.get_loc(d)
        if i + 1 < len(x) and np.isfinite(sv.iloc[i]) and sv.iloc[i] > 0: sc.iloc[i + 1] = 0.05 / sv.iloc[i]
    return (x * sc.ffill().shift(1)).dropna()

def carry(start='2004-06', end='2015-12'):
    fx = pd.read_pickle(f'{A}/boe_fx.pkl').set_index('DATE').sort_index()
    gbp = {'USD': 'XUDLUSS', 'EUR': 'XUDLERS', 'JPY': 'XUDLJYS', 'CHF': 'XUDLSFS', 'CAD': 'XUDLCDS', 'AUD': 'XUDLADS', 'NZD': 'XUDLNDS', 'SEK': 'XUDLSKS', 'NOK': 'XUDLNKS'}
    f = fx[list(gbp.values())].apply(pd.to_numeric, errors='coerce').dropna(subset=['XUDLUSS'])
    usd = pd.DataFrame({k: f['XUDLUSS'] / f[v] for k, v in gbp.items() if k != 'USD'})
    o = pd.read_pickle(f'{A}/oecd_rates.pkl'); o = o[o.MEASURE == 'IR3TIB']
    area = {'USA': 'USD', 'EA20': 'EUR', 'JPN': 'JPY', 'GBR': 'GBP', 'CHE': 'CHF', 'CAN': 'CAD', 'AUS': 'AUD', 'NZL': 'NZD', 'SWE': 'SEK', 'NOR': 'NOK'}
    r = o[o.REF_AREA.isin(area)].pivot_table(index='TIME_PERIOD', columns='REF_AREA', values='OBS_VALUE').rename(columns=area) / 100
    r.index = pd.PeriodIndex(r.index, freq='M'); r = r.ffill(limit=1)
    CCY = list(usd.columns); d = usd.loc[start:end].dropna(how='all'); dret = d.pct_change()
    mend = d.groupby(d.index.to_period('M')).tail(1).index; prev = pd.Series(0.0, index=CCY); daily, cost = [], {}
    for i, t in enumerate(mend[:-1]):
        p = t.to_period('M'); carry = (r.loc[p - 1, CCY] - r.loc[p - 1, 'USD']).dropna()
        vol = dret.loc[:t].iloc[-63:][carry.index].std() * np.sqrt(252); carry = carry[vol.notna() & (vol > 0)]
        if len(carry) < 6: continue
        hi, lo = carry.nlargest(3).index, carry.nsmallest(3).index
        w = pd.Series(0.0, index=CCY); w[hi] = (1 / vol[hi]) / (1 / vol[hi]).sum(); w[lo] = -(1 / vol[lo]) / (1 / vol[lo]).sum()
        nxt = mend[i + 1]; hold = dret.loc[t:nxt].iloc[1:]; q = nxt.to_period('M'); diff = (r.loc[q, CCY] - r.loc[q, 'USD']).fillna(0)
        daily.append(hold[CCY].fillna(0).mul(w).sum(axis=1) + (w * diff).sum() / 252); cost[hold.index[0]] = 2e-4 * (w - prev).abs().sum(); prev = w
    raw = pd.concat(daily); raw.loc[list(cost)] -= pd.Series(cost)
    lev = (0.05 / (raw.rolling(126).std() * np.sqrt(252))).shift(1); lev = lev.groupby(lev.index.to_period('M')).transform('first')
    return (raw * lev).dropna()

def diversification(pod, start, end):
    """Sharpe of trend + carry at equal risk, with and without the pod at equal risk (each scaled by its own volatility)."""
    j = pd.concat([trend().rename('trend'), carry().rename('carry'), pod.rename('pod')], axis=1).dropna().loc[start:end]
    sh = lambda s: s.mean() / s.std() * np.sqrt(252); z = j / j.std()
    return dict(n=len(j), without=sh(z[['trend', 'carry']].mean(axis=1)), with_pod=sh(z.mean(axis=1)),
                corr=j.corr().round(2).to_dict(), sharpe_each={c: round(sh(j[c]), 2) for c in j})
