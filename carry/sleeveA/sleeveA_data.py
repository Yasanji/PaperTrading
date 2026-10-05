"""Sleeve A: download Bank of England exchange rates and OECD three-month rates."""
import io, requests, pandas as pd
H = {'User-Agent': 'Mozilla/5.0'}
codes = ['XUDLUSS', 'XUDLERS', 'XUDLJYS', 'XUDLSFS', 'XUDLCDS', 'XUDLADS', 'XUDLNDS', 'XUDLSKS', 'XUDLNKS', 'XUDLDMS']
u = ('https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp?csv.x=yes&Datefrom=01/Jan/1990&Dateto=now'
     f'&SeriesCodes={",".join(codes)}&CSVF=TN&UsingCodes=Y&VPD=Y&VFD=N')
d = pd.read_csv(io.StringIO(requests.get(u, headers=H, timeout=90).text)); d['DATE'] = pd.to_datetime(d.DATE, format='%d %b %Y'); d.to_pickle('boe_fx.pkl')
u = ('https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_FINMARK,4.0/'
     'AUS+CAN+CHE+DEU+GBR+JPN+NOR+NZL+SWE+USA+EA20.M.IR3TIB+IRLT.PA.....?startPeriod=1990-01&dimensionAtObservation=AllDimensions&format=csvfilewithlabels')
pd.read_csv(io.StringIO(requests.get(u, headers=H, timeout=120).text)).to_pickle('oecd_rates.pkl')
