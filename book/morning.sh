#!/bin/bash
# 07:00: check the Gateway, then send the approved batch (dry run until --send is added after the 10-day dry run).
set -uo pipefail
cd "$HOME/Documents/PaperTrading"; source delta1/.venv/bin/activate
D=$(ls book/orders/*.approved.json 2>/dev/null | sort | tail -1 | xargs -n1 basename | cut -c1-10)   # latest approved batch
python -c "from ib_async import IB; ib=IB(); ib.connect('127.0.0.1',4002,clientId=41,readonly=True); print(ib.managedAccounts()); ib.disconnect()" \
  || { python book/kill.py trip "IB Gateway not connected at 07:00"; exit 1; }
[ -n "$D" ] || { echo "$(date): no approved batch" >> book/morning.log; exit 0; }
python book/execute.py "$D" >> book/morning.log 2>&1
