#!/bin/bash
# Daily vol refresh: rebuild the single Vol Desk tool (Book & P&L, Vol Surface, Monitor).
# Run by launchd on weekday evenings after the US close (com.yasanji.vrp.plist).
# Uses yfinance only (no IB Gateway needed). Writes vol/dashboard.html.
set -uo pipefail
cd "$HOME/PaperTrading/vol" || exit 1
source ../delta1/.venv/bin/activate
{
  echo "=== $(date) ==="
  python make_dashboard.py
  echo "dashboard.html rebuilt ($(ls -la dashboard.html | awk '{print $5}') bytes)"
} >> "$HOME/PaperTrading/vol/vrp/update.log" 2>&1
