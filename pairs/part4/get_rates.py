"""Interest-rate data for the carry test: US Treasury daily yield curve (3-month, 2-, 10- and 30-year) and OECD three-month interbank rates.
FRED republishes both; these are the original publishers, used because FRED was unavailable when the test was run."""
import io, pickle, requests, pandas as pd
H = {'User-Agent': 'Mozilla/5.0'}
frames = []
for y in range(2004, 2027):
    u = (f'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/{y}/all'
         f'?type=daily_treasury_yield_curve&field_tdr_date_value={y}&page&_format=csv')
    r = requests.get(u, headers=H, timeout=60)
    if r.status_code == 200 and 'Date' in r.text[:50]: frames.append(pd.read_csv(io.StringIO(r.text)))
t = pd.concat(frames); t['Date'] = pd.to_datetime(t['Date']); t = t.set_index('Date').sort_index()
pickle.dump(t[['3 Mo', '2 Yr', '10 Yr', '30 Yr']], open('msb/treasury.pkl', 'wb'))
u = ('https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/'
     'USA+EA20+JPN+GBR+AUS+CAN.M.IR3TIB.PA.....?startPeriod=2004-01')
r = requests.get(u, headers={**H, 'Accept': 'application/vnd.sdmx.data+csv; charset=utf-8'}, timeout=90)
open('msb/oecd_raw.csv', 'w').write(r.text)
print('Treasury', t.index[0].date(), '->', t.index[-1].date(), '| OECD rows', r.text.count('\n'))
