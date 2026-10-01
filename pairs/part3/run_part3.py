"""Part 3: 70/30 large/small book. Frozen spec; one run plus the agreed robustness checks."""
import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import part2_moving_anchor as p2, model_600 as L, model_small as S

TARGET = 0.035
SPLIT = {'large': 0.70, 'small': 0.30}                    # risk shares
IDLE = {'equity': 0.65, 'bonds': 0.20, 'cash': 0.15}      # idle risk split
OVERLAY_COST_BPS, VOL_WIN, BACKSTOP, CAP, QTR = 1.0, 63, 0.035, 0.040, 63

def sleeve(mod, sigma, exclude=()):
    mod.SIGMA, mod.IDLE_TO_EQUITY, mod.BACKSTOP, mod.SLOTS = sigma, 0.0, 1.0, 10   # book-level rules applied below
    pa, ex = mod.run(exclude=exclude)
    return pa, ex

def combine(sleeves):
    """sleeves: {name: (pa, ex, sigma)} -> book DataFrame with attribution."""
    idx = sorted(set().union(*[set(pa.index) for pa, _, _ in sleeves.values()]))
    start = max(pa.index[0] for pa, _, _ in sleeves.values()); idx = pd.DatetimeIndex([d for d in idx if d >= start])
    estr, _ = p2.load_estr(idx); rf = p2.accrue(estr, idx)
    eq = sum(w * L.X[k] for k, w in L.EQ_SPLIT.items()).reindex(idx).fillna(0.0)          # equity excess return
    bond_px = S.D6['bond'].reindex(idx.union(S.D6['bond'].index)).ffill().reindex(idx)
    bond = (bond_px.pct_change(fill_method=None).fillna(0.0) - rf)                          # bond excess over EUR cash
    eq_vol = eq.rolling(VOL_WIN).std() * np.sqrt(252); bd_vol = bond.rolling(VOL_WIN).std() * np.sqrt(252)
    budget = sum(sig * ex['idle'].reindex(idx).ffill().fillna(ex['idle'].iloc[0]) / 10 for _, ex, sig in sleeves.values())
    w_eq = (IDLE['equity'] * budget / eq_vol).fillna(0.0); w_bd = (IDLE['bonds'] * budget / bd_vol).fillna(0.0)
    pair = {n: pa.pair_net.reindex(idx).fillna(0.0) for n, (pa, _, _) in sleeves.items()}
    pgross = {n: pa.pair_gross.reindex(idx).fillna(0.0) for n, (pa, _, _) in sleeves.items()}
    tov = {n: pa.turnover.reindex(idx).fillna(0.0) for n, (pa, _, _) in sleeves.items()}
    gross = sum(ex['gross'].reindex(idx).fillna(0.0) for _, ex, _ in sleeves.values()) + w_eq + w_bd
    # daily loop: overlays and pairs scaled by the backstop multiplier decided two closes earlier (module timing)
    n = len(idx); k = np.ones(n); eqv, peak, tripped, since = 1.0, 1.0, False, 0; rows = []
    for t in range(n):
        kk = k[t - 2] if t >= 2 else 1.0
        we, wb = (w_eq.iloc[t - 2] if t >= 2 else 0.0), (w_bd.iloc[t - 2] if t >= 2 else 0.0)
        we1, wb1 = (w_eq.iloc[t - 3] if t >= 3 else 0.0), (w_bd.iloc[t - 3] if t >= 3 else 0.0)
        e_p, b_p = kk * we * eq.iloc[t], kk * wb * bond.iloc[t]
        o_cost = kk * (abs(we - we1) + abs(wb - wb1)) * OVERLAY_COST_BPS / 1e4
        pr = {nm: kk * s.iloc[t] for nm, s in pair.items()}
        tot = rf.iloc[t] + sum(pr.values()) + e_p + b_p - o_cost
        eqv *= 1 + tot; peak = max(peak, eqv); dd = 1 - eqv / peak; since += 1
        if eqv >= peak: tripped, k[t] = False, 1.0
        elif dd >= BACKSTOP: tripped, k[t] = True, 0.0
        elif tripped and since % QTR == 0: k[t] = max(0.0, (CAP - dd) / CAP)
        else: k[t] = k[t - 1] if t else 1.0
        rows.append(dict(date=idx[t], cash=rf.iloc[t], equity=e_p, bonds=b_p, overlay_cost=o_cost, total=tot, k=k[t],
                         **{f'pairs_{nm}': v for nm, v in pr.items()}))
    bk = pd.DataFrame(rows).set_index('date')
    bk['excess'] = bk.total - bk.cash
    return bk, dict(eq=eq, bond=bond, gross=gross, pgross=pgross, tov=tov, w_eq=w_eq, w_bd=w_bd)

def report(bk, aux):
    a = 252; ex = bk.excess; cum = (1 + bk.total).cumprod(); dd = cum / cum.cummax() - 1
    pairs = bk.filter(like='pairs_').sum(axis=1)
    X = np.column_stack([np.ones(len(bk)), aux['eq'].reindex(bk.index), aux['bond'].reindex(bk.index)])
    b = np.linalg.lstsq(X, ex.values, rcond=None)[0]
    out = {'return_%/yr': ((cum.iloc[-1]) ** (a / len(bk)) - 1) * 100, 'vol_%': bk.total.std() * np.sqrt(a) * 100,
           'sharpe_xs_estr': ex.mean() / ex.std() * np.sqrt(a), 'max_dd_%': dd.min() * 100,
           'estr_%/yr': bk.cash.mean() * a * 100, 'equity_%/yr': bk.equity.mean() * a * 100, 'bonds_%/yr': bk.bonds.mean() * a * 100,
           'pair_alpha_net_%/yr': pairs.mean() * a * 100, 'pair_alpha_t': pairs.mean() / pairs.std() * np.sqrt(len(pairs)),
           'beta_equity': b[1], 'beta_bonds': b[2], 'backstop_days': int((bk.k < 1).sum()), 'avg_gross_x': aux['gross'].mean()}
    for nm in [c[6:] for c in bk.columns if c.startswith('pairs_')]:
        s = bk[f'pairs_{nm}']; g = aux['pgross'][nm].reindex(bk.index).fillna(0); tv = aux['tov'][nm].reindex(bk.index).fillna(0)
        out[f'{nm}_net_%/yr'] = s.mean() * a * 100; out[f'{nm}_t'] = s.mean() / s.std() * np.sqrt(len(s)) if s.std() > 0 else 0.0
        out[f'{nm}_breakeven_bps'] = g.sum() / tv.sum() * 1e4 if tv.sum() > 0 else np.nan
    return pd.Series(out)

if __name__ == '__main__':
    sL, sS = TARGET * np.sqrt(SPLIT['large']), TARGET * np.sqrt(SPLIT['small'])
    runs = {}
    L_pa, L_ex = sleeve(L, sL); S_pa, S_ex = sleeve(S, sS); print('sleeves done', flush=True)
    runs['Combined 70/30'] = combine({'large': (L_pa, L_ex, sL), 'small': (S_pa, S_ex, sS)})
    Lf_pa, Lf_ex = sleeve(L, TARGET); runs['Large caps alone'] = combine({'large': (Lf_pa, Lf_ex, TARGET)})
    Sf_pa, Sf_ex = sleeve(S, TARGET); runs['Small caps alone'] = combine({'small': (Sf_pa, Sf_ex, TARGET)})
    bL, bS = L_ex['per'].sum().idxmax(), S_ex['per'].sum().idxmax()
    L2_pa, L2_ex = sleeve(L, sL, exclude=(bL,)); S2_pa, S2_ex = sleeve(S, sS, exclude=(bS,))
    runs['Combined, w/o best large pair'] = combine({'large': (L2_pa, L2_ex, sL), 'small': (S_pa, S_ex, sS)})
    runs['Combined, w/o best small pair'] = combine({'large': (L_pa, L_ex, sL), 'small': (S2_pa, S2_ex, sS)})
    bk, aux = runs['Combined 70/30']; last = bk.index[-252]
    runs['Combined, hold-out year'] = (bk[bk.index >= last], aux)
    T = pd.DataFrame({k: report(*v) for k, v in runs.items()})
    pickle.dump(dict(runs=runs, best={'large': bL, 'small': bS}, S_log=S_ex['log'], L_log=L_ex['log'],
                     S_per=S_ex['per'], S_ex=S_ex), open('results_part3.pkl', 'wb'))
    pd.set_option('display.width', 250); print(T.round(2).to_string()); print('best pairs:', bL, '|', bS)
