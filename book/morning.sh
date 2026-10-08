#!/bin/bash
# 07:00: check the Gateway, then send the approved batch (dry run until --send is added after the 10-day dry run).
set -uo pipefail
cd "$HOME/Documents/PaperTrading"; source delta1/.venv/bin/activate
D=$(date -v-1d +%F)      # the batch prepared last evening
python -c "from ib_async import IB; ib=IB(); ib.connect('127.0.0.1',4002,clientId=41,readonly=True); print(ib.managedAccounts()); ib.disconnect()" \
  || { python book/kill.py trip "IB Gateway not connected at 07:00"; exit 1; }
python book/execute.py "$D" >> book/morning.log 2>&1
