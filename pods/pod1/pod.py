"""Pod 1: systematic macro. Trend (60% of the pod's risk), G10 currency carry (20%) and Sleeve C, month-end rebalancing
(20%, rebal/SLEEVE_C_PREREGISTRATION.md, pods/pod1/sleeve_c.py), in micro futures.

Trend (pairs/part4/trend_dev.py, portfolio amendment 10.1): each Friday, the 12-month return divided by the 12-month
volatility (z). Long if z > 0.25, short if z < -0.25; inside the band the existing direction is kept. Size: whole
contracts for the market's target risk (contract check), risk per contract = notional x 63-day volatility.
Carry (carry/sleeveA/PREREGISTRATION.md, amendment 10.2): at each month-end, carry = three-month rate minus the US rate,
previous month's averages (OECD; SONIA for sterling after February 2026). Long the three highest, short the three
lowest of the seven currencies with futures, each sized for equal risk.
Markets in the contract check marked LEFT OUT are not traded (amendment 10.4).

Interface (DESIGN.md s.3): targets(as_of, prices, rates, previous) -> {local symbol root: contracts}, status(), checks()."""
import io, math, numpy as np, pandas as pd, requests
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'book')); import config as C

CC = pd.read_csv(C.CONTRACTS)
TRADED = CC[CC.verdict.str.startswith('TRADED')]
TREND = TRADED[TRADED.use.str.contains('trend')].set_index('found')
CARRY = TRADED[TRADED.use.str.contains('carry')].set_index('found')
CARRY_CCY = {'M6E': 'EA20', 'MJY': 'JPN', 'M6B': 'GBR', 'MSF': 'CHE', 'M6A': 'AUS', 'MCD': 'CAN', 'NZD': 'NZL'}
TREND_TARGET = float(CC[CC.use.str.startswith('trend')].target_risk.iloc[0]) * C.TREND_SHARE / C.CHECK_SHARES[0]   # contract check, rescaled to the current split
CARRY_TARGET = float(CC[CC.use == 'carry'].target_risk.iloc[0]) * C.CARRY_SHARE / C.CHECK_SHARES[1]
BAND = 0.25


def zscore(px):
    r = px.pct_change()
    return (px.iloc[-1] / px.iloc[-253] - 1) / (r.iloc[-252:].std() * math.sqrt(252))


def risk_per_contract(px, mult):
    return px.iloc[-1] * mult * px.pct_change().iloc[-63:].std() * math.sqrt(252)


def trend(prices, previous_sign):
    out = {}
    for sym, row in TREND.iterrows():
        p = prices.get(sym)
        if p is None or len(p.dropna()) < 260: continue
        p = p.dropna(); z = zscore(p); prev = previous_sign.get(sym, 0)
        sign = 1 if z > BAND else -1 if z < -BAND else prev
        exact = TREND_TARGET / risk_per_contract(p, row.multiplier)
        out[sym] = dict(sign=sign, z=round(float(z), 3), exact=float(exact))
    return out


CACHE = os.path.join(C.ROOT, 'delta1', 'oecd_rates_cache.csv')


def oecd_rates(start='2025-01'):
    """OECD three-month rates (SONIA for sterling). Cached; if the OECD or the Bank of England does not answer within
    30 seconds, the last cached table is used and the run says so. Rates are monthly, so a day-old cache is enough."""
    try:
        w = _oecd_rates(start); w.to_csv(CACHE); return w
    except Exception as e:
        if os.path.exists(CACHE):
            print(f'rates: download failed ({type(e).__name__}); using cache from {pd.Timestamp(os.path.getmtime(CACHE), unit="s").date()}')
            return pd.read_csv(CACHE, index_col=0)
        raise


def _oecd_rates(start):
    u = ('https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/'
         f'{"+".join(set(CARRY_CCY.values()) | {"USA"})}.M.IR3TIB.PA.....?startPeriod={start}&format=csvfilewithlabels')
    d = pd.read_csv(io.StringIO(requests.get(u, timeout=30).text))
    w = d.pivot_table(index='TIME_PERIOD', columns='REF_AREA', values='OBS_VALUE')
    s = sonia_monthly(); s.index = s.index.strftime('%Y-%m')            # sterling: SONIA after the OECD series ends
    w['GBR'] = w.get('GBR', pd.Series(dtype=float)).combine_first(s.reindex(w.index))
    return w


def sonia_monthly():
    u = ('https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/2025&Dateto=now'
         '&SeriesCodes=IUDSOIA&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N')
    d = pd.read_csv(io.StringIO(requests.get(u, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30).text))
    d['DATE'] = pd.to_datetime(d.DATE, format='%d %b %Y')
    return d.set_index('DATE').IUDSOIA.resample('MS').mean()


def carry(prices, rates, as_of):
    """rates: monthly table (index 'YYYY-MM', columns OECD codes). Uses the month before as_of's month."""
    m = (pd.Timestamp(as_of).to_period('M') - 1).strftime('%Y-%m')
    known = rates[rates.index <= m].ffill()                  # latest published month at or before m, per currency
    if known.empty: return {}
    row = known.iloc[-1]; c = {s: row[k] - row['USA'] for s, k in CARRY_CCY.items() if pd.notna(row.get(k))}
    if len(c) < 6: return {}
    ranked = sorted(c, key=c.get); out = {}
    for s in ranked[:3] + ranked[-3:]:
        p = prices.get(s)
        if p is None: continue
        sign = 1 if s in ranked[-3:] else -1
        out[s] = dict(sign=sign, carry=round(float(c[s]), 3), exact=float(CARRY_TARGET / risk_per_contract(p.dropna(), CARRY.loc[s].multiplier)))
    return out


def targets(as_of, prices, rates, previous_sign=None, scale=None, sleeve=None):
    """Contracts per market (trend, carry and Sleeve C netted), before the book's band and holding rules.
    sleeve: output of sleeve_c.targets(); its whole contracts are added after trend and carry are rounded (s.4.4)."""
    scale = C.SCALE[1] if scale is None else scale
    t, k = trend(prices, previous_sign or {}), carry(prices, rates, as_of)
    sc = {m: (sleeve or {}).get(m, 0) for m in ('MES', 'ZN')}; sp = {m: (sleeve or {}).get(m + '_prev', 0) for m in ('MES', 'ZN')}
    rows = []
    for sym in sorted(set(t) | set(k) | {m for m in sc if sc[m] or sp[m]}):
        e = t.get(sym, {}).get('sign', 0) * t.get(sym, {}).get('exact', 0) + k.get(sym, {}).get('sign', 0) * k.get(sym, {}).get('exact', 0)
        e *= scale
        n = int(math.copysign(max(1, round(abs(e))), e)) if abs(e) >= 0.5 else 0       # half-contract rule (s.3.8)
        rows.append(dict(market=sym, trend_sign=t.get(sym, {}).get('sign'), trend_z=t.get(sym, {}).get('z'),
                         carry_sign=k.get(sym, {}).get('sign'), exact=round(e, 2), contracts=n + sc.get(sym, 0),
                         sleeve_c=sc.get(sym, 0), sleeve_c_prev=sp.get(sym, 0)))
    return pd.DataFrame(rows)


def status():
    return dict(pod=1, stage='incubation', scale=C.SCALE[1])


def checks(prices, as_of):
    stale = [s for s in set(TREND.index) | set(CARRY.index) if s not in prices or prices[s].dropna().index[-1] < pd.Timestamp(as_of) - pd.tseries.offsets.BDay(1)]
    return [f'stale or missing prices: {", ".join(sorted(stale))}'] if stale else []
