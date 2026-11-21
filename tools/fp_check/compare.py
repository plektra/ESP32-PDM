"""Compare KiCad PCB pads against JLCPCB EasyEDA footprints.

For each LCSC part: rotate the EasyEDA pads by 0/90/180/270 deg, fit the translation that best puts each EasyEDA pad
on the KiCad pad of the same number, and report rotation, origin offset, worst pad-centre error and pad sizes.
"""
import json, math, sys

kic = json.load(open(sys.argv[1]))
easy = json.load(open(sys.argv[2]))
codes = sys.argv[3:] or list(easy)


def rot(x, y, deg):
    # KiCad: positive rotation is counter-clockwise on screen with y down
    a = math.radians(deg)
    return x * math.cos(a) + y * math.sin(a), -x * math.sin(a) + y * math.cos(a)


def kpads(ref):
    out = []
    for p in kic[ref]['pads']:
        w, h = p['w'], p['h']
        if round(p['rot']) % 180 == 90:
            w, h = h, w
        out.append(dict(n=p['n'], x=p['x'], y=p['y'], w=w, h=h, drill=p['drill'], net=p['net']))
    return out


def fit(kp, ep, deg, by_number=True):
    """Return (translation, worst error, pairs) for EasyEDA pads rotated by deg."""
    er = []
    for p in ep:
        x, y = rot(p['x'], p['y'], deg)
        w, h = p['size']
        if deg % 180 == 90:
            w, h = h, w
        er.append(dict(n=str(p['number']), x=x, y=y, w=w, h=h, hole=p.get('hole')))
    pairs = []
    if by_number:
        kd = {}
        for k in kp:
            kd.setdefault(k['n'], []).append(k)
        for e in er:
            for k in kd.get(e['n'], []):
                pairs.append((k, e))
    if not pairs:
        return None
    # translation = mean offset of matched pairs (multi-pad numbers paired all-to-all: use nearest instead)
    tx = sum(k['x'] - e['x'] for k, e in pairs) / len(pairs)
    ty = sum(k['y'] - e['y'] for k, e in pairs) / len(pairs)
    # refine with nearest-pad matching inside same number
    best = {}
    for k, e in pairs:
        d = math.hypot(k['x'] - e['x'] - tx, k['y'] - e['y'] - ty)
        key = id(e)
        if key not in best or d < best[key][0]:
            best[key] = (d, k, e)
    pairs = [(k, e) for _, k, e in best.values()]
    tx = sum(k['x'] - e['x'] for k, e in pairs) / len(pairs)
    ty = sum(k['y'] - e['y'] for k, e in pairs) / len(pairs)
    worst = max(math.hypot(k['x'] - e['x'] - tx, k['y'] - e['y'] - ty) for k, e in pairs)
    return (tx, ty), worst, pairs


refs_by_code = {}
for r, v in sorted(kic.items()):
    refs_by_code.setdefault(v['lcsc'], []).append(r)

rows = []
for code in codes:
    e = easy[code]
    fpe = e.get('footprint') or {}
    refs = refs_by_code.get(code, [])
    if not refs or not fpe.get('pads'):
        print(f'## {code}: no refs or no EasyEDA pads ({fpe.get("footprint_error") if fpe else e})\n')
        continue
    ref = refs[0]
    kp = kpads(ref)
    ep = fpe['pads']
    res = []
    for deg in (0, 90, 180, 270):
        f = fit(kp, ep, deg)
        if f:
            res.append((f[1], deg, f))
    res.sort(key=lambda t: t[0])
    worst, deg, (t, _, pairs) = res[0]
    print(f'## {code} {e.get("manufacturer","")} {e.get("model","")} ({e.get("package","")})')
    print(f'refs {",".join(refs)}  KiCad fp {kic[ref]["fp"]}  EasyEDA fp {fpe["name"]}  '
          f'pads KiCad {len(kp)} / EasyEDA {len(ep)}')
    alt = ', '.join(f'{d}°:{w:.2f}' for w, d, _ in res[1:])
    print(f'best fit by pad number: rotate EasyEDA {deg}° (others {alt}); origin offset '
          f'({t[0]:+.2f}, {t[1]:+.2f}) mm; worst pad-centre error {worst:.3f} mm')
    pins = {str(p['number']): p.get('name') for p in e.get('pins', [])}
    seen = set()
    for k, ee in sorted(pairs, key=lambda ke: ke[0]['n']):
        key = (k['n'], round(k['w'], 2), round(k['h'], 2), round(ee['w'], 2), round(ee['h'], 2))
        if key in seen:
            continue
        seen.add(key)
        dx = k['x'] - ee['x'] - t[0]
        dy = k['y'] - ee['y'] - t[1]
        hole = f' drill K {k["drill"]} / E {ee["hole"]}' if k['drill'] or ee['hole'] else ''
        print(f'  pad {k["n"]:>3} net {k["net"][:16]:16} EasyEDA pin name {str(pins.get(ee["n"]))[:10]:10} '
              f'K {k["w"]:.2f}x{k["h"]:.2f}  E {ee["w"]:.2f}x{ee["h"]:.2f}  d=({dx:+.2f},{dy:+.2f}){hole}')
    unmatched_k = {k['n'] for k in kp} - {k['n'] for k, _ in pairs}
    unmatched_e = {str(p['number']) for p in ep} - {k['n'] for k, _ in pairs}
    if unmatched_k or unmatched_e:
        print(f'  unmatched pad numbers: KiCad {sorted(unmatched_k)} EasyEDA {sorted(unmatched_e)}')
    # two-pad land metrics
    if len(kp) == 2 and len(ep) == 2:
        def land(ps, horiz):
            a, b = sorted(ps, key=lambda p: p['x'] if horiz else p['y'])
            if horiz:
                return (b['x'] - b['w'] / 2) - (a['x'] + a['w'] / 2), (b['x'] + b['w'] / 2) - (a['x'] - a['w'] / 2)
            return (b['y'] - b['h'] / 2) - (a['y'] + a['h'] / 2), (b['y'] + b['h'] / 2) - (a['y'] - a['h'] / 2)
        horiz = abs(kp[0]['x'] - kp[1]['x']) > abs(kp[0]['y'] - kp[1]['y'])
        gk, zk = land(kp, horiz)
        ge, ze = land([e for _, e in pairs], horiz)
        print(f'  land: gap G KiCad {gk:.2f} / EasyEDA {ge:.2f}; outer Z KiCad {zk:.2f} / EasyEDA {ze:.2f}')
    print()
