"""Part 2 final design - frozen parameters, one run. Reuses the Part 2 module's helpers."""
import pickle, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from itertools import combinations
import part2_moving_anchor as p2

# ---------------- frozen parameters (set before any result is seen) ----------------
FORM, TRADE, SLOTS, MIN_FUNDED = 504, 63, 3, 2
P_MAX, CORR_MIN, B_MIN, B_MAX = 0.05, 0.70, 0.5, 2.0
ENTRY, EXIT, STOP, ANCHOR = 2.0, 0.4, 4.0, 90
COST_BPS, SLIP_BPS, LAG = 5.0, 5.0, 1             # small caps: 10bp per trade
SIGMA = 0.035                     # book vol target (3-4%)
GROSS_CAP = 3.0                   # hard gross limit, x capital
SHRINK, SECTOR_RHO_FLOOR = 0.5, 0.3
DROP_WEEKS, READMIT_MONTHS = 3, 2
IDLE_TO_EQUITY = 0.70             # 70% of idle risk -> equity, 30% cash
EQ_SPLIT = {'spx': 2/3, 'sx5e': 1/3}; EQ_VOL_WIN = 63; EQ_COST_BPS = 1.0
BACKSTOP, CAP = 0.035, 0.040
LONG_CARRY_BPS, SHORT_CARRY_BPS = 25.0, 150.0      # small caps: 1.5% a year borrow
MIN_ADV = 1e6                                         # median daily traded value, GBP
MAX_LIVE_SCALE = 2.0              # size on in-trade risk: x 1/sqrt(live share), capped
FLAT_IS_IDLE = False              # coherent version: only empty/dropped slots are idle      # go to cash at -3.5%; resume scaled to headroom under 4%

D6 = pickle.load(open('data250.pkl', 'rb')); META = D6['meta'].drop_duplicates('yf')
META = META[META.yf.isin(D6['px'].keys())]
# listed funds are excluded (spec rule): fund-type sector label or a fund name
_ICB = r'Investment Trust|Closed End|Collective Investment|Equity Investment|Hedge Fund|General Financial'
_NAME = r'\bTrust\b|\bFund\b(?! Management)|Investments\b|Partnerships\b|Private Equity|Income\b|Infrastructure|Opportunit|\bMacro\b'
META = META[~(META.icb.str.contains(_ICB, case=False, na=False) | META.company.str.contains(_NAME, case=False, na=False))]
SEC = dict(zip(META.yf, META.industry + '|' + META.currency))     # same industry AND currency
NAMES = sorted(SEC); px = D6['px']
D = pickle.load(open('data.pkl', 'rb')); spx, sx5e = D['idx']['^GSPC'], D['idx']['^STOXX50E']
prices = pd.concat({n: px[n] for n in NAMES}, axis=1).dropna(how='all'); dates = prices.index
R = prices.ffill().pct_change(fill_method=None).fillna(0.0).clip(-0.5, 0.5)
estr, _ = p2.load_estr(dates); usd, _ = p2.load_usd_rate(dates)
X = pd.DataFrame({'spx': p2.market_excess(spx, dates, usd, 1.3),
                  'sx5e': p2.market_excess(sx5e, dates, estr, 3.0)}).fillna(0.0)
eq_combo = sum(w * X[k] for k, w in EQ_SPLIT.items())
eq_vol = (eq_combo.rolling(EQ_VOL_WIN).std() * np.sqrt(252))
_SCREEN = {}
ADV = pd.concat({n: D6['adv_gbp'][n] for n in NAMES}, axis=1).reindex(dates)

ALLPAIRS = [(a, b) for a, b in combinations(NAMES, 2) if SEC[a] == SEC[b]]
# ---------------- building blocks ----------------
def screen(f, pairs, hl_max):
    keep = []
    for a, b in pairs:
        d = f[[a, b]].dropna()
        if len(d) < 250 or d[a].corr(d[b]) < CORR_MIN: continue
        if ADV.loc[f.index, [a, b]].median().min() < MIN_ADV: continue      # liquidity filter
        p = max(p2.ts.coint(d[a], d[b])[1], p2.ts.coint(d[b], d[a])[1])
        beta, alpha = np.polyfit(np.log(d[b]), np.log(d[a]), 1)
        hl = p2.half_life(np.log(d[a]) - alpha - beta * np.log(d[b]))
        if p < P_MAX and hl <= hl_max and B_MIN <= beta <= B_MAX:
            keep.append((a, b, p, hl, beta))
    return pd.DataFrame(keep, columns=['a', 'b', 'p', 'half_life', 'beta']).sort_values('p')

def zscore(h, a, b, beta):
    s = np.log(h[a]) - beta * np.log(h[b])
    return (s - s.rolling(ANCHOR).mean().shift(1)) / s.rolling(ANCHOR).std().shift(1)

def positions(z, allowed):
    """Entry/exit/stop, with the stop latch: after a stop, no re-entry until |z| <= EXIT."""
    pos = np.zeros(len(z)); cur = 0.0; stopped = False; ok = allowed.values
    for i, zi in enumerate(z.values):
        if not ok[i]: cur = 0.0; stopped = False; continue
        if np.isnan(zi): pos[i] = cur; continue
        if stopped:
            if abs(zi) <= EXIT: stopped = False
            continue
        if cur != 0 and abs(zi) >= STOP: cur = 0.0; stopped = True
        elif cur == 0: cur = -1.0 if zi >= ENTRY else (1.0 if zi <= -ENTRY else 0.0)
        elif abs(zi) <= EXIT: cur = 0.0
        pos[i] = cur
    return pd.Series(pos, index=z.index)

def unit_pnl(a, b, beta, pos, idx):
    """Net P&L of 1 unit of gross in the pair (paper track), module timing conventions."""
    uy = (pos / (1 + beta.abs())).shift(LAG).fillna(0); ux = (-pos * beta / (1 + beta.abs())).shift(LAG).fillna(0)
    g = uy.shift(1).fillna(0) * R[a].reindex(idx) + ux.shift(1).fillna(0) * R[b].reindex(idx)
    t = uy.diff().abs().fillna(0) + ux.diff().abs().fillna(0)
    return g - t * (COST_BPS + SLIP_BPS) / 1e4

def formation_pass(f, a, b, beta):
    h = f[[a, b]].dropna(); z = zscore(h, a, b, beta)
    pos = positions(z, pd.Series(True, index=z.index))
    live = (pos[z.notna()] != 0).mean()
    return unit_pnl(a, b, pd.Series(beta, index=h.index), pos, h.index).sum() > 0, live

def erc(cov, iters=5000, tol=1e-10):
    """Equal risk contribution, long-only: multiplicative update keeps every weight positive."""
    n = len(cov)
    ev = np.linalg.eigvalsh(cov)
    if ev.min() <= 0: cov = cov + (abs(ev.min()) + 1e-10) * np.eye(n)
    w = 1.0 / np.sqrt(np.diag(cov)); w /= w.sum()
    for _ in range(iters):
        rc = w * (cov @ w); share = rc / rc.sum()
        w_new = w * np.sqrt((1.0 / n) / share); w_new /= w_new.sum()
        if np.abs(w_new - w).max() < tol: w = w_new; break
        w = w_new
    return w

def sizes(picks, f):
    """ERC unit-gross sizes; pair book vol = SIGMA * n / SLOTS if all were live."""
    U = pd.DataFrame({i: (f[r.a].pct_change() - r.beta * f[r.b].pct_change()) / (1 + abs(r.beta))
                      for i, r in picks.iterrows()}).dropna()
    sd = U.std().values * np.sqrt(252); C = U.corr().values
    C = SHRINK * C + (1 - SHRINK) * np.eye(len(C))
    secs = [SEC[r.a] for _, r in picks.iterrows()]
    for i in range(len(C)):
        for j in range(len(C)):
            if i != j and secs[i] == secs[j]: C[i, j] = max(C[i, j], SECTOR_RHO_FLOOR)
    cov = np.outer(sd, sd) * C
    w = erc(cov); w *= (SIGMA * len(w) / SLOTS) / np.sqrt(w @ cov @ w)
    return dict(zip(picks.index, w))

# ---------------- the model ----------------
def run(exclude=()):

    hl_max = FORM / 3
    Z, B, SIZE, SEL, FPASS, WSTART, log = {}, {}, {}, {}, {}, [], []
    for s0 in range(FORM, len(dates) - 1, TRADE):
        f_idx, t_idx = dates[s0 - FORM:s0], dates[s0:s0 + TRADE]; WSTART.append(t_idx[0])
        f = prices.loc[f_idx]
        if f_idx[0] not in _SCREEN: _SCREEN[f_idx[0]] = screen(f, ALLPAIRS, hl_max)
        sc = _SCREEN[f_idx[0]]; sc = sc[~(sc.a + '|' + sc.b).isin(exclude)]
        picks = sc.head(SLOTS).reset_index(drop=True)
        fps = {i: formation_pass(f, r.a, r.b, r.beta) for i, r in picks.iterrows()}
        sz = sizes(picks, f) if len(picks) >= MIN_FUNDED else {i: 0.0 for i in picks.index}
        sz = {i: v * min(MAX_LIVE_SCALE, 1 / np.sqrt(max(fps[i][1], 1e-9))) for i, v in sz.items()}
        for i, r in picks.iterrows():
            k = f'{r.a}|{r.b}'
            h = prices.loc[f_idx[0]:t_idx[-1], [r.a, r.b]].dropna()
            Z.setdefault(k, []).append(zscore(h, r.a, r.b, r.beta).reindex(t_idx))
            B.setdefault(k, []).append(pd.Series(r.beta, index=t_idx))
            SIZE.setdefault(k, []).append(pd.Series(sz[i], index=t_idx))
            SEL.setdefault(k, []).append(pd.Series(True, index=t_idx))
            fp, live = fps[i]
            FPASS.setdefault(k, []).append(pd.Series(fp, index=t_idx))
            log.append(dict(window=t_idx[0].date(), pair=k, sector=SEC[r.a], p=round(r.p, 4),
                            half_life=round(r.half_life, 1), beta=round(r.beta, 2),
                            size=round(sz[i], 3), formation_pass=fp, live_share=round(live, 2)))
    start = WSTART[0]; idx = dates[dates >= start]
    wk_end = pd.Series(idx.isocalendar().week.values.astype(int), index=idx); wk_end = wk_end.ne(wk_end.shift(-1)).fillna(True).astype(bool)
    mo_end = pd.Series(idx.month, index=idx); mo_end = mo_end.ne(mo_end.shift(-1)).fillna(True).astype(bool)
    win_start = pd.Series(idx.isin(WSTART), index=idx)

    P = {}
    for k in Z:
        a, b = k.split('|')
        sel = pd.concat(SEL[k]).reindex(idx).fillna(False).astype(bool)
        z = pd.concat(Z[k]).reindex(idx); beta = pd.concat(B[k]).reindex(idx).ffill().bfill()
        size = pd.concat(SIZE[k]).reindex(idx).fillna(0.0)
        fpass = pd.concat(FPASS[k]).reindex(idx).fillna(False).astype(bool)
        pos = positions(z, sel); paper = unit_pnl(a, b, beta, pos, idx)
        # evidence floor: state machine on the paper track, known at each close
        funded = np.zeros(len(idx), bool); on = False; lose = win = 0; wk = mo = 0.0
        for i, d in enumerate(idx):
            if not sel.iloc[i]:
                on = False; lose = win = 0; wk = mo = 0.0; continue
            if win_start.iloc[i] and (i == 0 or not sel.iloc[i - 1]):   # new episode
                on, lose, win, wk, mo = bool(fpass.iloc[i]), 0, 0, 0.0, 0.0
            elif win_start.iloc[i] and not fpass.iloc[i]:
                on = False; win = 0
            wk += paper.iloc[i]; mo += paper.iloc[i]
            if wk_end.iloc[i]:
                if on:
                    lose = lose + 1 if wk < 0 else (0 if wk > 0 else lose)
                    if lose >= DROP_WEEKS: on, win, mo = False, 0, 0.0
                wk = 0.0
            if mo_end.iloc[i]:
                if not on:
                    win = win + 1 if mo > 0 else (0 if mo < 0 else win)
                    if win >= READMIT_MONTHS: on, lose = True, 0
                mo = 0.0
            funded[i] = on
        P[k] = dict(a=a, b=b, sel=sel, pos=pos, beta=beta, size=size, paper=paper,
                    funded=pd.Series(funded, index=idx), sector=SEC[a])

    # at least MIN_FUNDED funded pairs, else none trade
    nf = sum(p['funded'].astype(int) for p in P.values())
    live_ok = nf >= MIN_FUNDED
    TW = pd.DataFrame(0.0, index=idx, columns=NAMES); PW = {}; active = pd.Series(0, index=idx)
    for k, p in P.items():
        m = p['size'] * (p['funded'] & live_ok) * p['pos']
        wy, wx = m / (1 + p['beta'].abs()), -m * p['beta'] / (1 + p['beta'].abs())
        PW[k] = (wy, wx); TW[p['a']] += wy; TW[p['b']] += wx
        active += ((m != 0) if FLAT_IS_IDLE else (p['size'] * (p['funded'] & live_ok) != 0)).astype(int)
    g = TW.abs().sum(axis=1); scl = (GROSS_CAP / g).clip(upper=1.0).fillna(1.0)
    TW = TW.mul(scl, axis=0)
    idle = SLOTS - active.clip(upper=SLOTS)
    e_tot = (IDLE_TO_EQUITY * SIGMA * idle / SLOTS / eq_vol.reindex(idx)).fillna(0.0)
    TE = pd.DataFrame({k: w * e_tot for k, w in EQ_SPLIT.items()})

    # daily loop: backstop decided at each close; target at t executed t+1, earns t+2
    n = len(idx); Rv = R.reindex(idx).values; Xv = X.reindex(idx).values
    TWv, TEv = TW.values, TE.values; rf = p2.accrue(estr, idx).values
    EXW = np.zeros_like(TWv); EXE = np.zeros_like(TEv); kser = np.ones(n)
    eq, peak, k, tripped = 1.0, 1.0, 1.0, False
    rows = np.zeros((n, 7))   # pair_gross, stock_cost, carry, market, eq_cost, turnover, cash
    for t in range(n):
        if t >= 1:
            EXW[t] = kser[t - 1] * TWv[t - 1]; EXE[t] = kser[t - 1] * TEv[t - 1]
        prevW = EXW[t - 1] if t >= 1 else np.zeros(TWv.shape[1])
        prevE = EXE[t - 1] if t >= 1 else np.zeros(TEv.shape[1])
        pg = prevW @ Rv[t]; mk = prevE @ Xv[t]
        tw = np.abs(EXW[t] - prevW).sum(); te = np.abs(EXE[t] - prevE).sum()
        wl, ws = prevW.clip(min=0).sum(), -prevW.clip(max=0).sum()
        carry = (wl * LONG_CARRY_BPS + ws * SHORT_CARRY_BPS) / 1e4 / 252
        rows[t] = [pg, tw * (COST_BPS + SLIP_BPS) / 1e4, carry, mk, te * EQ_COST_BPS / 1e4, tw, rf[t]]
        tot = rf[t] + pg - rows[t, 1] - carry + mk - rows[t, 4]
        eq *= 1 + tot; peak = max(peak, eq); dd = 1 - eq / peak
        if eq >= peak: tripped, k = False, 1.0
        if dd >= BACKSTOP: tripped, k = True, 0.0
        elif tripped and win_start.iloc[t]: k = max(0.0, (CAP - dd) / CAP)
        kser[t] = k
    pa = pd.DataFrame(rows, index=idx, columns=['pair_gross', 'stock_cost', 'carry', 'mkt', 'eq_cost', 'turnover', 'cash'])
    pa['rf'] = pa.cash
    pa['pair_costs'] = pa.stock_cost + pa.carry
    pa['pair_net'] = pa.pair_gross - pa.pair_costs
    for kk in EQ_SPLIT:
        pa[f'x_{kk}'] = X[kk].reindex(idx)
        pa[f'mkt_{kk}'] = pd.Series(EXE[:, list(EQ_SPLIT).index(kk)], index=idx).shift(1).fillna(0) * pa[f'x_{kk}']
    pa['market'] = pa.mkt - pa.eq_cost
    pa['total'] = pa.cash + pa.market + pa.pair_net; pa['excess'] = pa.total - pa.rf
    pa.attrs['lags'] = {'spx': True, 'sx5e': False}
    # per-pair attribution (before netting)
    ks = pd.Series(kser, index=idx).shift(1).fillna(1)
    per = {}
    for kk, (wy, wx) in PW.items():
        a, b = P[kk]['a'], P[kk]['b']
        ey, ex = (wy * scl).shift(1).fillna(0) * ks, (wx * scl).shift(1).fillna(0) * ks
        gp = ey.shift(1).fillna(0) * R[a].reindex(idx) + ex.shift(1).fillna(0) * R[b].reindex(idx)
        per[kk] = gp - (ey.diff().abs().fillna(0) + ex.diff().abs().fillna(0)) * (COST_BPS + SLIP_BPS) / 1e4
    extras = dict(P=P, per=pd.DataFrame(per), k=pd.Series(kser, index=idx), active=active, idle=idle,
                  equity_w=e_tot, gross=pd.Series(np.abs(EXW).sum(1), index=idx), log=pd.DataFrame(log))
    return pa, extras
