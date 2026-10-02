import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import kalman_patch; kalman_patch.MEMORY = 90
import part2_moving_anchor as p2, model_v5_kalman as A, model_600_kalman as B
def rep(pa):
    h, ab, d = p2.decision_report(pa); pn = pa.pair_net
    return dict(sharpe=h['sharpe (excess of €STR)'], ret=h['total_ret_%/yr'], maxdd=h['max_dd_%'], alpha=pn.mean() * 252 * 100,
                t=pn.mean() / pn.std() * np.sqrt(len(pn)), beta=ab['beta_total'], turnover=d['turnover_x_capital/yr'])
A.SLOTS = 3; pa, ex = A.run(); B.SLOTS, B.SIGMA, B.IDLE_TO_EQUITY = 10, 0.035, 0.70; pb, exb = B.run()
V5 = pickle.load(open('results_v5.pkl', 'rb')); O = pickle.load(open('results_600.pkl', 'rb'))
T = pd.DataFrame({'EURO STOXX 50: rolling anchor (published)': rep(V5['pa']), 'EURO STOXX 50: Kalman, 90-day': rep(pa),
                  'STOXX 600 10 pairs: rolling anchor (published)': rep(O[10]['pa']), 'STOXX 600 10 pairs: Kalman, 90-day': rep(pb)}).T
pd.set_option('display.width', 220); print(T.round(2).to_string())
print('\npicks: SX5E', len(ex['log']), '| STOXX600', len(exb['log']), '| avg funded SX5E', round(ex['active'].mean(), 2), 'STOXX600', round(exb['active'].mean(), 2))
pickle.dump(dict(T=T, pa=pa, pb=pb, ex=ex, exb=exb), open('results_kalman90.pkl', 'wb'))
