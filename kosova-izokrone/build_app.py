"""Inject the Kosovo border into app.html -> <out> (default: dist/index.html)"""
import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, 'dist', 'index.html')
border = json.load(open(os.path.join(here, 'border.json')))
html = open(os.path.join(here, 'app.html'), encoding='utf-8').read()
html = html.replace('__BORDER__', json.dumps(border, separators=(',', ':')))
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
open(out, 'w', encoding='utf-8').write(html)
