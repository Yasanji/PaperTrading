#!/bin/bash
# Daily VRP update: rebuild the backtest, the live vol surface, and the standalone viewer.
# Run by launchd on weekday evenings after the US close (com.yasanji.vrp.plist).
# Uses yfinance only (no IB Gateway needed). Writes vol/vrp/viewer.html.
set -uo pipefail
cd "$HOME/PaperTrading/vol/vrp" || exit 1
source ../../delta1/.venv/bin/activate
{
  echo "=== $(date) ==="
  python make_viewer.py
  echo "viewer.html rebuilt ($(ls -la viewer.html | awk '{print $5}') bytes)"
} >> update.log 2>&1
