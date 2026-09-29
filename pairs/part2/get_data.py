import yfinance as yf, pandas as pd, pickle
NAMES = ['ADS.DE','ADYEN.AS','AD.AS','AI.PA','AIR.PA','ALV.DE','ABI.BR','ARGX.BR',
         'ASML.AS','CS.PA','BAS.DE','BAYN.DE','BBVA.MC','SAN.MC','BMW.DE','BNP.PA',
         'BN.PA','DBK.DE','DB1.DE','DHL.DE','DTE.DE','ENEL.MI','ENI.MI','EL.PA',
         'RACE.MI','RMS.PA','IBE.MC','ITX.MC','IFX.DE','INGA.AS','ISP.MI','OR.PA',
         'MC.PA','MBG.DE','MUV2.DE','NDA-FI.HE','PRX.AS','RHM.DE','SAF.PA','SGO.PA',
         'SAN.PA','SAP.DE','SU.PA','SIE.DE','ENR.DE','TTE.PA','DG.PA','UCG.MI',
         'VOW.DE','WKL.AS']
S, E = '2021-09-27', '2026-09-25'
px, bad = {}, []
for s in NAMES:
    try:
        d = yf.download(s, start=S, end=E, auto_adjust=False, progress=False)['Adj Close'].squeeze().dropna().rename(s)
        if len(d) < 250: bad.append((s, len(d)))
        px[s] = d
    except Exception as ex:
        bad.append((s, str(ex)[:60]))
idx = {t: yf.download(t, start=S, end=E, progress=False)['Close'].squeeze().dropna() for t in ['^GSPC','^STOXX50E']}
pickle.dump({'px': px, 'NAMES': NAMES, 'idx': idx}, open('data.pkl','wb'))
print('names:', len(px), 'problems:', bad)
for s in ['SAF.PA','SIE.DE']: print(s, px[s].index[0].date(), px[s].index[-1].date(), len(px[s]))
for t,v in idx.items(): print(t, v.index[0].date(), v.index[-1].date(), len(v))
