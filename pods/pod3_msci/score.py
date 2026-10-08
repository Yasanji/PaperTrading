"""Score a committed prediction against MSCI's published list. Usage: python score.py prediction.csv actual.csv
actual.csv has columns: change (ADD or DELETE), name. Names are matched on their first word, upper case."""
import sys, pandas as pd
p = pd.read_csv(sys.argv[1]); a = pd.read_csv(sys.argv[2])
key = lambda s: str(s).upper().split()[0]
for ch in ['ADD', 'DELETE']:
    P = {key(n) for n in p.loc[p.call == ch, 'name']}; A = {key(n) for n in a.loc[a.change == ch, 'name']}
    W = {key(n) for n in p.loc[p.call == 'watch: ' + ch.lower(), 'name']}
    print(f'{ch}: predicted {len(P)}, actual {len(A)}, correct {len(P & A)}; '
          f'precision {len(P & A) / max(len(P), 1):.0%}, recall {len(P & A) / max(len(A), 1):.0%}; actual changes on the watch list {len(W & A)}')
    print('  missed:', sorted(A - P), ' wrong:', sorted(P - A))
