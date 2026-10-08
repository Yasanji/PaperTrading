"""STOXX Europe 600 review: rank by free float market cap and apply the 550/750 buffer.
Universe = current STOXX 600 (Xtrackers LU0328475792) plus MSCI Europe IMI names not in it.
Free float values: fund weights scaled to USD with Yahoo market values (STOXX weights for members, MSCI weights otherwise).
Usage: python rank600.py MSCI_UNIVERSE_CSV SXXP_XLSX PRICES_PKL OUTDIR"""
import sys, pandas as pd, numpy as np
msci = pd.read_csv(sys.argv[1]); p = pd.read_pickle(sys.argv[3]).ffill(); out = sys.argv[4]
d = pd.read_excel(sys.argv[2], header=None); hdr = next(k for k in range(10) if 'ISIN' in [str(v) for v in d.iloc[k]])
s = pd.read_excel(sys.argv[2], header=hdr).dropna(subset=['ISIN']); s = s[(s['Type of Security'] == 'Equities') & (s.Weighting > 1e-6)]
fx = {c: p[c + 'USD=X'].iloc[-1] for c in ['EUR', 'GBP', 'CHF', 'SEK', 'DKK', 'NOK']}; fx.update(USD=1.0)
msci['ccy'] = msci.y_ccy.replace({'GBp': 'GBP'}); msci['full_usd'] = msci.mcap.where(msci.mcap > 0) * msci.ccy.map(fx) / 1e9
for seg in ['STANDARD', 'SMALL']:                                   # MSCI free float from fund weights
    k = msci.segment == seg; msci.loc[k, 'ff_msci'] = msci.loc[k, 'weight'] * (msci.loc[k, 'full_usd'] * (msci.loc[k, 'float_shares'] / msci.loc[k, 'implied_shares'].fillna(msci.loc[k, 'shares'])).clip(0, 1) / msci.loc[k, 'weight']).median()
s = s.merge(msci[['isin', 'full_usd', 'float_shares', 'implied_shares', 'shares', 'symbol']], left_on='ISIN', right_on='isin', how='left')
scale = (s.full_usd * (s.float_shares / s.implied_shares.fillna(s.shares)).clip(0, 1) / s.Weighting).median()
s['ff_usd'] = s.Weighting * scale; s['member'] = True
import re
def stem(n):                                   # first significant word: share classes of one company share it
    w = [x for x in re.sub(r'[^A-Z0-9 ]', ' ', str(n).upper()).split() if len(x) > 2 and x not in ('THE', 'CLASS', 'PREF', 'PAR', 'SHS', 'SHARES', 'SHRS', 'REG', 'HOLDING', 'GROUP', 'KGAA', 'CHOCOLADEFABRIKEN', 'FASTIGHETS')]
    return w[0] if w else ''
member_stems = set(s.Name.map(stem))
msci['stem'] = msci['name'].map(stem)
nm = msci[~msci['isin'].isin(s.ISIN) & ~msci.stem.isin(member_stems)                 # other share classes of members
          & ~msci.exchange.astype(str).str.contains('NASDAQ|New York')]               # STOXX requires a European listing
nm = nm.rename(columns={'ff_msci': 'ff_usd'}); nm['member'] = False
u = pd.concat([s.rename(columns={'Name': 'name', 'ISIN': 'isin2'})[['name', 'isin', 'ff_usd', 'member', 'symbol']].assign(isin=s.ISIN),
               nm[['name', 'isin', 'ff_usd', 'member', 'symbol']]], ignore_index=True).dropna(subset=['ff_usd'])
u = u.sort_values('ff_usd', ascending=False).reset_index(drop=True); u['rank'] = u.index + 1
sys.path.insert(0, 'code'); sys.path.insert(0, '.'); from select600 import select
u['selected'] = select(u['rank'], u.member, n=int(u.member.sum()))   # keep the fund's line count (604: some companies have two lines)
add = u[u.selected & ~u.member]; dele = u[~u.selected & u.member]
u['call'] = np.select([u.selected & ~u.member, ~u.selected & u.member,
                       ~u.member & u['rank'].between(551, 600), u.member & u.selected & (u['rank'] > 560)],
                      ['ADD', 'DELETE', 'watch: add', 'watch: delete'], '')
print(f'members ranked: {u.member.sum()}; predicted additions {len(add)}, deletions {len(dele)}')
for c in ['ADD', 'DELETE', 'watch: add', 'watch: delete']:
    print(c); print(u[u.call == c][['rank', 'name', 'ff_usd']].round(2).head(15).to_string(index=False))
u[u.call != ''][['call', 'rank', 'name', 'isin', 'symbol', 'ff_usd', 'member']].round(3).to_csv(f'{out}/stoxx600_prediction.csv', index=False)
u.to_csv(f'{out}/stoxx600_rank.csv', index=False)
