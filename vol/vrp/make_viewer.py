"""Regenerate the standalone viewer: run the backtest (and a live surface), embed the result
JSON into viewer_template.html, and write viewer.html. One command:

    python make_viewer.py

Open the resulting viewer.html in any browser. It is fully standalone (data embedded); the only
external dependency is the AG Grid library loaded from a CDN, so it needs internet the first time.
"""
import os, json
import backtest

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    result = backtest.run(os.path.join(HERE, 'vrp_backtest.json'))
    tpl = open(os.path.join(HERE, 'viewer_template.html')).read()
    out = os.path.join(HERE, 'viewer.html')
    open(out, 'w').write(tpl.replace('__DATA__', json.dumps(result)))
    print(f'\nwrote {out}  ({os.path.getsize(out) // 1024} KB)')
