"""Build the single Vol Desk tool: run the VRP backtest and the monitor, embed both into
dashboard_template.html, and write dashboard.html (one file, three views: Book & P&L, Vol
Surface, Monitor).

    python make_dashboard.py

Open dashboard.html in any browser (AG Grid + Plotly load from a CDN).
"""
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'vrp'))
sys.path.insert(0, os.path.join(HERE, 'monitor'))
sys.path.insert(0, HERE)
import backtest
import monitor

if __name__ == '__main__':
    vrp = backtest.run(os.path.join(HERE, 'vrp', 'vrp_backtest.json'))
    mon = monitor.run(os.path.join(HERE, 'monitor', 'monitor.json'))
    tpl = open(os.path.join(HERE, 'dashboard_template.html')).read()
    out = os.path.join(HERE, 'dashboard.html')
    open(out, 'w').write(tpl.replace('__VRP__', json.dumps(vrp)).replace('__MONITOR__', json.dumps(mon)))
    print(f'\nwrote {out}  ({os.path.getsize(out) // 1024} KB)')
