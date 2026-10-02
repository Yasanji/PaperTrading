"""Signal test 11 (fixed 1 Oct 2026): volatility-managed equity index, Moreira and Muir (2017)."""
import numpy as np, pandas as pd, yfinance as yf, pickle, warnings; warnings.filterwarnings('ignore')
px = yf.download(['^STOXX50E', '^GSPC'], start='2004-01-01', end='2026-09-26', auto_adjust=True, progress=False)['Close'].ffill()
out, keep = {}, {}
for tk, lab in [('^STOXX50E', 'EURO STOXX 50'), ('^GSPC', 'S&P 500')]:
    r = px[tk].pct_change().dropna(); days = r.index
    me = pd.DatetimeIndex(r.groupby([days.year, days.month]).apply(lambda s: s.index[-1]).values)   # month-end trading days
    w = pd.Series(np.nan, index=days)
    for d in me:
        i = days.get_loc(d)
        if i < 756 or i + 1 >= len(days): continue
        month = r[(days.year == d.year) & (days.month == d.month)]
        var_m = (month ** 2).mean() * 252; target = r.iloc[i - 755:i + 1].var() * 252
        w.iloc[i + 1] = min(target / var_m, 2.0) if var_m > 0 else np.nan               # from the next day's close
    w = w.ffill(); m = (w.shift(1) * r - w.diff().abs() * 2e-4).dropna(); b = r.reindex(m.index)
    def stats(a, z):
        x, y = m[a:z], b[a:z]; X = np.column_stack([np.ones(len(y)), y.values]); coef, res, *_ = np.linalg.lstsq(X, x.values, rcond=None)
        e = x.values - X @ coef; se = np.sqrt(e.var(ddof=2) / len(e) * np.linalg.inv(X.T @ X / len(e))[0, 0])
        return dict(alpha_pct=coef[0] * 252 * 100, t=coef[0] / se, beta=coef[1], sharpe_managed=x.mean() / x.std() * np.sqrt(252),
                    sharpe_index=y.mean() / y.std() * np.sqrt(252), avg_weight=w[a:z].mean())
    for p, a, z in [('2013-2022', '2013-01-01', '2022-12-31'), ('2013-2017', '2013-01-01', '2017-12-31'), ('2018-2022', '2018-01-01', '2022-12-31'), ('2008-2012', '2008-01-01', '2012-12-31')]:
        out[f'{lab} | {p}'] = stats(a, z)
    keep[lab] = (m, b, w)
T = pd.DataFrame(out).T; pd.set_option('display.width', 220); print(T.round(2).to_string())
e = {p: out[f'EURO STOXX 50 | {p}'] for p in ('2013-2022', '2013-2017', '2018-2022', '2008-2012')}
ok = e['2013-2022']['alpha_pct'] > 0 and e['2013-2022']['t'] > 2 and e['2013-2017']['alpha_pct'] > 0 and e['2018-2022']['alpha_pct'] > 0 and e['2008-2012']['alpha_pct'] > 0
print('\nPRE-REGISTERED PASS MARK (EURO STOXX 50):', 'PASS' if ok else 'FAIL')
pickle.dump(dict(T=T, keep=keep), open('msb/volmanaged_results.pkl', 'wb'))
