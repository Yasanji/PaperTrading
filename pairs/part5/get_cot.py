"""Download CFTC Commitments of Traders history (legacy, futures only) into cot/cot_all.pkl."""
import io, zipfile, os, requests, pandas as pd
os.makedirs('cot', exist_ok=True); frames = []
for y in range(2009, 2027):
    r = requests.get(f'https://www.cftc.gov/files/dea/history/deacot{y}.zip', headers={'User-Agent': 'Mozilla/5.0'})
    z = zipfile.ZipFile(io.BytesIO(r.content)); frames.append(pd.read_csv(z.open(z.namelist()[0]), low_memory=False)); print(y, 'ok')
pd.concat(frames).to_pickle('cot/cot_all.pkl')
