"""MSCI Europe Standard index: predict additions and deletions at an Index Review.

Rules from the MSCI GIMI Methodology, August 2026 (full Index Review, not a light rebalancing):
  - Global Minimum Size Reference (GMSR) for DM Standard; Global Minimum Size Range = 0.5 to 1.15 times GMSR (s. 2.3.2).
  - Market Size-Segment Cutoff (per market) = full market cap of the company ranked at the market's
    Segment Number of Companies, kept within the Global Minimum Size Range (s. 3.1.4).
  - Existing Standard constituents stay while full market cap >= 2/3 of the cutoff (s. 3.1.5.1).
  - Small Cap constituents migrate up when full market cap >= 1.5 times the cutoff (upper buffer).
  - Free float market cap must be >= 50% of the cutoff (bounded by the range) for new constituents,
    and >= 2/3 of that for existing ones; 1.8 times for FIF < 0.15 (s. 2.3.6.1, 3.1.6.2).
Not modelled: liquidity (ATVR), foreign room, the coverage-target adjustment to the number of companies,
corporate events, IPOs outside the Small Cap index, extreme price increase rule.
"""
import numpy as np, pandas as pd

CCY_MARKET = {'GBP': 'UK', 'GBp': 'UK', 'CHF': 'CH', 'SEK': 'SE', 'DKK': 'DK', 'NOK': 'NO'}
DOM_MARKET = {'Austria': 'AT', 'Belgium': 'BE', 'Finland': 'FI', 'France': 'FR', 'Germany': 'DE', 'Ireland': 'IE',
              'Italy': 'IT', 'Netherlands': 'NL', 'Portugal': 'PT', 'Spain': 'ES'}
EXCH_MARKET = {'Euronext Paris': 'FR', 'XETRA': 'DE', 'Milan Stock Exchange': 'IT', 'Mercado Continuo Espana': 'ES',
               'Euronext Amsterdam': 'NL', 'Euronext Brussels': 'BE', 'Helsinki Stock Exchange': 'FI',
               'Euronext Lisbon': 'PT', 'Vienna Stock Exchange': 'AT', 'Irish Stock Exchange': 'IE'}
MARKETS = ['AT', 'BE', 'CH', 'DE', 'DK', 'ES', 'FI', 'FR', 'IE', 'IT', 'NL', 'NO', 'PT', 'SE', 'UK']


def market(r):
    if r.currency in CCY_MARKET: return CCY_MARKET[r.currency]
    if r.currency == 'USD': return {'United Kingdom': 'UK', 'Switzerland': 'CH', 'Netherlands': 'NL'}.get(r.domicile, 'UK')
    if r.domicile in DOM_MARKET: return DOM_MARKET[r.domicile]
    return EXCH_MARKET.get(r.exchange, DOM_MARKET.get(r.domicile))


def company_key(r):
    """Share classes of one company share a name stem (ATLAS COPCO AB A / B, LINDT REG / PC)."""
    w = [x for x in str(r['name']).upper().replace('.', ' ').split() if x not in ('THE', 'L', 'AB', 'AG', 'AS', 'A/S', 'SA', 'SE', 'PLC', 'NV', 'N', 'V', 'ASA', 'OYJ', 'SPA', 'S', 'P', 'A', 'B', 'D', 'SHS', 'SHARES', 'SHRS', 'REG', 'PC')]
    return ' '.join(w[:2])


def companies(u, fx):
    """One row per company: full and free float market cap in USD billions, segment, market."""
    u = u.copy()
    u['market'] = u.apply(market, axis=1)
    u = u[u.market.isin(MARKETS)]
    ccy = u.y_ccy.replace({'GBp': 'GBP', 'ZAc': 'ZAR', 'ILA': 'ILS'})
    u['full_usd'] = u.mcap.where(u.mcap > 0) * ccy.map(fx) / 1e9
    sh = u.implied_shares.fillna(u.shares)
    u['fif'] = (u.float_shares / sh).clip(0, 1)
    u['ff_yahoo'] = u.full_usd * u.fif
    if 'fund' not in u: u['fund'] = u.segment
    for seg in ['STANDARD', 'SMALL']:                      # fund weights are MSCI free-float weights; scale them to USD
        k = u.fund == seg
        u.loc[k, 'ff_usd'] = u.loc[k, 'weight'] * (u.loc[k, 'ff_yahoo'] / u.loc[k, 'weight']).median()
    u['fif'] = (u.ff_usd / u.full_usd).clip(0, 1)
    u['key'] = u.apply(company_key, axis=1)
    g = u.sort_values('weight', ascending=False).groupby(['market', 'key'], as_index=False).agg(
        name=('name', 'first'), isin=('isin', 'first'), symbol=('symbol', 'first'), segment=('segment', 'first'),
        full_usd=('full_usd', 'max'), ff_usd=('ff_usd', 'max'), fif=('fif', 'max'))
    return g


def predict(c, gmsr, coverage_adjust=False):
    lo, hi = 0.5 * gmsr, 1.15 * gmsr
    out, cuts = [], []
    for mk, d in c.groupby('market'):
        d = d.dropna(subset=['full_usd']).sort_values('full_usd', ascending=False).reset_index(drop=True)
        n0 = int((d.segment == 'STANDARD').sum()); tot = d.ff_usd.sum() / 0.99   # IMI covers ~99% of the market
        cov = lambda k: d.ff_usd.iloc[:k].sum() / tot
        n = n0
        if coverage_adjust and cov(n0) > 0.90:                                # too much coverage: cut the number of companies, 5% then 20% limits
            for lim in (0.05, 0.20):
                ks = [k for k in range(n0, int(np.floor(n0 * (1 - lim))) - 1, -1) if k >= 1 and cov(k) <= 0.90]
                if ks: n = ks[0]; break
                n = max(1, int(np.ceil(n0 * (1 - lim))))
        elif coverage_adjust and cov(n0) < 0.80:                              # too little coverage: add companies
            ks = [k for k in range(n0, min(len(d), int(np.ceil(n0 * 1.2))) + 1) if cov(k) >= 0.80]
            n = ks[0] if ks else min(len(d), int(np.ceil(n0 * 1.2)))
        raw = d.full_usd.iloc[n - 1] if n else np.nan
        cut = min(max(raw, lo), hi)
        ffmin = 0.5 * cut
        cuts.append(dict(market=mk, n_now=n0, n_target=n, coverage=cov(n), raw_cutoff=raw, cutoff=cut, lower_buffer=2 / 3 * cut, upper_buffer=1.5 * cut))
        for _, r in d.iterrows():
            ffreq = ffmin * (1.8 if (r.fif == r.fif and r.fif < 0.15) else 1.0)
            if r.segment == 'STANDARD':
                if r.full_usd < 2 / 3 * cut:
                    out.append(dict(r, change='DELETE', rule='full mcap < 2/3 cutoff', margin=r.full_usd / (2 / 3 * cut), cutoff=cut))
                elif r.ff_usd < 2 / 3 * ffreq:
                    out.append(dict(r, change='DELETE', rule='free float < 2/3 of minimum', margin=r.ff_usd / (2 / 3 * ffreq), cutoff=cut))
            else:
                if r.full_usd >= 1.5 * cut and r.ff_usd >= ffreq:
                    out.append(dict(r, change='ADD', rule='full mcap >= 1.5 x cutoff and free float >= minimum', margin=r.full_usd / (1.5 * cut), cutoff=cut))
    return pd.DataFrame(out), pd.DataFrame(cuts)


def near_misses(c, cuts, band=0.15):
    """Stocks within band of a threshold, for the watch list."""
    c = c.merge(cuts[['market', 'cutoff']], on='market')
    c['ratio'] = np.where(c.segment == 'STANDARD', c.full_usd / (2 / 3 * c.cutoff), c.full_usd / (1.5 * c.cutoff))
    return c[(c.ratio > 1 - band) & (c.ratio < 1 + band)].sort_values('ratio')
