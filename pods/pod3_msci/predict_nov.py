"""November 2026 MSCI Europe prediction. Usage: python predict_nov.py UNIVERSE_CSV PRICES_PKL OUTDIR [WINDOW_START WINDOW_END]
Decision rule (calibrated on the May and August 2026 reviews, fixed before November):
  delete if full mcap / (2/3 x cutoff) < 1.05 ; watch 1.05-1.20
  add    if full mcap / (1.5 x cutoff) >= 0.97 ; watch 0.85-0.97"""
import sys, pandas as pd, numpy as np
sys.path.insert(0, '.'); import model
u = pd.read_csv(sys.argv[1]); u['fund'] = u.segment; p = pd.read_pickle(sys.argv[2]).ffill(); out = sys.argv[3]
win = p.loc[sys.argv[4]:sys.argv[5]] if len(sys.argv) > 5 else p.iloc[-1:]
now = p.loc[:u.as_of.iloc[0]].iloc[-1]
u['mcap'] = u.mcap * u.symbol.map(win.mean() / now)
fx = {c: win[c + 'USD=X'].mean() for c in ['EUR', 'GBP', 'CHF', 'SEK', 'DKK', 'NOK']}; fx['USD'] = 1.0
gmsr = 16.28 * win['URTH'].mean() / p['URTH'].loc['2026-07-20']
c = model.companies(u, fx); _, cuts = model.predict(c, gmsr)
x = c.dropna(subset=['full_usd']).merge(cuts[['market', 'cutoff']], on='market')
x['ratio'] = np.where(x.segment == 'STANDARD', x.full_usd / (2 / 3 * x.cutoff), x.full_usd / (1.5 * x.cutoff))
x['call'] = np.select([(x.segment == 'STANDARD') & (x.ratio < 1.05), (x.segment == 'STANDARD') & (x.ratio < 1.20),
                       (x.segment == 'SMALL') & (x.ratio >= 0.97), (x.segment == 'SMALL') & (x.ratio >= 0.85)],
                      ['DELETE', 'watch: delete', 'ADD', 'watch: add'], '')
r = x[x.call != ''].sort_values(['call', 'ratio'])
cols = ['call', 'market', 'name', 'isin', 'symbol', 'full_usd', 'ff_usd', 'cutoff', 'ratio']
r[cols].round(3).to_csv(f'{out}/prediction.csv', index=False); cuts.round(3).to_csv(f'{out}/cutoffs.csv', index=False)
print(f'window {win.index[0].date()} to {win.index[-1].date()}; GMSR {gmsr:.2f}bn; range {0.5*gmsr:.2f} to {1.15*gmsr:.2f}bn')
print(r[cols].round(2).to_string(index=False))
