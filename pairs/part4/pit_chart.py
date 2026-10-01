"""Chart the three timings from pit_bt.py (run that first)."""
import pickle, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.dates as mdates
R = pickle.load(open('pit_results.pkl', 'rb')); fig, ax = plt.subplots(figsize=(10, 5.6))
for k, c, ls in [('Tuesday (hindsight)', '#E07B39', '--'), ('Friday close (earliest possible)', '#2F6FD0', '-'), ('Monday close (cautious)', '#B8B8B0', '-')]:
    cum = R[k]['_wk'].cumsum() * 100; ax.plot(cum.index.to_timestamp(), cum.values, color=c, ls=ls, lw=2.2, label=f'{k}  {cum.iloc[-1]:+.1f}%')
ax.axhline(0, color='#999', lw=1); ax.legend(frameon=False); ax.set_ylabel('Cumulative % of capital')
ax.set_title('The same signal, dated to when it was known'); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
fig.tight_layout(); fig.savefig('pit_demo_cot_timing.png', dpi=200)
