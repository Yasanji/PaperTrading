"""Retry Yahoo lookups for rows missing a market cap, slowly, largest weights first, saving as it goes. Usage: python fill.py CSV"""
import sys, time, importlib.util, pandas as pd
f = sys.argv[1]
spec = importlib.util.spec_from_file_location('fx', __file__.replace('fill.py', 'fetch_info.py')); fx = importlib.util.module_from_spec(spec); spec.loader.exec_module(fx)
m = pd.read_csv(f)
for k in range(6):
    miss = m[m.mcap.isna()].sort_values('weight', ascending=False).index
    print('pass', k, 'missing', len(miss), flush=True)
    for n, i in enumerate(miss):
        r = fx.info(m.at[i, 'isin'])
        for c, v in r.items():
            if c in m.columns and v is not None: m.at[i, c] = v
        if n % 20 == 0: m.to_csv(f, index=False); print(n, m.mcap.notna().sum(), flush=True)
        time.sleep(2.0)
    m.to_csv(f, index=False)
    if m.mcap.notna().all(): break
    time.sleep(120)
print('done; with market cap:', m.mcap.notna().sum(), 'of', len(m), flush=True)
