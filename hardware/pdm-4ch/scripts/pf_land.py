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
# GND copper an earlier run removed is no longer on the exported board, so this export does not list it again: keep
# the earlier drop lists (else fixed_routes.py puts that harvest copper back on turned parts' pads)
_old = os.path.join(HERE, 'pf_routes.json')
if os.path.exists(_old):
    _o = json.load(open(_old))
    for _k in ('drop_gnd', 'drop_gnd_vias'):
        out[_k] = _o.get(_k, []) + [x for x in out[_k] if x not in _o.get(_k, [])]
    # the router's GND pad stubs of the earlier run are locked board copper now. Where this run put a new GND via
    # within 0.6 mm of an old one (the same pad tied again, e.g. 0.05 mm off), the old via and its stub go (else both
    # stay and the vias break hole-to-hole). Old stubs the router did not redo stay: it saw them as existing copper.
    _new_v = [v['at'] for v in r['vias'] if v['net'] == 'GND']
    _near = lambda p, q, d: abs(p[0] - q[0]) <= d and abs(p[1] - q[1]) <= d
    _gone = [v['at'] for v in _o.get('vias', []) if v['net'] == 'GND' and not v.get('kept') and
             any(_near(v['at'], q, 0.6) and not _near(v['at'], q, 1e-4) for q in _new_v)]
    out['drop_gnd_vias'] += _gone
    for t in _o.get('tracks', []):
        if t['net'] == 'GND' and not t.get('kept') and any(_near(p, g, 1e-3) for p in t['pts'] for g in _gone):
            out['drop_gnd'] += [[t['layer'], a, e] for a, e in zip(t['pts'], t['pts'][1:])]
for it in geo['items']:   # copper of the routed nets that stayed on the base board (wide feeds, escape stubs)
    if it['net'] in geo['width'] and it['kind'] == 'track':
        out['tracks'].append({'net': it['net'], 'layer': it['layer'], 'width': it['w'], 'pts': it['seg'], 'kept': 1})   # exact: matches the board copper
    elif it['net'] in geo['width'] and it['kind'] == 'via':
        out['vias'].append({'net': it['net'], 'at': it['at'], 'size': it['size'], 'drill': it['drill'], 'kept': 1})
out['tracks'] += [{'net': t['net'], 'layer': t['layer'], 'width': t['width'], 'pts': [rnd(p) for p in t['pts']]} for t in r['tracks']]
out['vias'] += [{'net': v['net'], 'at': rnd(v['at']), 'size': 0.6, 'drill': 0.3} for v in r['vias']]
seen, uniq = set(), []   # two legs of a net may end in the same via: keep one
for v in out['vias']:
    k = (v['net'], round(v['at'][0] * 1000), round(v['at'][1] * 1000))
    if k not in seen:
        seen.add(k); uniq.append(v)
out['vias'] = uniq
with open(os.path.join(HERE, 'pf_routes.json'), 'w') as f:
    f.write('{\n')
    for k in ('nets', 'place', 'open', 'drop_gnd', 'drop_gnd_vias'):
        f.write(' %s: %s,\n' % (json.dumps(k), json.dumps(out[k])))
    for k in ('tracks', 'vias'):
        f.write(' %s: [\n  %s\n ]%s\n' % (json.dumps(k), ',\n  '.join(json.dumps(x) for x in out[k]), ',' if k == 'tracks' else ''))
    f.write('}\n')
print('pf_routes.json: %d nets, %d moved parts, %d tracks, %d vias, open %s' % (len(out['nets']), len(out['place']), len(out['tracks']), len(out['vias']), r['open']))
