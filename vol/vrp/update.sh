#!/bin/bash
# Daily vol refresh: rebuild the VRP backtest/viewer and the skew & term-structure monitor.
# Run by launchd on weekday evenings after the US close (com.yasanji.vrp.plist).
# Uses yfinance only (no IB Gateway needed).
set -uo pipefail
cd "$HOME/PaperTrading/vol/vrp" || exit 1
source ../../delta1/.venv/bin/activate
{
  echo "=== $(date) ==="
  python make_viewer.py
  echo "viewer.html rebuilt ($(ls -la viewer.html | awk '{print $5}') bytes)"
  cd "$HOME/PaperTrading/vol/monitor"
  python make_monitor.py
  echo "monitor.html rebuilt ($(ls -la monitor.html | awk '{print $5}') bytes)"
} >> "$HOME/PaperTrading/vol/vrp/update.log" 2>&1
