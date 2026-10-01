"""Part 3, test 2: 65% large-cap pairs, 15% Eurozone small-cap pairs, 20% managed-futures ETFs. Idle risk in cash."""
import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import part2_moving_anchor as p2, model_600 as L, model_ezsmall as E
TARGET = 0.035; SPLIT = {'large': 0.65, 'small': 0.15, 'mf': 0.20}
MF_COST_BPS, COV_WIN, BACKSTOP, CAP, QTR = 5.0, 252, 0.035, 0.040, 63

def sleeve(mod, sigma, exclude=()):
    mod.SIGMA, mod.IDLE_TO_EQUITY, mod.BACKSTOP, mod.SLOTS = sigma, 0.0, 1.0, 10
    return mod.run(exclude=exclude)

def mf_sleeve(idx, sigma, drop=()):
    """Equal risk across the managed-futures ETFs, hedged to EUR (excess over USD cash), monthly rebalance, 1-day lag."""
    full = pd.DatetimeIndex(sorted(set().union(*[set(s.index) for s in E.D6['mf'].values()]) | set(idx)))  # use pre-test history for the covariance
    usd, _ = p2.load_usd_rate(full)
    X = pd.DataFrame({t: p2.market_excess(s, full, usd, 0.0) for t, s in E.D6['mf'].items() if t not in drop}).fillna(0.0)
    out_idx = idx; idx = full
    month_end = pd.Series(idx.month, index=idx); month_end = month_end.ne(month_end.shift(-1))
    W = pd.DataFrame(np.nan, index=idx, columns=X.columns)
    for i, d in enumerate(idx):
        if month_end.iloc[i] and i >= COV_WIN:
            cov = X.iloc[i - COV_WIN + 1:i + 1].cov().values * 252
            w = L.erc(cov); W.iloc[i] = w * sigma / np.sqrt(w @ cov @ w)
    W = W.ffill().fillna(0.0)
    held = W.shift(2).fillna(0.0)                                   # decided at close t, filled t+1, earns t+2
    gross = (held * X).sum(axis=1); cost = held.diff().abs().sum(axis=1).fillna(0.0) * MF_COST_BPS / 1e4
    res = pd.DataFrame({'pair_net': gross - cost, 'pair_gross': gross, 'turnover': held.diff().abs().sum(axis=1).fillna(0.0)})
    return res.reindex(out_idx).fillna(0.0), held.abs().sum(axis=1).reindex(out_idx).fillna(0.0)

def combine(parts):
    """parts: {name: DataFrame with pair_net, pair_gross, turnover}; idle risk in cash; book-level backstop."""
    start = max(p.index[0] for p in parts.values())
    idx = pd.DatetimeIndex(sorted(set().union(*[set(p.index) for p in parts.values()]))); idx = idx[idx >= start]
    estr, _ = p2.load_estr(idx); rf = p2.accrue(estr, idx)
    P = pd.DataFrame({n: p.pair_net.reindex(idx).fillna(0.0) for n, p in parts.items()})
    k = np.ones(len(idx)); eqv, peak, tripped, since = 1.0, 1.0, False, 0; rows = []
    for t in range(len(idx)):
        kk = k[t - 2] if t >= 2 else 1.0; pr = (kk * P.iloc[t]).to_dict(); tot = rf.iloc[t] + sum(pr.values())
        eqv *= 1 + tot; peak = max(peak, eqv); dd = 1 - eqv / peak; since += 1
        if eqv >= peak: tripped, k[t] = False, 1.0
        elif dd >= BACKSTOP: tripped, k[t] = True, 0.0
        elif tripped and since % QTR == 0: k[t] = max(0.0, (CAP - dd) / CAP)
        else: k[t] = k[t - 1] if t else 1.0
        rows.append(dict(date=idx[t], cash=rf.iloc[t], total=tot, k=k[t], **pr))
    bk = pd.DataFrame(rows).set_index('date'); bk['excess'] = bk.total - bk.cash
    return bk, parts

def report(bk, parts):
    a = 252; ex = bk.excess; cum = (1 + bk.total).cumprod(); dd = cum / cum.cummax() - 1
    eq = sum(w * L.X[k] for k, w in L.EQ_SPLIT.items()).reindex(bk.index).fillna(0.0)
    beta = np.polyfit(eq.values, ex.values, 1)[0]
    alpha = bk[list(parts)].sum(axis=1)
    out = {'return_%/yr': (cum.iloc[-1] ** (a / len(bk)) - 1) * 100, 'vol_%': bk.total.std() * np.sqrt(a) * 100,
           'sharpe_xs_estr': ex.mean() / ex.std() * np.sqrt(a), 'max_dd_%': dd.min() * 100, 'estr_%/yr': bk.cash.mean() * a * 100,
           'strategies_%/yr': alpha.mean() * a * 100, 'strategies_t': alpha.mean() / alpha.std() * np.sqrt(len(alpha)),
           'beta_equity': beta, 'backstop_days': int((bk.k < 1).sum())}
    for n, p in parts.items():
        s = bk[n]; g = p.pair_gross.reindex(bk.index).fillna(0); tv = p.turnover.reindex(bk.index).fillna(0)
        out[f'{n}_%/yr'] = s.mean() * a * 100; out[f'{n}_t'] = s.mean() / s.std() * np.sqrt(len(s)) if s.std() > 0 else 0.0
        if n != 'mf': out[f'{n}_breakeven_bps'] = g.sum() / tv.sum() * 1e4 if tv.sum() > 0 else np.nan
    return pd.Series(out)

if __name__ == '__main__':
    s = {k: TARGET * np.sqrt(v) for k, v in SPLIT.items()}
    Lp, Lx = sleeve(L, s['large']); Sp, Sx = sleeve(E, s['small']); print('pair sleeves done', flush=True)
    idx = Lp.index.union(Sp.index)
    MFp, MFg = mf_sleeve(idx, s['mf'])
    runs = {'Combined 65/15/20': combine({'large': Lp, 'small': Sp, 'mf': MFp})}
    Lf, _ = sleeve(L, TARGET); runs['Large caps alone'] = combine({'large': Lf})
    Sf, Sfx = sleeve(E, TARGET); runs['Small caps alone'] = combine({'small': Sf})
    MFf, _ = mf_sleeve(idx, TARGET); runs['Managed futures alone'] = combine({'mf': MFf})
    for t in E.D6['mf']:
        m2, _ = mf_sleeve(idx, s['mf'], drop=(t,)); runs[f'Combined, without {t}'] = combine({'large': Lp, 'small': Sp, 'mf': m2})
    bS = Sx['per'].sum().idxmax(); S2, _ = sleeve(E, s['small'], exclude=(bS,))
    runs['Combined, w/o best small pair'] = combine({'large': Lp, 'small': S2, 'mf': MFp})
    bk, parts = runs['Combined 65/15/20']; last = bk.index[-252]; runs['Combined, hold-out year'] = (bk[bk.index >= last], parts)
    T = pd.DataFrame({k: report(*v) for k, v in runs.items()})
    apr = bk.loc['2025-03-31':'2025-04-30']; apr_cols = [c for c in ['large', 'small', 'mf', 'total'] if c in apr]
    corr = pd.DataFrame({n: bk[n] for n in ['large', 'small', 'mf']}).assign(equity=sum(w * L.X[k] for k, w in L.EQ_SPLIT.items()).reindex(bk.index)).corr().round(2)
    pickle.dump(dict(runs=runs, T=T, corr=corr, S_log=Sx['log'], S_ex=Sx, MF_gross=MFg, best_small=bS), open('results_part3b.pkl', 'wb'))
    pd.set_option('display.width', 260); print(T.round(2).to_string())
    print('\nApril 2025 (31 Mar to 30 Apr), % of capital:', (apr[apr_cols].sum() * 100).round(2).to_dict())
    print('\nCorrelations of daily returns:\n', corr.to_string()); print('best small pair:', bS)
