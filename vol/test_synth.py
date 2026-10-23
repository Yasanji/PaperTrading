"""Synthetic self-test: generate option prices from a KNOWN arbitrage-free SVI surface,
run them through the pipeline, and check it recovers the inputs. No network, no data noise.
"""
import math, datetime as dt
import numpy as np, pandas as pd
import bs, clean, forward, imply, svi, surface as surfmod

S, r, q = 600.0, 0.040, 0.015
as_of = dt.date(2026, 10, 23)
Ts = [0.08, 0.25, 0.50, 1.00]
# Known SVI slices (equity-like: negative rho = downside skew), calendar-increasing a.
TRUE = {T: dict(a=0.030 * T + 0.004, b=0.10 * math.sqrt(T) + 0.02,
                rho=-0.45, m=0.0, sigma=0.12) for T in Ts}

print("=== forward & inversion recovery (per expiry) ===")
slices, forwards, meta = [], {}, []
max_vol_err = 0.0
for T in Ts:
    F_true, D_true = S * math.exp((r - q) * T), math.exp(-r * T)
    p_true = TRUE[T]
    Ks = F_true * np.exp(np.linspace(-0.30, 0.30, 25))
    rows = []
    for K in Ks:
        sig = math.sqrt(svi.w(p_true, math.log(K / F_true)) / T)
        for right in ('C', 'P'):
            px = bs.black76_price(F_true, K, T, sig, D_true, right)
            rows.append(dict(expiry='x', strike=K, right=right, bid=px, ask=px,
                             last=px, volume=1, open_interest=1, mid=px))
    edf = pd.DataFrame(rows)
    calls = {r_.strike: r_.mid for r_ in edf[edf.right == 'C'].itertuples()}
    puts = {r_.strike: r_.mid for r_ in edf[edf.right == 'P'].itertuples()}
    F, D, n = forward.implied_forward(calls, puts)
    quotes, _ = clean.select_otm(edf, F, D)
    tv = imply.slice_total_variance(quotes, F, D, T)
    k = np.array([x['k'] for x in tv]); w = np.array([x['w'] for x in tv])
    vega = np.array([x['vega'] for x in tv])
    p, rmse, arb = svi.fit_slice(k, w, vega, T)
    # recovered vs true vol over the fitted strikes
    verr = max(abs(math.sqrt(svi.w(p, kk) / T) - math.sqrt(svi.w(p_true, kk) / T)) for kk in k)
    max_vol_err = max(max_vol_err, verr)
    print(f"T={T:.2f}  F recov {F:.3f} (true {F_true:.3f})  D {D:.5f} (true {D_true:.5f})  "
          f"rmse {rmse:.4f}vp  max_vol_err {verr*100:.4f}vp  arb_ok {arb}")
    slices.append((T, p)); forwards[T] = (F, D)
    meta.append({'T': T, 'params': p})

print(f"\nworst vol recovery error across all slices: {max_vol_err*100:.4f} vol points")

print("\n=== surface checks ===")
slices, nfix = svi.enforce_calendar(slices)
surface = surfmod.Surface(S, slices, forwards, str(as_of), 'TEST')
kg = np.linspace(-0.6, 0.4, 120)
fly = all(svi.butterfly_ok(p, kg) for _, p in slices)
cal = all(np.all(svi.w(slices[i-1][1], kg) - svi.w(slices[i][1], kg) <= 1e-6) for i in range(1, len(slices)))
print(f"butterfly arb-free: {fly}   calendar arb-free: {cal}   calendar fixes: {nfix}")

print("\n=== greeks: put-call delta parity should equal exp(-qT) ===")
for T in Ts:
    F, D = forwards[T]
    K = F
    gc = surface.greeks(K, T, 'C'); gp = surface.greeks(K, T, 'P')
    print(f"T={T:.2f}  callΔ-putΔ={gc['delta']-gp['delta']:.5f}  exp(-qT)={math.exp(-q*T):.5f}  "
          f"vega(C)={gc['vega']:.4f} vega(P)={gp['vega']:.4f}")

print("\n=== desk views ===")
for T in Ts:
    print(f"T={T:.2f}  atm_vol {surface.atm_vol(T)*100:.2f}  25dRR {surface.risk_reversal(T)*100:+.2f}  "
          f"25dBF {surface.butterfly(T)*100:+.2f}  skew {surface.skew(T):+.4f}")
print(f"\nfwd vol {Ts[0]:.2f}->{Ts[-1]:.2f}: {surface.forward_vol(Ts[0], Ts[-1])*100:.2f}")
