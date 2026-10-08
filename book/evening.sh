#!/bin/bash
# Evening chain (DESIGN.md s.4). Each step runs only if the previous one succeeded; any failure stops the chain.
# Run by launchd after the 22:30 collector. Orders are not sent here: execute.py runs at 07:00 after approval.
set -euo pipefail
cd "$HOME/Documents/PaperTrading"
source delta1/.venv/bin/activate
D=$(date +%F)
LOG=book/evening.log
{
  echo "=== $(date) ==="
  python book/futures_ib.py --yahoo-only                      # futures closes (Yahoo until IB data is funded)
  python book/book.py "$D" --source db                       # pods -> book rules -> targets and orders files
  git add "book/targets/$D.csv" "book/targets/$D.json" "book/orders/$D.csv"
  git commit -q -m "Targets for $D"
  git push -q                                                 # targets public before any order
  python book/approve.py "$D"                                 # prints the batch for review
  osascript -e "display notification \"Targets for $D committed. Review with approve.py\" with title \"Paper book\""
} >> "$LOG" 2>&1 || {
  python book/kill.py trip "evening chain failed on $D: see book/evening.log"
  osascript -e "display notification \"Evening chain failed: see book/evening.log\" with title \"Paper book\""
}
