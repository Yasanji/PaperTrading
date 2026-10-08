"""Fill names Yahoo cannot find by ISIN, using hand-checked tickers. Usage: python fill_symbols.py CSV"""
import sys, time, pandas as pd, yfinance as yf
f = sys.argv[1]; m = pd.read_csv(f)
SYM = {'ALLIANZ SE REG': 'ALV.DE', 'L AIR LIQUIDE': 'AI.PA', 'L OREAL S.A.': 'OR.PA', 'ASSA ABLOY AB B': 'ASSA-B.ST', 'KBC GROUP NV': 'KBC.BR',
 'ATLAS COPCO AB B SHS': 'ATCO-B.ST', 'PUBLICIS GROUPE': 'PUB.PA', 'HALMA PLC': 'HLMA.L', 'EURONEXT NV': 'ENX.PA', 'CARLSBERG AS B': 'CARL-B.CO',
 'INTERTEK GROUP PLC': 'ITRK.L', 'AGEAS': 'AGS.BR', 'GEA GROUP AG': 'G1A.DE', 'CONTINENTAL AG': 'CON.DE', 'RAIFFEISEN BANK INTERNATIONA': 'RBI.VI',
 'KESKO OYJ B SHS': 'KESKOB.HE', 'FRESNILLO PLC': 'FRES.L', 'ALSTOM': 'ALO.PA', 'GJENSIDIGE FORSIKRING ASA': 'GJF.OL', 'VAR ENERGI ASA': 'VAR.OL',
 'VERBUND AG': 'VER.VI', 'NKT A/S': 'NKT.CO', 'SAIPEM SPA': 'SPM.MI', 'SSAB AB   B SHARES': 'SSAB-B.ST', 'CRODA INTERNATIONAL PLC': 'CRDA.L',
 'BECHTLE AG': 'BC8.DE', 'KONGSBERG MARITIME ASA': 'KMAR.OL', 'K S AG REG': 'SDF.DE', 'VIENNA INSURANCE GROUP AG': 'VIG.VI', 'PUMA SE': 'PUM.DE',
 'HEXPOL AB': 'HPOL-B.ST', 'PER AARSLEFF HOLDING A/S': 'PAAL-B.CO', 'WACKER CHEMIE AG': 'WCH.DE', 'BREMBO N.V.': 'BRE.MI', 'LANXESS AG': 'LXS.DE',
 'SAF HOLLAND SE': 'SFQ.DE', 'INVESTOR AB B SHS': 'INVE-B.ST'}
n = 0
for i in m.index[m.mcap.isna() & m['name'].isin(SYM)]:
    s = SYM[m.at[i, 'name']]
    try:
        x = yf.Ticker(s).fast_info                      # chart-based; works when the quote endpoint is rate-limited
        if x['marketCap']:
            pen = 100 if x['currency'] == 'GBp' else 1     # fast_info reports UK market cap in pence
            for c, v in dict(symbol=s, mcap=x['marketCap'] / pen, y_ccy=x['currency'], shares=x['shares']).items(): m.at[i, c] = v
            n += 1
    except Exception as e: print(s, e)
    time.sleep(1)
m.to_csv(f, index=False); print('filled', n)
