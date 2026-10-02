import numpy as np, pandas as pd
MEMORY = 90          # second, disclosed run: the anchor adapts over about 90 days, matching the rolling anchor and the spread's reversion
def kalman(h, a, b, ve, memory=MEMORY):
    """Point-in-time Kalman filter on log prices: y = alpha_t + beta_t * x + e.
    State drift set so the level adapts over about MEMORY days: q_alpha = ve / MEMORY**2, q_beta scaled by the level of x."""
    y, x = np.log(h[a].values), np.log(h[b].values); n = len(y)
    th = np.zeros(2); P = np.eye(2)
    qa = ve / memory ** 2; Vw = np.diag([qa / np.mean(x ** 2), qa])
    z = np.full(n, np.nan); beta = np.full(n, np.nan)
    for t in range(n):
        R = P + Vw; xv = np.array([x[t], 1.0])
        yhat = xv @ th; Q = xv @ R @ xv + ve; e = y[t] - yhat
        z[t] = e / np.sqrt(Q); beta[t] = th[0]          # uses the state from the previous day only
        K = R @ xv / Q; th = th + K * e; P = R - np.outer(K, xv) @ R
    z[:60] = np.nan                                     # let the filter settle before trading
    return pd.Series(z, index=h.index), pd.Series(beta, index=h.index)
