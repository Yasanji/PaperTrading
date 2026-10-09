"""Sleeve B and Pod 4 universe, frozen at 5 October 2026 (PREREGISTRATION.md s.2): STOXX Europe 600 from
pairs/part2/stoxx600_constituents.csv with the suffixes of pairs/part2/get600.py; S&P 500 and Hang Seng from the
last Wikipedia revision on or before 5 October 2026. Writes data/universe.csv (yahoo, region, name)."""
import io, requests, pandas as pd
H = {'User-Agent': 'PaperTrading research (yasanji)'}
SUF = {'United Kingdom': '.L', 'France': '.PA', 'Germany': '.DE', 'Switzerland': '.SW', 'Netherlands': '.AS', 'Spain': '.MC',
       'Italy': '.MI', 'Sweden': '.ST', 'Denmark': '.CO', 'Finland': '.HE', 'Norway': '.OL', 'Belgium': '.BR', 'Austria': '.VI',
       'Ireland': '.IR', 'Portugal': '.LS', 'Poland': '.WA', 'Luxembourg': '.AS', 'Greece': '.AT'}
REV = {'sp': ('wiki_sp500_1376729338.html', '1376729338, 25 September 2026'), 'hk': ('wiki_hsi_1377881667.html', '1377881667, 1 October 2026')}
def wiki(k):   # last revision on or before 5 October 2026, saved as HTML (the Wikipedia API rate-limits this workspace)
    f, rev = REV[k]; return pd.read_html(io.StringIO(open('data/' + f).read())), rev
s = pd.read_csv('../../pairs/part2/stoxx600_constituents.csv')
eu = pd.DataFrame(dict(yahoo=[str(k).strip().replace(' ', '-').replace('.', '-') + SUF.get(c, '?') for k, c in zip(s.Ticker, s.Country)],
                       region='EU', name=s.Company)); eu = eu[~eu.yahoo.str.endswith('?')]
tb, r1 = wiki('sp'); sp = tb[0]
us = pd.DataFrame(dict(yahoo=sp.Symbol.str.replace('.', '-', regex=False), region='US', name=sp.Security))
tb, r2 = wiki('hk'); hs = next(t for t in tb if any('Ticker' in str(c) or 'Code' in str(c) for c in t.columns) and len(t) > 50)
col = next(c for c in hs.columns if 'Ticker' in str(c) or 'Code' in str(c))
code = hs[col].astype(str).str.extract(r'(\d{1,5})')[0].dropna().astype(int)
hk = pd.DataFrame(dict(yahoo=[f'{c:04d}.HK' for c in code], region='HK', name=hs.loc[code.index, hs.columns[1]].values))
u = pd.concat([eu, us, hk]).drop_duplicates('yahoo'); u.to_csv('data/universe.csv', index=False)
print(len(eu), len(us), len(hk), '| S&P revision', r1, '| Hang Seng revision', r2)
