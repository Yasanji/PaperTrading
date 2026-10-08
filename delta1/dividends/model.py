"""EURO STOXX 50 index dividend points: realised and expected for the current dividend-futures year, and a forecast
for the next one, flat and bottom-up.

Index points from a dividend D of company i = D * k_i, where k_i = index weight_i * index level / price_i
(index shares per divisor point, constant between reviews). Futures years run from the Monday after the third Friday
of December to the third Friday of December. Bottom-up amounts for the largest contributors are in dps_inputs.csv;
all other companies repeat their last 12 months of payments, grown by `g_rest`.
Usage: python model.py [g_rest]"""
import io, sys, time, datetime as dt, requests, pandas as pd, yfinance as yf

H = {'User-Agent': 'Mozilla/5.0'}
HERE = __file__.rsplit('/', 1)[0] if '/' in __file__ else '.'
FIX = {'L AIR LIQUIDE': 'AI.PA', 'L OREAL S.A.': 'OR.PA'}


def third_friday(y):
    d = dt.date(y, 12, 15)
    return pd.Timestamp(d + dt.timedelta(days=(4 - d.weekday()) % 7))


def members():
    """Constituents and weights from the Xtrackers EURO STOXX 50 fund (LU0380865021); loyalty-share lines merged."""
    raw = requests.get('https://etf.dws.com/etfdata/export/GBR/ENG/excel/product/constituent/LU0380865021/', headers=H, timeout=90).content
    d = pd.read_excel(io.BytesIO(raw), header=None); hdr = next(k for k in range(10) if 'ISIN' in [str(v) for v in d.iloc[k]])
    h = pd.read_excel(io.BytesIO(raw), header=hdr).dropna(subset=['ISIN'])
    h = h[(h['Type of Security'] == 'Equities') & (h.Name != '-')]
    sym = []
    for _, r in h.iterrows():
        s = FIX.get(r.Name)
        if s is None:
            q = yf.Search(r.ISIN, max_results=1).quotes; s = q[0]['symbol'] if q else None; time.sleep(0.5)
        sym.append('NDA-FI.HE' if s == 'NDA-SE.ST' else s)
    h['symbol'] = sym
    m = h.dropna(subset=['symbol']).groupby('symbol', as_index=False).agg(name=('Name', 'first'), weight=('Weighting', 'sum'))
    m['weight'] /= m.weight.sum()
    return m


def run(g_rest=0.05, today=None):
    today = pd.Timestamp(today or dt.date.today())
    y = today.year if today <= third_friday(today.year) else today.year + 1
    cur = (third_friday(y - 1), third_friday(y)); nxt = (third_friday(y), third_friday(y + 1))
    m = members()
    px = yf.download(m.symbol.tolist() + ['^STOXX50E'], period='5d', progress=False, auto_adjust=False)['Close'].ffill().iloc[-1]
    L = px['^STOXX50E']; m['k'] = m.weight * L / m.symbol.map(px)
    rows = []
    for s in m.symbol:
        for _ in range(3):
            try: d = yf.Ticker(s).dividends; break
            except Exception: time.sleep(5)
        d.index = d.index.tz_localize(None)
        rows += [dict(symbol=s, ex=ex, amount=float(a)) for ex, a in d[d.index >= today - pd.DateOffset(years=2)].items()]
    dv = pd.DataFrame(rows).merge(m[['symbol', 'k']], on='symbol'); dv['points'] = dv.amount * dv.k
    realised = dv[(dv.ex > cur[0]) & (dv.ex <= today)]
    ly = dv[(dv.ex > today - pd.DateOffset(years=1)) & (dv.ex <= cur[1] - pd.DateOffset(years=1))].copy()
    ly['ex'] += pd.DateOffset(years=1); rest = ly[ly.ex > today]
    base = pd.concat([dv[(dv.ex > today - pd.DateOffset(years=1)) & (dv.ex <= today)], rest]).copy()
    base['ex'] += pd.DateOffset(years=1); base = base[(base.ex > nxt[0]) & (base.ex <= nxt[1])]
    flat = base.groupby('symbol').points.sum()
    inp = pd.read_csv(f'{HERE}/dps_inputs.csv').set_index('symbol')
    bu = flat * (1 + g_rest)
    for s, r in inp.iterrows():
        if s in m.set_index('symbol').index:
            bu[s] = sum(float(x) for x in str(r.payments_2027).split(';')) * m.set_index('symbol').k[s]
    out = pd.DataFrame(dict(flat=flat, bottom_up=bu)).fillna(0.0)
    summary = dict(as_of=today.date().isoformat(), index_level=float(L), current_year=y,
                   current_realised=float(realised.points.sum()), current_expected=float(realised.points.sum() + rest.points.sum()),
                   next_flat=float(out.flat.sum()), next_bottom_up=float(out.bottom_up.sum()), g_rest=g_rest)
    return summary, out, m


if __name__ == '__main__':
    s, out, _ = run(float(sys.argv[1]) if len(sys.argv) > 1 else 0.05)
    for k, v in s.items(): print(f'{k}: {v:.3g}' if isinstance(v, float) else f'{k}: {v}')
    print(out.sort_values('bottom_up', ascending=False).head(16).round(2).to_string())
