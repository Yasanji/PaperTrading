"""Part 3 candidate: residual mean reversion (Avellaneda & Lee 2010) on the STOXX 600.
Frozen parameters; the risk framework from Part 2 (stop latch, evidence floor, vol target, backstop)."""
import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from numpy.lib.stride_tricks import sliding_window_view as swv
import part2_moving_anchor as p2

# ---------------- frozen parameters ----------------
WIN, MIN_IND, MAX_REV_DAYS = 60, 5, 30
S_OPEN, S_CLOSE_SHORT, S_CLOSE_LONG, S_STOP = 1.25, 0.75, -0.5, 4.0   # Avellaneda & Lee thresholds
SIGMA, MAX_NAME, GROSS_CAP, TURN_CAP = 0.035, 0.05, 3.0, 0.25
COST_BPS, LONG_CARRY_BPS, SHORT_CARRY_BPS, LAG = 3.0, 25.0, 45.0, 1   # as Part 2
DROP_WEEKS, DROP_DAYS = 3, 42
BACKSTOP, CAP, QTR = 0.035, 0.040, 63
START = '2023-09-11'                                                    # same OOS start as Part 2

# ---------------- data: EUR returns ----------------
D6 = pickle.load(open('data600.pkl', 'rb')); META = D6['meta'].drop_duplicates('yf')
META = META[META.yf.isin(D6['px'].keys())].set_index('yf')
FX = pickle.load(open('fx.pkl', 'rb')); D = pickle.load(open('data.pkl', 'rb'))
NAMES = sorted(META.index)
prices = pd.concat({n: D6['px'][n] for n in NAMES}, axis=1).dropna(how='all').sort_index()
dates = prices.index
avail = prices.ffill().notna()
r_loc = prices.ffill().pct_change(fill_method=None)
ccy = META.currency.replace({'GBp': 'GBP'})
r_fx = pd.DataFrame({n: (FX[ccy[n]].reindex(dates.union(FX[ccy[n]].index)).ffill().reindex(dates).pct_change(fill_method=None)
                         if ccy[n] != 'EUR' else pd.Series(0.0, index=dates)) for n in NAMES})
R = ((1 + r_loc) * (1 + r_fx.fillna(0)) - 1).clip(-0.5, 0.5).where(avail)   # EUR daily returns
IND = META.industry
estr, _ = p2.load_estr(dates); usd, _ = p2.load_usd_rate(dates)
Xm = pd.DataFrame({'spx': p2.market_excess(D['idx']['^GSPC'], dates, usd, 1.3),
                   'sx5e': p2.market_excess(D['idx']['^STOXX50E'], dates, estr, 3.0)}).fillna(0.0)

def signals(exclude_ind=()):
    """Per stock and day: s-score, eligibility, hedge beta, residual vol, leave-one-out industry return."""
    T, N = len(dates), len(NAMES)
    S = np.full((T, N), np.nan); EL = np.zeros((T, N), bool); B = np.full((T, N), np.nan)
    SV = np.full((T, N), np.nan); LOO = np.full((T, N), np.nan)
    Rv = R.values; Av = avail.values
    for ind, members in IND.groupby(IND).groups.items():
        if ind in exclude_ind: continue
        idx = [NAMES.index(m) for m in members]
        if len(idx) < MIN_IND: continue
        sub = np.nan_to_num(Rv[:, idx]); cnt = Av[:, idx].sum(1)
        tot = sub.sum(1)
        for k, j in enumerate(idx):
            loo = np.where((cnt - Av[:, j]) >= MIN_IND - 1, (tot - sub[:, k]) / np.maximum(cnt - Av[:, j], 1), np.nan)
            LOO[:, j] = loo
            y, x = Rv[:, j], loo
            if len(y) < WIN: continue
            Y, Xw = swv(y, WIN), swv(x, WIN)                    # window ending at t = i + WIN - 1
            ok = np.isfinite(Y).all(1) & np.isfinite(Xw).all(1)
            Y, Xw = np.nan_to_num(Y), np.nan_to_num(Xw)
            xm, ym = Xw.mean(1, keepdims=True), Y.mean(1, keepdims=True)
            vx = ((Xw - xm) ** 2).sum(1)
            b = np.where(vx > 0, ((Xw - xm) * (Y - ym)).sum(1) / np.where(vx > 0, vx, 1), 0.0)
            a = ym[:, 0] - b * xm[:, 0]
            e = Y - a[:, None] - b[:, None] * Xw
            Xc = np.cumsum(e, 1); X0, X1 = Xc[:, :-1], Xc[:, 1:]
            m0, m1 = X0.mean(1, keepdims=True), X1.mean(1, keepdims=True)
            v0 = ((X0 - m0) ** 2).sum(1)
            b2 = np.where(v0 > 0, ((X0 - m0) * (X1 - m1)).sum(1) / np.where(v0 > 0, v0, 1), np.nan)
            a2 = m1[:, 0] - b2 * m0[:, 0]
            z = X1 - a2[:, None] - b2[:, None] * X0
            good = ok & (b2 > 0) & (b2 < 1)
            with np.errstate(all='ignore'):
                mu = a2 / (1 - b2); sig = np.sqrt(z.var(1) / (1 - b2 ** 2))
                s = (Xc[:, -1] - mu) / sig
                rev_days = -1 / np.log(b2)
            rows = np.arange(WIN - 1, len(y))
            S[rows, j] = np.where(good & np.isfinite(s), s, np.nan)
            EL[rows, j] = good & (rev_days < MAX_REV_DAYS) & np.isfinite(s)
            B[rows, j] = b; SV[rows, j] = e.std(1) * np.sqrt(252)
    return S, EL, B, SV, LOO

def run(exclude_ind=()):
    S, EL, B, SV, LOO = signals(exclude_ind)
    T, N = S.shape; t0 = dates.get_loc(pd.Timestamp(START)) if pd.Timestamp(START) in dates else dates.searchsorted(pd.Timestamp(START))
    Rv = np.nan_to_num(R.values); LOOv = np.nan_to_num(LOO)
    ind_codes = pd.Categorical(IND.reindex(NAMES)).codes
    # ---- position state machine + evidence floor on the unit (paper) spread P&L ----
    POS = np.zeros((T, N)); pos = np.zeros(N); stopped = np.zeros(N, bool); drop_until = np.zeros(N, int)
    lose = np.zeros(N, int); wk = np.zeros(N); held_wk = np.zeros(N, bool)
    week = dates.isocalendar().week.values.astype(int)
    for t in range(t0, T):
        # unit P&L of the position held into today (decided at t-1-LAG), for the floor
        if t - 1 - LAG >= 0:
            ph = POS[t - 1 - LAG]; bh = np.nan_to_num(B[t - 1 - LAG])
            u = ph * (Rv[t] - bh * LOOv[t]); wk += u; held_wk |= ph != 0
        s = S[t]; fin = np.isfinite(s)
        st_hit = (pos != 0) & fin & (np.abs(s) >= S_STOP)
        pos[st_hit] = 0; stopped |= st_hit
        stopped &= ~(fin & (s > S_CLOSE_LONG) & (s < S_CLOSE_SHORT))
        pos[(pos == -1) & fin & (s < S_CLOSE_SHORT)] = 0
        pos[(pos == 1) & fin & (s > S_CLOSE_LONG)] = 0
        pos[~fin] = 0
        can = (pos == 0) & ~stopped & EL[t] & (t >= drop_until) & fin
        pos[can & (s > S_OPEN)] = -1; pos[can & (s < -S_OPEN)] = 1
        if t == T - 1 or week[t + 1] != week[t]:                       # week end
            lose = np.where(held_wk & (wk < 0), lose + 1, np.where(held_wk & (wk > 0), 0, lose))
            hit = lose >= DROP_WEEKS
            drop_until[hit] = t + DROP_DAYS; pos[hit] = 0; lose[hit] = 0
            wk[:] = 0; held_wk[:] = False
        pos[t < drop_until] = 0
        POS[t] = pos
    # ---- target weights: equal risk per position, industry hedge, caps ----
    TW = np.zeros((T, N)); ncode = ind_codes.max() + 1
    for t in range(t0, T):
        p = POS[t]; act = p != 0
        n = act.sum()
        if n == 0: continue
        w = np.zeros(N); w[act] = p[act] * (SIGMA / np.sqrt(n)) / np.maximum(SV[t, act], 0.05)
        wb = w * np.nan_to_num(B[t])
        live = np.isfinite(LOO[t]) | act
        H = np.bincount(ind_codes, weights=wb, minlength=ncode)
        cnt = np.bincount(ind_codes, weights=(np.isfinite(R.values[t]) & live).astype(float), minlength=ncode)
        memb = np.isfinite(R.values[t]) & live
        hedge = np.where(memb, -(H[ind_codes] - wb) / np.maximum(cnt[ind_codes] - 1, 1), 0.0)
        nw = w + hedge
        g = np.abs(nw).sum(); nw = np.clip(nw, -MAX_NAME * g, MAX_NAME * g)
        g = np.abs(nw).sum()
        if g > GROSS_CAP: nw *= GROSS_CAP / g
        TW[t] = nw
    # ---- daily loop: lag, turnover cap, backstop, P&L ----
    rf = p2.accrue(estr, dates).values
    EX = np.zeros((T, N)); k, tripped, eq, peak = 1.0, False, 1.0, 1.0
    rows = []; since = 0
    for t in range(t0, T):
        prev = EX[t - 1]
        desired = k * TW[t - 1] if t - 1 >= t0 else np.zeros(N)
        delta = desired - prev; turn = np.abs(delta).sum()
        capt = TURN_CAP * max(np.abs(prev).sum(), np.abs(desired).sum())
        if k > 0 and turn > capt and capt > 0: delta *= capt / turn
        EX[t] = prev + delta
        pg = prev @ Rv[t]; tw = np.abs(EX[t] - prev).sum()
        wl, ws = prev.clip(min=0).sum(), -prev.clip(max=0).sum()
        carry = (wl * LONG_CARRY_BPS + ws * SHORT_CARRY_BPS) / 1e4 / 252
        cost = tw * COST_BPS / 1e4
        tot = rf[t] + pg - cost - carry
        eq *= 1 + tot; peak = max(peak, eq); dd = 1 - eq / peak
        since += 1
        if eq >= peak: tripped, k = False, 1.0
        if dd >= BACKSTOP: tripped, k = True, 0.0
        elif tripped and since % QTR == 0: k = max(0.0, (CAP - dd) / CAP)
        rows.append((dates[t], pg, cost + carry, tw, rf[t], (prev != 0).sum(), np.abs(prev).sum(), k))
    pa = pd.DataFrame(rows, columns=['date', 'pair_gross', 'pair_costs', 'turnover', 'cash', 'n_pos', 'gross', 'k']).set_index('date')
    pa['rf'] = pa.cash; pa['pair_net'] = pa.pair_gross - pa.pair_costs
    for kk in ('spx', 'sx5e'): pa[f'x_{kk}'] = Xm[kk].reindex(pa.index); pa[f'mkt_{kk}'] = 0.0
    pa['market'] = 0.0; pa['total'] = pa.cash + pa.pair_net; pa['excess'] = pa.total - pa.rf
    pa.attrs['lags'] = {'spx': True, 'sx5e': False}
    # per-industry net contribution (for the robustness check)
    contrib = {}
    pnl = (np.vstack([np.zeros(N), EX[t0:-1]]) * Rv[t0:])
    for ind in IND.unique():
        cols = [NAMES.index(m) for m in IND[IND == ind].index]
        contrib[ind] = pnl[:, cols].sum() / len(pa) * 252 * 100
    return pa, dict(contrib=pd.Series(contrib).sort_values(ascending=False), EX=EX, POS=POS)
