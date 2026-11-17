"""Decision 215: take a router result into the build. Python 3:
  pf_land.py <work dir>
Writes scripts/pf_routes.json from <work>/geo.json (pf_export.py: nets, part moves, kept copper, removed GND copper)
and <work>/routes.json (pf_route.py: tracks, vias). fixed_routes.py loads that file at its end: the listed nets lose
every older T()/V() entry and get these instead, so build_routing.sh reproduces the board from the scripts."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
work = sys.argv[1]
geo = json.load(open(os.path.join(work, 'geo.json')))
r = json.load(open(os.path.join(work, 'routes.json')))
rnd = lambda p: [round(p[0], 4), round(p[1], 4)]
out = {'nets': sorted(geo['width']), 'place': geo['moves'], 'open': r['open'],
       'drop_gnd': geo['drop_gnd'], 'drop_gnd_vias': geo['drop_gnd_vias'], 'tracks': [], 'vias': []}
for it in geo['items']:   # copper of the routed nets that stayed on the base board (wide feeds, escape stubs)
    if it['net'] in geo['width'] and it['kind'] == 'track':
        out['tracks'].append({'net': it['net'], 'layer': it['layer'], 'width': it['w'], 'pts': it['seg'], 'kept': 1})   # exact: matches the board copper
    elif it['net'] in geo['width'] and it['kind'] == 'via':
        out['vias'].append({'net': it['net'], 'at': it['at'], 'size': it['size'], 'drill': it['drill'], 'kept': 1})
out['tracks'] += [{'net': t['net'], 'layer': t['layer'], 'width': t['width'], 'pts': [rnd(p) for p in t['pts']]} for t in r['tracks']]
out['vias'] += [{'net': v['net'], 'at': rnd(v['at']), 'size': 0.6, 'drill': 0.3} for v in r['vias']]
with open(os.path.join(HERE, 'pf_routes.json'), 'w') as f:
    f.write('{\n')
    for k in ('nets', 'place', 'open', 'drop_gnd', 'drop_gnd_vias'):
        f.write(' %s: %s,\n' % (json.dumps(k), json.dumps(out[k])))
    for k in ('tracks', 'vias'):
        f.write(' %s: [\n  %s\n ]%s\n' % (json.dumps(k), ',\n  '.join(json.dumps(x) for x in out[k]), ',' if k == 'tracks' else ''))
    f.write('}\n')
print('pf_routes.json: %d nets, %d moved parts, %d tracks, %d vias, open %s' % (len(out['nets']), len(out['place']), len(out['tracks']), len(out['vias']), r['open']))
