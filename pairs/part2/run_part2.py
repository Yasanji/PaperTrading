"""Part 2: run the frozen design on both universes.

    python get_data.py        # EURO STOXX 50 names, ^GSPC, ^STOXX50E  -> data.pkl
    python get600.py          # STOXX 600 names + Yahoo industries    -> data600.pkl
    python run_part2.py       # both walk-forwards + robustness checks -> results/
"""
import numpy as np, pandas as pd
import part2_moving_anchor as p2

def summary(pa):
    head, ab, dec = p2.decision_report(pa); pn = pa.pair_net
    return {'return_%/yr': head['total_ret_%/yr'], 'vol_%': head['vol_%'],
            'sharpe_xs_estr': head['sharpe (excess of €STR)'], 'max_dd_%': head['max_dd_%'],
            'pair_alpha_net_%/yr': pn.mean() * 252 * 100,
            'pair_alpha_t': pn.mean() / pn.std() * np.sqrt(len(pn)),
            'equity_idle_%/yr': pa.market.mean() * 252 * 100,
            'beta_total': ab['beta_total'], 'turnover_x/yr': dec['turnover_x_capital/yr']}

if __name__ == '__main__':
    import model_sx5e as A, model_stoxx600 as B
    out = {}
    pa, ex = A.run(); best = ex['per'].sum().idxmax()
    out['sx5e_3'] = summary(pa); out['sx5e_3_ex_best'] = summary(A.run(exclude=(best,))[0])
    ex['log'].to_csv('results/sx5e_pair_log.csv', index=False)
    for k in (3, 10):
        B.SLOTS = k; pa, ex = B.run(); best = ex['per'].sum().idxmax()
        out[f'stoxx600_{k}'] = summary(pa); out[f'stoxx600_{k}_ex_best'] = summary(B.run(exclude=(best,))[0])
        ex['log'].to_csv(f'results/stoxx600_pair_log_{k}pairs.csv', index=False)
    pd.DataFrame(out).round(3).to_csv('results/summary.csv'); print(pd.DataFrame(out).round(2))
