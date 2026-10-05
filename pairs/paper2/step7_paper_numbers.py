"""Paper 2: numbers added to the paper after the corrected analysis (exploratory UK breakdown with the full equation, power, strategy t-statistics)."""
import numpy as np, pandas as pd
from scipy import stats
from step2_main import S, fit
FULL = ['thr', 'cal', 'week4', 'calw4', 'xa0', 'xa1', 'xa2', 'xa3', 'xa4', 'mom']
if __name__ == '__main__':
    print('Exploratory (not pre-registered): UK month-end coefficient by period, full equation')
    for name, a, b in (('1999-2008', '1999-01-01', '2008-12-31'), ('2009-2016', '2009-01-01', '2016-12-31'), ('2017-Mar 2023', '2017-01-01', '2023-03-17')):
        f = fit(S['UK'].loc[a:b].dropna(), FULL); print(f'  {name}: {f.params.calw4:+.3f} (t {f.tvalues.calw4:+.2f})')
    r = pd.read_pickle('step6_corrected_results.pkl')['R']
    print('Power to detect the UK main-sample effect (0.179) at 5%, two-sided')
    for lab, key in (('UK hold-out', ('UK', 'hold-out')), ('Germany main', ('DE', 'main')), ('Germany hold-out', ('DE', 'hold-out'))):
        v = r[key][('A local', 'calw4')]; se = v['coef'] / v['t_nw']; z = 0.179 / abs(se)
        print(f'  {lab}: standard error {abs(se):.4f}, power {(stats.norm.cdf(z - 1.96) + stats.norm.cdf(-z - 1.96)) * 100:.0f}%')
    print('UK month-end strategy, net of 1 basis point a trade on each leg')
    for per, (a, b) in (('main', ('1999-01-01', '2023-03-17')), ('hold-out', ('2023-03-20', '2026-09-30'))):
        d = S['UK'].loc[a:b].dropna(subset=['y_next']); pos = pd.Series(np.where(d.week4 > 0, -np.sign(d.cal), 0.0), d.index)
        net = (pos * d.y_next - pos.diff().abs().fillna(0) * 2e-4).dropna()
        print(f'  {per}: Sharpe {net.mean() / net.std() * np.sqrt(252):.2f}, t {net.mean() / net.std() * np.sqrt(len(net)):.2f}')
