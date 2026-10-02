"""Statistics behind Sections 5.4, 6, 7 and 8 of the paper. Run after the signal tests, from the working directory used by them."""
import pickle, io, zipfile, requests, numpy as np, pandas as pd
from scipy.stats import norm, skew, kurtosis
rng = np.random.default_rng(1)
def load(f, c): return pickle.load(open(f, 'rb'))[c]
SIG = {'Futures trend': ('msb/trend_dev_results.pkl', 'xs'), 'Low volatility': ('msb/lowvol_results.pkl', 'vs'), 'Momentum': ('msb/mom_results.pkl', 'vs'),
       'Industry momentum': ('msb/indmom_results.pkl', 'vs'), 'Reversal': ('msb/rev_results.pkl', 'vs'), 'Pairs': ('msb/pairs_dev_results.pkl', 'xs'),
       'Short interest': ('msb/si_results.pkl', 'vs'), 'Value proxy (futures)': ('msb/value_fut_results.pkl', 'xs'),
       'Value proxy (equities)': ('msb/value_eq_results.pkl', 'vs'), 'Carry (currencies, bonds)': ('msb/carry_results.pkl', 'comb')}
D = {k: (load(*v)['2015':'2022'] if k == 'Value proxy (equities)' else load(*v)['2013':'2022']).dropna() for k, v in SIG.items()}
def nw_t(x, lags=10):
    x = np.asarray(x); d = x - x.mean(); n = len(x); s = d @ d / n
    for l in range(1, lags + 1): s += 2 * (1 - l / (lags + 1)) * (d[l:] @ d[:-l]) / n
    return x.mean() / np.sqrt(s / n)
# Section 6: deflated Sharpe ratio (Bailey and Lopez de Prado, 2014) and block-bootstrap intervals
sr = {k: v.mean() / v.std() for k, v in D.items()}; sd = np.std(list(sr.values()), ddof=1); g = 0.5772156649
def bench(N): return sd * ((1 - g) * norm.ppf(1 - 1 / N) + g * norm.ppf(1 - 1 / (N * np.e)))
def dsr(x, b):
    s = x.mean() / x.std(); return norm.cdf((s - b) * np.sqrt(len(x) - 1) / np.sqrt(1 - skew(x) * s + (kurtosis(x, fisher=False) - 1) / 4 * s ** 2))
rows = {}
for k, v in D.items():
    x = v.values; T = len(x); bs = []
    for _ in range(2000):
        idx = np.concatenate([np.arange(a, a + 21) for a in rng.integers(0, T - 21, T // 21)]); y = x[idx]; bs.append(y.mean() / y.std() * np.sqrt(252))
    rows[k] = dict(sharpe=sr[k] * np.sqrt(252), ci_lo=np.percentile(bs, 2.5), ci_hi=np.percentile(bs, 97.5), dsr_10=dsr(x, bench(10)), dsr_11=dsr(x, bench(11)), dsr_26=dsr(x, bench(26)))
print('Section 6: luck benchmark (annualised) N=10 %.2f, N=11 %.2f, N=26 %.2f' % tuple(bench(n) * np.sqrt(252) for n in (10, 11, 26)))
print(pd.DataFrame(rows).T.sort_values('sharpe', ascending=False).round(2).to_string())
# Section 6.2: power
print('\nSection 6.2: power of a t > 1.96 test'); print(pd.DataFrame({f'{y} years': {s: norm.cdf(s * np.sqrt(y) - 1.96) for s in (0.3, 0.5, 0.8, 1.0)} for y in (5, 8, 10)}).T.round(2).to_string())
# Section 4: Newey-West check
print('\nSection 4: plain vs Newey-West t'); [print(f'  {k:15s} {D[k].mean() / D[k].std() * np.sqrt(len(D[k])):.2f}  {nw_t(D[k].values):.2f}') for k in ('Futures trend', 'Low volatility', 'Momentum')]
# Section 6.3: White's Reality Check and Hansen's SPA, stationary bootstrap, nine long-short signals over 2013-2022
rng = np.random.default_rng(11)                                         # seed used for the paper's run
X = pd.DataFrame({k: v for k, v in D.items() if k != 'Value proxy (equities)'}).fillna(0.0).values; n, m = X.shape; mu = X.mean(0)
def sb():
    idx = np.empty(n, int); i = rng.integers(n)
    for t in range(n): idx[t] = i; i = rng.integers(n) if rng.random() < 1 / 21 else (i + 1) % n
    return idx
boot = np.array([X[sb()].mean(0) for _ in range(2000)]); om = np.sqrt(n) * boot.std(0); T0 = max((np.sqrt(n) * mu / om).max(), 0); thr = np.sqrt(2 * np.log(np.log(n)))
for name, c in [('Reality Check', mu), ('SPA (consistent)', mu * (np.sqrt(n) * mu / om >= -thr))]:
    print(f'Section 6.3: {name} p = {(np.maximum((np.sqrt(n) * (boot - c) / om).max(1), 0) >= T0).mean():.3f}')
# Section 5.4: European Fama-French five factors plus momentum
def ff(name):
    z = zipfile.ZipFile(io.BytesIO(requests.get(f'https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip', headers={'User-Agent': 'Mozilla/5.0'}, timeout=60).content))
    lines = z.read(z.namelist()[0]).decode('latin1').splitlines(); i0 = next(i for i, l in enumerate(lines) if l.startswith(','))
    rows_ = [l.split(',') for l in lines[i0 + 1:] if l.split(',')[0].strip().isdigit()]
    df = pd.DataFrame(rows_, columns=['date'] + [h.strip() for h in lines[i0].split(',')[1:len(rows_[0])]])
    df['date'] = pd.to_datetime(df.date.str.strip(), format='%Y%m%d'); return df.set_index('date').apply(pd.to_numeric, errors='coerce') / 100
F = ff('Europe_5_Factors_Daily').join(ff('Europe_Mom_Factor_Daily'), how='inner'); cols = ['Mkt-RF', 'SMB', 'HML', 'RMW', 'CMA', 'WML']
print('\nSection 5.4: alpha % a year (Newey-West t) after six European factors')
for k in ('Low volatility', 'Momentum', 'Industry momentum', 'Short interest', 'Value proxy (equities)', 'Reversal', 'Pairs'):
    d = pd.concat([D[k].rename('y'), F[cols]], axis=1, join='inner').dropna(); Xf = np.column_stack([np.ones(len(d)), d[cols].values]); y = d.y.values
    b = np.linalg.lstsq(Xf, y, rcond=None)[0]; e = y - Xf @ b; S = (Xf * e[:, None]).T @ (Xf * e[:, None]) / len(y)
    for l in range(1, 11): G = (Xf[l:] * e[l:, None]).T @ (Xf[:-l] * e[:-l, None]) / len(y); S += (1 - l / 11) * (G + G.T)
    Q = np.linalg.inv(Xf.T @ Xf / len(y)); se = np.sqrt(np.diag(Q @ S @ Q / len(y)))
    print(f'  {k:24s} {b[0] * 252 * 100:5.1f}  (t {b[0] / se[0]:.1f})')
# Section 7: historical episodes and sensitivity
S = {k: pd.concat([load(p, pk)['2008':'2012'], load(f, c)['2013':'2022']]) for k, (p, pk, f, c) in
     {'Trend': ('msb/pre_trend.pkl', 'xs', 'msb/trend_dev_results.pkl', 'xs'), 'Low volatility': ('msb/pre_lowvol.pkl', 'vs', 'msb/lowvol_results.pkl', 'vs'),
      'Momentum': ('msb/pre_mom.pkl', 'vs', 'msb/mom_results.pkl', 'vs')}.items()}
E = [('Lehman', '2008-09-01', '2008-11-30'), ('Momentum crash', '2009-03-01', '2009-05-31'), ('Euro crisis', '2011-07-01', '2011-09-30'),
     ('Swiss franc', '2015-01-12', '2015-01-23'), ('Covid', '2020-02-19', '2020-03-23'), ('Rate shock', '2022-01-01', '2022-10-31')]
print('\nSection 7.1: return % in each episode'); print(pd.DataFrame({k: {e: ((1 + s[a:b]).prod() - 1) * 100 for e, a, b in E} for k, s in S.items()}).round(1).to_string())
print('\nSection 7.2: development Sharpe under each change')
for k, f, c in [('Trend', 'trend', 'xs'), ('Low volatility', 'lowvol', 'vs'), ('Momentum', 'mom', 'vs')]:
    out = []
    for v in ('cost2', 'cost3', 'lag', 'borrow3'):
        try: s = load(f'msb/sens_{f}_{v}.pkl', c)['2013':'2022'].dropna(); out.append(f'{v} {s.mean() / s.std() * np.sqrt(252):.2f}')
        except FileNotFoundError: pass
    print(f'  {k:15s} ' + ' | '.join(out))
