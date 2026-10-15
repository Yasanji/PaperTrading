"""Paper 2, SSRN extensions (15 Oct 2026). All exploratory: run after the primary results and the audit.
A volatility controls and interaction; B five markets by period; C equity and bond legs, simple strategy;
D HMM-style spillover (US signals only); E exclusions matched to HMM. Writes a4_step4_results.csv."""
import numpy as np, pandas as pd, statsmodels.api as sm
import a4_step3_battery as B
R = B.raw(); S = B.build(R); MAIN = B.MAIN; NEW = ['CA', 'AU']; ALL = ['US', 'UK', 'DE', 'CA', 'AU']
vix = pd.read_csv('ext_vix.csv', parse_dates=['observation_date']).set_index('observation_date').VIXCLS.astype(float) / 100
rows = []; add = lambda **k: rows.append(k)
for m in S:
    d = S[m]; rv = d.re.rolling(22).std() * np.sqrt(252); d['rv'] = rv
    d['vix'] = vix.reindex(d.index.union(vix.index)).ffill().reindex(d.index).shift(1 if m != 'US' else 0)
    q = rv.rolling(756, min_periods=252).quantile(0.8); d['hv'] = (rv > q).astype(float).where(q.notna())
    S[m] = d
def pooled(a, b, mk=NEW, **kw):
    z = B.stack(S, mk, a, b, **kw); return B.ols_cluster(z)
# A. volatility
r = pooled(*MAIN, extra=('rv', 'vix')); add(block='A vol controls', test='pooled + RV, VIX', signal='thr', coef=r.params['thr'], t=r.tvalues['thr'])
add(block='A vol controls', test='pooled + RV, VIX', signal='calw4', coef=r.params['calw4'], t=r.tvalues['calw4'])
r = pooled(*MAIN, extra=('rv', 'vix', 'hv'), inter='hv')
for k in ('thr', 'calw4'):
    add(block='A vol interaction', test='low-vol days (base)', signal=k, coef=r.params[k], t=r.tvalues[k])
    add(block='A vol interaction', test='extra on high-vol days', signal=k, coef=r.params[f'{k}_hv'], t=r.tvalues[f'{k}_hv'])
for m in ALL:
    d = S[m].loc[MAIN[0]:MAIN[1]]; X = B.cols(m) + ['rv', 'vix', 'hv']; d = d.dropna(subset=X).copy(); d['thr_hv'] = d.thr * d.hv
    rr, _ = B.fit(d, 'y_next', X + ['thr_hv']); add(block='A vol interaction', test=m, signal='thr base / extra high-vol', coef=rr.params['thr'], t=rr.tvalues['thr'], coef2=rr.params['thr_hv'], t2=rr.tvalues['thr_hv'])
# B. five markets by period
P = {'1999-2008': ('1999-01-01', '2008-12-31'), '2009-2019': ('2009-01-01', '2019-12-31'), '2020-Mar 2023': ('2020-01-01', '2023-03-17'),
     'Mar 2023-Sep 2026': ('2023-03-20', '2026-09-30')}
for m in ALL:
    for lab, (a, b) in P.items():
        try:
            rr, dd = B.fit(S[m].loc[a:b], 'y_next', B.cols(m)); add(block='B by period', test=m, period=lab, signal='thr', coef=rr.params['thr'], t=rr.tvalues['thr'], n=len(dd))
        except Exception as e: add(block='B by period', test=m, period=lab, signal='thr', note=str(e)[:60])
    d = S[m].loc['1999-01-01':'2026-09-30']; d = d[(d.index < '2020-01-01') | (d.index > '2023-03-17')]
    rr, dd = B.fit(d, 'y_next', B.cols(m)); add(block='B by period', test=m, period='1999-Sep 2026 ex 2020-Mar 2023', signal='thr', coef=rr.params['thr'], t=rr.tvalues['thr'], n=len(dd))
    d = S[m].loc[MAIN[0]:MAIN[1]]; ex = ((d.index >= '2008-09-01') & (d.index <= '2009-03-31')) | ((d.index >= '2020-03-01') & (d.index <= '2020-03-31'))
    rr, dd = B.fit(d[~ex], 'y_next', B.cols(m)); add(block='E HMM exclusion', test=m, period='main ex Sep08-Mar09, Mar20', signal='thr', coef=rr.params['thr'], t=rr.tvalues['thr'], n=len(dd))
# C. legs and strategy
for y in ('re_next', 'rb_next'):
    r = pooled(*MAIN, y=y)
    for k in ('thr', 'calw4'): add(block='C legs', test=f'pooled {y}', signal=k, coef=r.params[k], t=r.tvalues[k])
def strat(d, cost=0.0001):
    pos = -np.sign(d.thr); pnl = pos * d.y_next - cost * 2 * pos.diff().abs().fillna(0) / 2
    return pnl.mean() * 252 / (pnl.std() * np.sqrt(252)), pnl.mean() * 252 * 100
for m in ALL:
    d = S[m].loc[MAIN[0]:MAIN[1]].dropna(subset=['thr', 'y_next']); ex = ((d.index >= '2008-09-01') & (d.index <= '2009-03-31')) | ((d.index >= '2020-03-01') & (d.index <= '2020-03-31'))
    for lab, dd in (('main', d), ('main ex crises', d[~ex]), ('Mar 2023-Sep 2026', S[m].loc['2023-03-20':'2026-09-30'].dropna(subset=['thr', 'y_next']))):
        for c in (0, 0.0001):
            sr, ar = strat(dd, c); add(block='C strategy', test=m, period=lab, signal=f'cost {c*1e4:.0f}bp/leg', coef=sr, t=ar, note='coef=Sharpe, t=annual return %')
# D. HMM spillover: US signals only
for m in ['UK', 'DE', 'CA', 'AU']:
    d = S[m].loc[MAIN[0]:MAIN[1]]
    for y, lab in (('y_next', 'equity-minus-bond'), ('re_next', 'equity')):
        rr, dd = B.fit(d, y, ['us_thr', 'us_calw4', 'spx1', 'spx2'])
        for k in ('us_thr', 'us_calw4'): add(block='D spillover', test=m, period=lab, signal=k, coef=rr.params[k], t=rr.tvalues[k], n=len(dd))
out = pd.DataFrame(rows); out.to_csv('a4_step4_results.csv', index=False); pd.set_option('display.width', 200); print(out.round(3).to_string())
