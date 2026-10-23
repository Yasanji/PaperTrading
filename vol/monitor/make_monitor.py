"""Build the standalone vol monitor: run monitor.py and embed the result JSON into the template.

    python make_monitor.py

Open the resulting monitor.html in any browser (AG Grid + Plotly load from a CDN).
"""
import os, json
import monitor

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    result = monitor.run(os.path.join(HERE, 'monitor.json'))
    tpl = open(os.path.join(HERE, 'monitor_template.html')).read()
    out = os.path.join(HERE, 'monitor.html')
    open(out, 'w').write(tpl.replace('__DATA__', json.dumps(result)))
    print(f'\nwrote {out}  ({os.path.getsize(out) // 1024} KB)')
