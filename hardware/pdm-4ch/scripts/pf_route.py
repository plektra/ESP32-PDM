"""Decision 215: one-pass signal router for pdm-4ch (driver of pf_core.c). Python 3 with numpy + pillow:
  pf_route.py <work dir> [--iters N] [--nets a,b] [--skip a,b] [--png]
Reads <work>/geo.json (pf_export.py), rasterizes the board at 0.05 mm into the router's maps, routes every net with
negotiated congestion (all nets may overlap at a rising price until none does), then commits the result: nets without
a conflict as routed, the rest one by one against the committed copper. Writes <work>/routes.json
({'tracks': [{net, layer, width, pts}], 'vias': [{net, at}], 'open': {net: n}}) and, with --png, one picture per layer.
Rules (same as the build, docs/ARCHITECTURE.md): class clearances (1.0 mm round VS/VBAT_IN, 0.2 mm signals), power
pour outlines + zone clearance closed to signals, rule areas, 0.5 mm to the edge, no signal on In1, In2 inside VS-In2
only >= 1.5 mm from its outline and never over a PROFET thermal field, In2 tracks 0.9 mm off GND THT pads, no via on
an SMD pad. Within 0.6 mm of a routed pad the class clearance and the pour outline give way to the board's 0.2 mm
(the pad's escape; the pour fill retreats there)."""
import argparse, ctypes, json, math, os, subprocess, sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

G = 0.05
L = ['F.Cu', 'In2.Cu', 'B.Cu']
HERE = os.path.dirname(os.path.abspath(__file__))
CORRIDOR_BAND = 1.5
# VS-In2 east edge: the band is open along the whole edge (decision 215 (6), was the one window of decision 199:
# x 55-57, y 6.45-20). In2 runs may cross the edge anywhere east of the PROFET thermal fields; the build's gates
# (one island, area, 40/40 thermal vias, heat budget) check the pour afterwards.
EXIT_WINDOW = tuple(float(v) for v in os.environ.get('PF_EXIT', '53.0,6.45,61.5,56.0').split(','))
VS_MIN_MM2 = 893.0   # decision 216: 75 % of the 1190.7 mm2 baseline, pieces allowed (each via-tied)
IN2_COST, CORRIDOR_COST, VIA_COST = 1.2, 3.0, 60.0   # via = 3 mm of track


def px(p):
    return (p[0] / G, p[1] / G)


class Maps:
    def __init__(self, geo):
        self.geo = geo
        self.W, self.H = int(round(geo['size'][0] / G)) + 1, int(round(geo['size'][1] / G)) + 1
        self.m = geo['margin']
        names = sorted({it['net'] for it in geo['items'] if it['net']})
        self.nid = {n: i + 1 for i, n in enumerate(names)}
        self.build()

    def owner(self, draws):
        """draws: list of (net id, polygons). Returns int32 map: 0 none, id one net, -1 several nets."""
        draws = sorted(draws, key=lambda d: d[0])
        a = Image.new('I', (self.W, self.H), 0); b = Image.new('I', (self.W, self.H), 0)
        da, db = ImageDraw.Draw(a), ImageDraw.Draw(b)
        for i, pl in draws:
            for p in pl:
                if len(p) >= 3:
                    da.polygon([px(q) for q in p], fill=i)
        for i, pl in reversed(draws):
            for p in pl:
                if len(p) >= 3:
                    db.polygon([px(q) for q in p], fill=i)
        A, B = np.asarray(a, dtype=np.int32), np.asarray(b, dtype=np.int32)
        return np.where(A == B, A, -1)

    def mask(self, polys_list, ring=0.0):
        im = Image.new('1', (self.W, self.H), 0); d = ImageDraw.Draw(im)
        for pl in polys_list:
            for p in pl:
                if len(p) < 3:
                    continue
                pts = [px(q) for q in p]
                d.polygon(pts, fill=1)
                if ring > 0:
                    w = int(math.ceil(2 * ring / G)); r = ring / G
                    d.line(pts + [pts[0]], fill=1, width=w)
                    for x, y in pts:
                        d.ellipse([x - r, y - r, x + r, y + r], fill=1)
        return np.asarray(im, dtype=bool)

    def edge(self, e):
        k = int(math.ceil(e / G)); m = np.zeros((self.H, self.W), bool)
        m[:k + 1] = True; m[-k - 1:] = True; m[:, :k + 1] = True; m[:, -k - 1:] = True
        return m

    def build(self):
        geo, m = self.geo, self.m
        nid = lambda it: self.nid.get(it['net'], 0) or 30000   # no-net copper: an id no routed net has
        self.P, self.O, self.CM = [], [], []
        esc_all = {l: [] for l in L}
        via_draw, via_block = [], []
        for l in L:
            full, base, own, block, rblock = [], [], [], [], []
            for it in geo['items']:
                if l in it['layers']:
                    full.append((nid(it), it['tf'][l])); base.append((nid(it), it['tb'][l]))
                    if it['cl']:
                        own.append((nid(it), it['raw'][l]))
                    if 'esc' in it:
                        esc_all[l].append(it['esc'][l])
                if 'hole_t' in it:   # a drilled hole blocks every layer, but not its own net
                    full.append((nid(it), it['hole_t'])); base.append((nid(it), it['hole_t']))
                if l == 'In2.Cu' and 'gndtht' in it:
                    rblock.append(it['gndtht'])
            F = self.owner(full); B = self.owner(base)
            zb = np.zeros((self.H, self.W), bool); rb_ = self.mask(rblock) | self.edge(0.5 + 0.1 + m)
            cm = np.full((self.H, self.W), 16 if l != 'In2.Cu' else int(round(16 * IN2_COST)), np.uint8)
            for z in geo['zones']:
                if l not in z['layers'] and z['kind'] != 'rule':
                    continue
                if z['kind'] == 'rule':
                    rb_ |= self.mask([z['poly']], 0.1 + m)
                elif z['kind'] == 'pour':
                    zb |= self.mask([z['poly']], z['zc'] + 0.1 + m)
                elif z['kind'] == 'thermal':
                    rb_ |= self.mask([z['poly']], 0.1 + m)
                elif z['kind'] == 'corridor':
                    inside = self.mask([z['poly']])
                    cm[inside] = int(round(16 * IN2_COST * CORRIDOR_COST))
                    # decision 178: runs inside VS-In2 stay >= 1.5 mm from its outline; outside it the normal zone
                    # clearance holds (the old router also closed 1.5 mm outside the pour)
                    band = self.mask([z['poly']], z['zc'] + 0.1 + m) & ~inside | \
                        (inside & ~self.erode(inside, CORRIDOR_BAND))
                    x0, y0, x1, y1 = EXIT_WINDOW
                    band[int(y0 / G):int(y1 / G), int(x0 / G):int(x1 / G)] = False
                    zb |= band
                    self.vs_inside = inside; self.vs_zc = z['zc']
            esc = self.mask(esc_all[l])
            Pm = np.where(zb, -1, F)
            Pm = np.where(esc, B, Pm)
            Pm = np.where(rb_, -1, Pm)
            Om = self.owner(own)
            # own copper eroded by half a track: a track centre there keeps the track inside the copper
            Oe = np.where(self.erode(Om > 0, 0.1), Om, 0)
            self.P.append(np.ascontiguousarray(Pm.astype(np.int16)))
            self.O.append(np.ascontiguousarray(Oe.astype(np.int16)))
            self.Oraw = getattr(self, 'Oraw', []) + [Om]
            self.CM.append(np.ascontiguousarray(cm))
        vd, vblock = [], []
        for it in geo['items']:
            for l in it['layers']:
                vd.append((nid(it), it['v'][l]))
            if 'vpad' in it:
                vblock += [it['vpad'][l] for l in it['layers']]
            if 'hole_v' in it:
                vd.append((nid(it), it['hole_v']))
        V = self.owner(vd)
        vb = self.mask(vblock) | self.edge(0.5 + 0.3 + m)
        for z in geo['zones']:
            if z['kind'] in ('rule', 'thermal'):
                vb |= self.mask([z['poly']], 0.3 + m)
            elif z['kind'] == 'pour':
                vb |= self.mask([z['poly']], z['zc'] + 0.3 + m)
        self.VM = np.ascontiguousarray(np.where(vb, -1, V).astype(np.int16))

    def erode(self, m, r):
        k = int(round(r / G))
        im = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(2 * k + 1))
        return np.asarray(im) > 0

    def cells(self, it):
        """states of an item's own copper (eroded where that leaves something, else its centre cell)"""
        out = []
        N = self.W * self.H
        for li, l in enumerate(L):
            if l not in it['layers']:
                continue
            xs = [q[0] for p in it['raw'][l] for q in p]; ys = [q[1] for p in it['raw'][l] for q in p]
            if not xs:
                continue
            x0, x1 = max(int(min(xs) / G) - 1, 0), min(int(max(xs) / G) + 2, self.W)
            y0, y1 = max(int(min(ys) / G) - 1, 0), min(int(max(ys) / G) + 2, self.H)
            sub = self.O[li][y0:y1, x0:x1] == self.nid[it['net']]
            # only cells of this item (another pad of the net may be in the box): test against its polygon
            im = Image.new('1', (x1 - x0, y1 - y0), 0)
            for p in it['raw'][l]:
                ImageDraw.Draw(im).polygon([(q[0] / G - x0, q[1] / G - y0) for q in p], fill=1)
            sub = sub & np.asarray(im, dtype=bool)
            yy, xx = np.nonzero(sub)
            if len(yy) == 0:
                cx, cy = int(round(it['at'][0] / G)), int(round(it['at'][1] / G))
                self.O[li][cy, cx] = self.nid[it['net']]
                yy, xx = np.array([cy - y0]), np.array([cx - x0])
            out.append(li * N + (yy + y0) * self.W + (xx + x0))
        return np.concatenate(out).astype(np.int32) if out else np.zeros(0, np.int32)


def load_core():
    so = os.path.join(HERE, 'pf_core.so')
    src = os.path.join(HERE, 'pf_core.c')
    if not os.path.exists(so) or os.path.getmtime(so) < os.path.getmtime(src):
        subprocess.check_call(['cc', '-O2', '-shared', '-fPIC', '-o', so, src])
    c = ctypes.CDLL(so)
    c.pf_route.argtypes = [ctypes.c_int, ctypes.c_float, ctypes.c_int, ctypes.c_float]
    c.pf_conflicts.argtypes = [ctypes.c_int, ctypes.c_float]
    c.pf_reach.restype = ctypes.c_long; c.pf_reach.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_long]
    c.pf_set_maxexp.argtypes = [ctypes.c_long]
    return c


def emit(mp, name, width, legs):
    """legs (state arrays) -> tracks/vias in mm"""
    N = mp.W * mp.H
    tracks, vias = [], []
    for leg in legs:
        run = []
        for i, s in enumerate(leg):
            l, c = divmod(int(s), N)
            pt = (round((c % mp.W) * G, 3), round((c // mp.W) * G, 3))
            if run and run[0] != l:
                vias.append({'net': name, 'at': pt})
                if len(run) > 2:
                    tracks.append({'net': name, 'layer': L[run[0]], 'width': width, 'pts': simplify(run[1:])})
                run = []
            if not run:
                run = [l]
            run.append(pt)
        if len(run) > 2:
            tracks.append({'net': name, 'layer': L[run[0]], 'width': width, 'pts': simplify(run[1:])})
    return tracks, vias


def simplify(pts):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[i], pts[i + 1]
        if abs((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) > 1e-9:
            out.append(b)
    out.append(pts[-1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('work'); ap.add_argument('--iters', type=int, default=60)
    ap.add_argument('--nets', default=''); ap.add_argument('--skip', default=''); ap.add_argument('--png', action='store_true')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--ties', default='auto')
    ap.add_argument('--resume', action='store_true'); ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    t0 = time.time()
    geo = json.load(open(os.path.join(a.work, 'geo.json')))
    mp = Maps(geo)
    print('maps %.0f s, grid %d x %d' % (time.time() - t0, mp.W, mp.H), flush=True)
    core = load_core()
    p16 = ctypes.POINTER(ctypes.c_int16); p8 = ctypes.POINTER(ctypes.c_uint8)
    # clusters
    cl = {}
    for it in geo['items']:
        if it['cl']:
            cl.setdefault(it['net'], {}).setdefault(it['cl'], []).append(it)
    cells = {n: {k: np.unique(np.concatenate([mp.cells(it) for it in its])) for k, its in d.items()} for n, d in cl.items()}
    core.pf_init(mp.W, mp.H, *[x.ctypes.data_as(p16) for x in mp.P], *[x.ctypes.data_as(p16) for x in mp.O],
                 mp.VM.ctypes.data_as(p16), *[x.ctypes.data_as(p8) for x in mp.CM])
    want = set(a.nets.split(',')) - {''}; skip = set(a.skip.split(',')) - {''}
    nets = []
    for n in sorted(cl):
        if len(cl[n]) < 2 or (want and n not in want) or n in skip:
            continue
        w = geo['width'][n]
        ni = core.pf_add_net(mp.nid[n], int(round(((w - 0.2) / 2 + geo.get('clr', {}).get(n, 0.2) - 0.2) / G)))
        keys = sorted(cells[n])
        for k in keys:
            arr = np.ascontiguousarray(cells[n][k])
            core.pf_add_cluster(ni, len(arr), arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)))
        core.pf_finalize(ni)
        nets.append({'name': n, 'i': ni, 'w': w, 'keys': keys, 'ncl': len(keys)})
    print('%d nets, %d links' % (len(nets), sum(n['ncl'] - 1 for n in nets)), flush=True)
    rng = np.random.default_rng(a.seed)
    i32 = ctypes.POINTER(ctypes.c_int32)
    legfile = os.path.join(a.work, 'legs.npz')
    resume = a.resume and os.path.exists(legfile)
    if resume:
        z = np.load(legfile)
        for n in nets:
            for g in range(int(z['nleg_%d' % n['i']])):
                arr = np.ascontiguousarray(z['leg_%d_%d' % (n['i'], g)])
                core.pf_load_leg(n['i'], len(arr), arr.ctypes.data_as(i32))
            for q in z['fail_%d' % n['i']]:
                core.pf_load_fail(n['i'], int(q))
            core.pf_commit_loaded(n['i'])
        print('resumed', legfile, flush=True)
    # sealed by the fixed board alone?
    pres, todo = 0.5, list(nets)
    # GND ties (--ties auto | R17.2,C21.2,...): a short F.Cu stub and a via to the GND plane for GND pads the pours may
    # not reach between the routed tracks. Routed first, on the empty board; the signals then keep clear of them.
    tie_legs, tie_fail = [], []
    if a.ties == 'auto':   # every GND SMD pad of a moved part: its old tie copper went with the move
        a.ties = ','.join(it['ref'] for it in geo['items'] if it['kind'] == 'pad' and it['net'] == 'GND' and it.get('smd')
                          and it['ref'].split('.')[0] in geo.get('moves', {}))
    if a.ties:
        gid = mp.nid['GND']; N_ = mp.W * mp.H
        ti = core.pf_add_net(gid, int(round((0.3 - 0.2) / 2 / G)))
        pads = {it['ref']: it for it in geo['items'] if it['kind'] == 'pad' and it['net'] == 'GND' and it.get('smd')}
        refs = [r for r in a.ties.split(',') if r in pads]
        for r in refs:
            it = pads[r]; cx, cy = int(round(it['at'][0] / G)), int(round(it['at'][1] / G))
            arr = np.array([cy * mp.W + cx + dy * mp.W + dx for dy in (-1, 0, 1) for dx in (-1, 0, 1)], np.int32)
            core.pf_add_cluster(ti, len(arr), arr.ctypes.data_as(i32))
        for q, r in enumerate(refs):
            if not core.pf_route_tie(ti, q):
                tie_fail.append(r)
        for g in range(core.pf_nleg(ti)):
            arr = np.zeros(core.pf_leg_len(ti, g), np.int32); core.pf_leg_get(ti, g, arr.ctypes.data_as(i32)); tie_legs.append(arr)
        print('GND ties: %d routed, failed %s' % (len(tie_legs), tie_fail), flush=True)
    bad = {}
    for it in range(0 if resume else a.iters):
        order = sorted(todo, key=lambda n: rng.random())
        for n in order:
            n['fail'] = core.pf_route(n['i'], pres, 0, VIA_COST)
        bad = {}
        for n in nets:
            b = core.pf_conflicts(n['i'], min(0.2 + 0.05 * it, 1.5))
            if b:
                bad[n['name']] = b
        sealed = sum(n.get('fail', 0) for n in nets)
        if it == 0:
            for n in nets:
                for i in range(core.pf_nfail(n['i'])):
                    q = core.pf_fail_get(n['i'], i); k = n['keys'][q]
                    refs = [x['ref'] or x['kind'] + str(x['at']) for x in cl[n['name']][k]]
                    print('  sealed', n['name'], refs[:4], 'reach', core.pf_reach(n['i'], q, 200000), flush=True)
        print('round %d: %d nets conflict (%d cells), %d legs sealed, pres %.1f, %.0f s'
              % (it, len(bad), sum(bad.values()), sealed, pres, time.time() - t0), flush=True)
        if not bad:
            break
        pres = min(pres * 1.25, 80.0)
        todo = [n for n in nets if n['name'] in bad]
    def save_legs():
        d = {}
        for n in nets:
            k = core.pf_nleg(n['i']); d['nleg_%d' % n['i']] = k
            for g in range(k):
                arr = np.zeros(core.pf_leg_len(n['i'], g), np.int32); core.pf_leg_get(n['i'], g, arr.ctypes.data_as(i32))
                d['leg_%d_%d' % (n['i'], g)] = arr
            d['fail_%d' % n['i']] = np.array([core.pf_fail_get(n['i'], q) for q in range(core.pf_nfail(n['i']))], np.int32)
        np.savez(legfile, **d)
    hot = {}
    for n in nets:
        buf = np.zeros(20000, np.int32)
        k = core.pf_conflict_cells(n['i'], buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)), 20000)
        for j in range(k):
            c = int(buf[2 * j])
            key = (int((c % mp.W) * G // 2) * 2, int((c // mp.W) * G // 2) * 2)
            hot.setdefault(key, {}).setdefault(n['name'], 0); hot[key][n['name']] += 1
    json.dump([[k[0], k[1], v] for k, v in hot.items()], open(os.path.join(a.work, 'hot.json'), 'w'))
    for k, v in sorted(hot.items(), key=lambda kv: -sum(kv[1].values()))[:25]:
        print('  hot x %d-%d y %d-%d: %d cells' % (k[0], k[0] + 2, k[1], k[1] + 2, sum(v.values())),
              sorted(v, key=lambda q: -v[q])[:6])
    # commit: nets in conflict are taken off and put back one by one against the committed copper
    # greedy cover: take off the net with the most conflict cells per link until no two committed nets conflict
    conf = []
    while True:
        worst, wb = None, 0
        for n in nets:
            if n in conf:
                continue
            b = core.pf_conflicts(n['i'], 0.0) / (n['ncl'] - 1)
            if b > wb:
                worst, wb = n, b
        if worst is None:
            break
        core.pf_clear(worst['i']); conf.append(worst)
    print('commit: %d nets kept as routed, %d put back one by one' % (len(nets) - len(conf), len(conf)), flush=True)
    for n in sorted(conf, key=lambda n: (-n['w'], -n['ncl'])):   # wide and many-pin nets first: they have the least choice
        n['fail'] = core.pf_route(n['i'], 0.0, 1, VIA_COST)
    # retry: a net that still has an open link is rerouted whole after each other failed net had its turn
    for rnd in range(3):
        failed = [n for n in conf if core.pf_nfail(n['i'])]
        if not failed:
            break
        for n in failed:
            core.pf_route(n['i'], 0.0, 1, VIA_COST)
    if not resume:
        save_legs()
    # rip-up: a net with an open link is routed across the cheapest committed nets; those are taken off, the net
    # goes in, they are put back. Kept only when fewer links stay open in total.
    def total_open():
        return sum(core.pf_nfail(n['i']) for n in nets)
    for rnd, (rp, rv) in enumerate([(4, 1), (12, 1), (2, 1), (30, 1), (6, 0.4), (20, 2.5), (1, 1), (60, 1), (8, 0.2), (3, 3)]):
        failed = [n for n in nets if core.pf_nfail(n['i'])]
        if not failed:
            break
        for x in failed:
            before = total_open()
            for n in nets:
                core.pf_save(n['i'])
            core.pf_route(x['i'], float(rp), 0, VIA_COST * rv)
            blk = [n for n in nets if n is not x and core.pf_conflicts(n['i'], 0.0) > 0]
            ok = False
            if blk and len(blk) <= 10 and core.pf_nfail(x['i']) == 0:
                for n in blk:
                    core.pf_clear(n['i'])
                core.pf_route(x['i'], 0.0, 1, VIA_COST * rv)
                for n in sorted(blk, key=lambda n: (-n['w'], -n['ncl'])):
                    core.pf_route(n['i'], 0.0, 1, VIA_COST)
                ok = total_open() < before
            if a.verbose:
                print('  try %d %s: soft fail %d, blockers %s -> open %d (was %d)' % (rnd, x['name'], core.pf_nfail(x['i']) if not blk else -1, [n['name'] for n in blk][:12], total_open(), before), flush=True)
            if ok:
                print('rip-up %d: %s in, moved %s; open %d -> %d' % (rnd, x['name'], [n['name'] for n in blk], before, total_open()), flush=True)
            else:
                for n in [x] + blk:
                    core.pf_clear(n['i'])
                for n in [x] + blk:
                    core.pf_restore(n['i'])
    out = {'tracks': [], 'vias': [], 'open': {}}
    t, v = emit(mp, 'GND', 0.3, tie_legs)
    out['tracks'] += t; out['vias'] += v; out['tie_fail'] = tie_fail
    for n in nets:
        legs = []
        for g in range(core.pf_nleg(n['i'])):
            ln = core.pf_leg_len(n['i'], g)
            arr = np.zeros(ln, np.int32); core.pf_leg_get(n['i'], g, arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)))
            legs.append(arr)
        t, v = emit(mp, n['name'], n['w'], legs)
        out['tracks'] += t; out['vias'] += v
        nf = core.pf_nfail(n['i'])
        if nf:
            out['open'][n['name']] = nf
    # VS-In2 island check (decision 216: area floor; pieces listed): the fill is the outline minus every foreign In2
    # item (fixed and routed) grown by the zone clearance; counted at 0.1 mm
    if hasattr(mp, 'vs_inside'):
        im = Image.new('1', (mp.W, mp.H), 0); d = ImageDraw.Draw(im); zc = mp.vs_zc
        for it in geo['items']:
            if it['net'] != 'VS' and 'In2.Cu' in it['layers']:
                for p in it['raw']['In2.Cu']:
                    if len(p) > 2:
                        d.polygon([px(q) for q in p], fill=1)
            if it['net'] != 'VS' and 'hole_t' in it:
                for p in it['hole_t']:
                    if len(p) > 2:
                        d.polygon([px(q) for q in p], fill=1)
        for t in out['tracks']:
            if t['layer'] == 'In2.Cu':
                d.line([px(p) for p in t['pts']], fill=1, width=int(round(t['width'] / G)) + 1)
                for p in t['pts']:
                    x, y = px(p); r = t['width'] / 2 / G
                    d.ellipse([x - r, y - r, x + r, y + r], fill=1)
        for v in out['vias']:
            x, y = px(v['at']); r = 0.3 / G
            d.ellipse([x - r, y - r, x + r, y + r], fill=1)
        k = int(round((zc + 0.15) / G)) * 2 + 1   # + half the pour min width: necks thinner than that vanish
        foreign = np.asarray(im.convert('L').filter(ImageFilter.MaxFilter(k if k % 2 else k + 1))) > 0
        fill = mp.vs_inside & ~foreign
        img = np.ascontiguousarray(fill.astype(np.uint8))
        buf = np.zeros(3 * 4096, np.int32)
        k = core.pf_components(img.ctypes.data_as(p8), mp.W, mp.H, buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int32)), 4096)
        comps = [(int(buf[3 * i]) * G * G, int(buf[3 * i + 1]) * G, int(buf[3 * i + 2]) * G) for i in range(min(k, 4096))]
        comps.sort(reverse=True)
        big = [c for c in comps if c[0] > 1.0]
        out['vs_in2'] = {'islands': len(big), 'area': round(sum(c[0] for c in comps), 1), 'parts': [[round(c[0], 1), round(c[1], 1), round(c[2], 1)] for c in big[:5]]}
        print('VS-In2 check: %d islands > 1 mm2, total %.1f mm2 (min %.1f)%s' % (len(big), out['vs_in2']['area'], VS_MIN_MM2,
              ('' if out['vs_in2']['area'] >= VS_MIN_MM2 else '  FAIL') + ' ' + str(out['vs_in2']['parts'])), flush=True)
    json.dump(out, open(os.path.join(a.work, 'routes.json'), 'w'))
    print('done: %d tracks, %d vias, open %d links in %d nets, %.0f s'
          % (len(out['tracks']), len(out['vias']), sum(out['open'].values()), len(out['open']), time.time() - t0))
    for n, k in sorted(out['open'].items()):
        print('  open', n, k)
    if a.png:
        col = {'F.Cu': (200, 50, 50), 'In2.Cu': (210, 140, 40), 'B.Cu': (60, 110, 220)}
        for li, l in enumerate(L):
            base = np.zeros((mp.H, mp.W, 3), np.uint8) + 255
            base[mp.P[li] != 0] = (225, 225, 225); base[mp.P[li] == -1] = (170, 170, 170); base[mp.Oraw[li] > 0] = (120, 200, 120)
            im = Image.fromarray(base); d = ImageDraw.Draw(im)
            for t in out['tracks']:
                if t['layer'] == l:
                    d.line([px(p) for p in t['pts']], fill=col[l], width=int(round(t['width'] / G)))
            for v in out['vias']:
                x, y = px(v['at']); d.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(0, 0, 0))
            im.save(os.path.join(a.work, 'route-%s.png' % l))


if __name__ == '__main__':
    main()
