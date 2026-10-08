"""Back-check the STOXX 600 ranking on the September 2026 review (rank date 31 August 2026).
Membership before the review = current members minus September additions plus September deletions."""
import pandas as pd, numpy as np
u = pd.read_csv('data/stoxx600_rank.csv'); p = pd.read_pickle('../pod3_msci/data/prices.pkl').ffill()
ADD = ['NATIONAL BANK OF GREECE', 'ENDEAVOUR', 'EUROBANK', 'PIRAEUS', 'ALPHA BANK', 'PUBLIC POWER', 'METLEN', 'GEK TERNA',
       'MOTOR OIL', 'ROSEBANK', 'XTB', 'SOFTCAT', 'EASYJET', 'JUMBO']
DEL = ['KONGSBERG MARITIME', 'FRAPORT', 'JD SPORTS', 'WIENERBERGER', 'BAKKAFROST', 'TAURON', 'BUCHER', 'AUMOVIO', 'VISCOFAN',
       'THULE', 'KEMIRA', 'WIHLBORGS', 'SIGNIFY', 'SES']
def hit(n, keys): return next((k for k in keys if (k == 'SES' and str(n).upper().split()[0] == 'SES') or (k != 'SES' and k in str(n).upper())), None)
u['a'] = u['name'].map(lambda n: hit(n, ADD)); u['d'] = u['name'].map(lambda n: hit(n, DEL))
u['pre'] = (u.member & u.a.isna()) | u.d.notna()
r = (p.loc['2026-08-31'] / p.iloc[-1])                         # rank date: last trading day of August
u['ff_aug'] = u.ff_usd * u.symbol.map(r).fillna(1.0)
u = u.sort_values('ff_aug', ascending=False).reset_index(drop=True); u['rank_aug'] = u.index + 1
print('additions found in data:', sorted(u.a.dropna().unique())); print('deletions found in data:', sorted(u.d.dropna().unique()))
print(u[u.a.notna() | u.d.notna()][['rank_aug', 'name', 'pre', 'a', 'd']].to_string(index=False))
pa = u[~u.pre & (u.rank_aug <= 550)]; pdl = u[u.pre & (u.rank_aug > 750)]
print('\npredicted adds:', len(pa), 'right:', pa.a.notna().sum(), list(pa['name']))
print('predicted deletes:', len(pdl), 'right:', pdl.d.notna().sum(), list(pdl['name']))
import sys; from select600 import select
u['sel'] = select(u.rank_aug, u.pre)
pa = u[u.sel & ~u.pre]; pdl = u[~u.sel & u.pre]
act_d = u.d.notna().sum()
print('\nwith the 600 fill rule:')
print('predicted adds:', len(pa), 'right:', pa.a.notna().sum(), '| actual adds in data:', u.a.notna().sum())
print('predicted deletes:', len(pdl), 'right:', pdl.d.notna().sum(), '| actual deletes in data:', act_d)
print('wrong deletes:', list(pdl[pdl.d.isna()]['name'])); print('missed deletes:', list(u[u.d.notna() & u.sel]['name']))
print('wrong adds:', list(pa[pa.a.isna()]['name'])); print('missed adds:', list(u[u.a.notna() & ~u.sel]['name']))
