"""Inject graph.bin.gz, places.json and border.json into template.html -> ../kosova-izokrone.html"""
import base64, json, sys, datetime, os
here = os.path.dirname(os.path.abspath(__file__))
p = lambda f: os.path.join(here, f)
html = open(p('template.html'), encoding='utf-8').read()
html = html.replace('__GRAPH__', base64.b64encode(open(p('graph.bin.gz'), 'rb').read()).decode())
html = html.replace('__PLACES__', open(p('places.json'), encoding='utf-8').read())
html = html.replace('__BORDER__', open(p('border.json')).read())
html = html.replace('__OSMDATE__', sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat())
open(os.path.join(here, '..', 'kosova-izokrone.html'), 'w', encoding='utf-8').write(html)
