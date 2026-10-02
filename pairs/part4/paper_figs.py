import pickle, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.dates as mdates
plt.rcParams.update({'font.family': 'DejaVu Serif', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': '#333333', 'axes.labelcolor': '#111111', 'xtick.color': '#333333', 'ytick.color': '#333333'})
DARK, MID, LIGHT, ACC = '#111111', '#7A7A7A', '#C8C8C8', '#1F4E9C'; OUT = '/mnt/user-data/outputs/'
pct = matplotlib.ticker.FuncFormatter(lambda v, p: f'{v:.0f}%')
# Figure 1: development Sharpe ratios
P = pickle.load(open('msb/paper_stats.pkl', 'rb')); R = P['R'].sort_values('sharpe')
lab = {'Carry (interim)': 'Carry (currencies, bonds)*', 'Value proxy (equities)': 'Value proxy (equities)**'}
fig, ax = plt.subplots(figsize=(7.5, 4.6)); fig.subplots_adjust(left=0.33, right=0.95, top=0.97, bottom=0.13)
for i, (k, r) in enumerate(R.iterrows()):
    c = ACC if k == 'Futures trend' else (MID if k in ('Low volatility', 'Momentum') else LIGHT)
    ax.barh(i, r.sharpe, color=c, height=0.65); ax.text(r.sharpe + (0.02 if r.sharpe >= 0 else -0.02), i, f'{r.sharpe:.2f}', va='center', ha='left' if r.sharpe >= 0 else 'right', fontsize=9.5)
ax.axvline(0, color=DARK, lw=0.8); ax.set_yticks(range(len(R))); ax.set_yticklabels([lab.get(k, k) for k in R.index]); ax.tick_params(axis='y', length=0)
ax.set_xlim(-0.85, 1.0); ax.set_xlabel('Annualised Sharpe ratio, 2013\u20132022, after costs')
fig.savefig(OUT + 'paper_f1.png', dpi=220); plt.close(fig)
# Figure 2: cumulative returns 2008-2022
def series(pre, prek, dev, devk): return pd.concat([pickle.load(open(pre, 'rb'))[prek]['2008':'2012'], pickle.load(open(dev, 'rb'))[devk]['2013':'2022']])
S = [('Trend', series('msb/pre_trend.pkl', 'xs', 'msb/trend_dev_results.pkl', 'xs'), ACC, '-'),
     ('Low volatility', series('msb/pre_lowvol.pkl', 'vs', 'msb/lowvol_results.pkl', 'vs'), DARK, '--'),
     ('Momentum', series('msb/pre_mom.pkl', 'vs', 'msb/mom_results.pkl', 'vs'), MID, ':')]
fig, ax = plt.subplots(figsize=(7.5, 4.2)); fig.subplots_adjust(left=0.10, right=0.97, top=0.97, bottom=0.12)
ax.axvspan(pd.Timestamp('2008-01-01'), pd.Timestamp('2012-12-31'), color='#EFEFEF', zorder=0)
ax.text(pd.Timestamp('2008-04-01'), 0.95, 'Crisis-years check', transform=ax.get_xaxis_transform(), fontsize=9.5, color=MID)
ax.text(pd.Timestamp('2013-04-01'), 0.95, 'Development decade', transform=ax.get_xaxis_transform(), fontsize=9.5, color=MID)
for n, s, c, ls in S: ax.plot(s.index, ((1 + s).cumprod() - 1) * 100, color=c, ls=ls, lw=1.6, label=n)
ax.axhline(0, color=DARK, lw=0.6); ax.yaxis.set_major_formatter(pct); ax.set_ylabel('Cumulative return')
ax.xaxis.set_major_locator(mdates.YearLocator(2)); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y')); ax.legend(frameon=False, loc='lower right')
fig.savefig(OUT + 'paper_f2.png', dpi=220); plt.close(fig)
# Figure 3: Sharpe ratios with intervals and DSR
sr0 = P['sr0']; fig, ax = plt.subplots(figsize=(7.5, 4.8)); fig.subplots_adjust(left=0.30, right=0.84, top=0.92, bottom=0.12)
for i, (k, r) in enumerate(R.iterrows()):
    c = ACC if k == 'Futures trend' else DARK
    ax.plot([r.ci_low, r.ci_high], [i, i], color=c, lw=1.4); ax.plot(r.sharpe, i, 'o', color=c, ms=5)
    ax.text(1.68, i, f'{r.dsr:.2f}', va='center', fontsize=9.5)
ax.text(1.68, len(R) - 0.35, 'DSR', fontsize=9.5, fontweight='bold')
ax.axvline(0, color=DARK, lw=0.6); ax.axvline(sr0, color=DARK, lw=0.9, ls='--'); ax.text(sr0 + 0.03, 0.3, f'Expected maximum\nfrom ten trials: {sr0:.2f}', fontsize=8.5)
ax.set_yticks(range(len(R))); ax.set_yticklabels([lab.get(k, k) for k in R.index]); ax.tick_params(axis='y', length=0)
ax.set_xlim(-1.4, 1.6); ax.set_xlabel('Annualised Sharpe ratio with 95% block-bootstrap interval')
fig.savefig(OUT + 'paper_f3.png', dpi=220); plt.close(fig)
# Figure 4: timing of positioning data
T = pickle.load(open('pit_results.pkl', 'rb')); fig, ax = plt.subplots(figsize=(7.5, 4.0)); fig.subplots_adjust(left=0.10, right=0.97, top=0.97, bottom=0.12)
for k, lb, c, ls in [('Tuesday (hindsight)', 'Tuesday (date described; not tradable)', MID, '--'), ('Friday close (earliest possible)', 'Friday close (after publication)', ACC, '-'), ('Monday close (cautious)', 'Monday close', DARK, ':')]:
    cum = T[k]['_wk'].cumsum() * 100; ax.plot(cum.index.to_timestamp(), cum.values, color=c, ls=ls, lw=1.6, label=lb)
ax.axhline(0, color=DARK, lw=0.6); ax.yaxis.set_major_formatter(pct); ax.set_ylabel('Cumulative return, % of capital')
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y')); ax.legend(frameon=False, loc='lower left')
fig.savefig(OUT + 'paper_f4.png', dpi=220); plt.close(fig); print('ok')
