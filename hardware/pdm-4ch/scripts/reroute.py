"""Decision 214: one-pass rip-up router for the pdm-4ch signal nets (negotiated congestion, "PathFinder").
reroute.py <geom.json> <nets (comma list) | @file | @json> <out.py> [iterations]
geom.json comes from geom_export.py on the build base (routing_build.py prep: the REROUTED_NETS copper is gone, every
other item is fixed). Every net is routed on maze_route.py's own masks (foreign fixed copper, pour outlines and their
rings, keep-outs, the VS-In2 corridor band, edge, class widths), so the legal space is exactly the maze router's.
The nets of this run may overlap each other at a price: each round, a cell used by another net of the run costs
(1 + history) * (1 + pres * users); after the round the history of every contested cell grows and the present factor
rises (capped at 8), and every net that still conflicts is ripped up and rerouted. Ends when no two nets conflict or
after the iteration limit. Then a legalization pass commits the nets one by one, the committed copper being a hard
obstacle and the history costs steering each net away from the contested cells: every emitted leg is legal, and a leg
that finds no room stays open. Writes fixed_routes.py lines (T/V) like maze_route.py.
Cells inside a net's own fixed copper (pads, stubs) never count as conflicts: that copper is fixed already."""
import heapq, json, math, os, sys, time
from array import array

GEO = os.environ.get('REROUTE_GEO') or sys.argv[1]
_argv = sys.argv
sys.argv = [sys.argv[0], GEO, 'x']
import importlib.util, os
_spec = importlib.util.spec_from_file_location('mz', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maze_route.py'))
mz = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(mz)
sys.argv = _argv

W, H, G, L = mz.W, mz.H, mz.G, mz.L
N = W * H
MARGIN = 0.06
CLR = 0.2


def disk(r_mm):
    k = int(math.ceil(r_mm / G))
    return [dy * W + dx for dy in range(-k, k + 1) for dx in range(-k, k + 1) if (dx * dx + dy * dy) * G * G <= r_mm * r_mm]


def half(net):
    return mz.WIDTH.get(net, 0.2) / 2


def footprint(net, path, copper=None):
    """cells another net's track centre (half width 0.1) / via centre (r 0.3) may not use: per layer, and for vias.
    Path cells inside the net's own fixed copper (pads, stubs) add nothing: that copper is fixed and already in every
    other net's mask."""
    h = half(net)
    dt = disk(h + CLR + 0.1 + MARGIN); dv = disk(h + CLR + 0.3 + MARGIN)
    vt = disk(0.3 + CLR + 0.1 + MARGIN); vv = disk(0.3 + CLR + 0.3 + MARGIN)
    ft = [set() for _ in L]; fv = set()
    prev = None
    for li, c in path:
        x = c % W
        if copper is not None and c in copper[li] and (prev is None or prev[0] == li):
            prev = (li, c); continue
        for o in dt:
            n = c + o
            if 0 <= n < N and abs(n % W - x) < 12:
                ft[li].add(n)
        for o in dv:
            n = c + o
            if 0 <= n < N and abs(n % W - x) < 12:
                fv.add(n)
        if prev is not None and prev[0] != li:   # a via at c
            for l2 in range(3):
                for o in vt:
                    n = c + o
                    if 0 <= n < N and abs(n % W - x) < 12:
                        ft[l2].add(n)
            for o in vv:
                n = c + o
                if 0 <= n < N and abs(n % W - x) < 12:
                    fv.add(n)
        prev = (li, c)
    return ft, fv


class Net:
    def __init__(self, name):
        self.name = name
        self.cls = sorted({it['cl'] for it in mz.geo['items'] if it['net'] == name})
        self.tm, self.vm, self.cor = mz.masks(name)
        self.cells = {}   # cluster -> {layer: cells}
        for it in mz.geo['items']:
            if it['net'] != name:
                continue
            for l in it['layers']:
                if l in L:
                    self.cells.setdefault(it['cl'], {ll: set() for ll in L})[l] |= mz.erode(mz.cells_of(it['raw'][l]))
        self.own = {l: set().union(*[self.cells[k][l] for k in self.cells]) if self.cells else set() for l in L}
        self.copper = [set() for _ in L]   # raw own fixed copper per layer index
        for it in mz.geo['items']:
            if it['net'] == name:
                for l in it['layers']:
                    if l in L:
                        self.copper[L.index(l)] |= mz.cells_of(it['raw'][l])
        self.paths = []      # legs: lists of (li, c)
        self.failed = []     # clusters it could not reach
        self.ft = [set() for _ in L]; self.fv = set()


def route_leg(net, start, goal, occ_t, occ_v, hist, histv, pres, hard=False):
    gpts = [(c % W, c // W) for l in L for c in goal[l]]
    if not gpts or not any(start.values()):
        return None
    gx0, gx1 = min(p[0] for p in gpts), max(p[0] for p in gpts)
    gy0, gy1 = min(p[1] for p in gpts), max(p[1] for p in gpts)

    def hh(c):
        x, y = c % W, c // W
        return math.hypot(max(gx0 - x, 0, x - gx1), max(gy0 - y, 0, y - gy1))
    dist = {}; prev = {}; pq = []
    for li, l in enumerate(L):
        for c in start[l]:
            dist[(li, c)] = 0.0; heapq.heappush(pq, (hh(c), 0.0, li, c))
    nb = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    tm, vm, cor, own = net.tm, net.vm, net.cor, net.own
    n = 0
    while pq:
        f, g, li, c = heapq.heappop(pq)
        if g > dist.get((li, c), 1e18):
            continue
        n += 1
        if n > 4000000:
            return None
        if c in goal[L[li]]:
            path = [(li, c)]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1]
        x, y = c % W, c // W
        tml = tm[L[li]]; ol = own[L[li]]; ot = occ_t[li]; hl = hist[li]; cop = net.copper[li]
        for dx, dy, w in nb:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            nc = ny * W + nx
            if tml[nc] and nc not in ol:
                continue
            if hard and ot[nc] and nc not in cop:
                continue
            base = w * (mz.IN2_COST * (mz.CORRIDOR_COST if cor[nc] else 1.0) if li == 1 else 1.0)
            ng = g + (base if nc in cop else base * (1.0 + hl[nc]) * (1.0 + pres * ot[nc]))
            if ng < dist.get((li, nc), 1e18):
                dist[(li, nc)] = ng; prev[(li, nc)] = (li, c)
                heapq.heappush(pq, (ng + hh(nc), ng, li, nc))
        if not vm[c] and c not in ol and not (hard and occ_v[c]):
            vc = mz.VIA_COST * (1.0 + histv[c]) * (1.0 + pres * occ_v[c])
            for lj in range(3):
                if lj != li and not tm[L[lj]][c] and not (hard and occ_t[lj][c]):
                    ng = g + vc
                    if ng < dist.get((lj, c), 1e18):
                        dist[(lj, c)] = ng; prev[(lj, c)] = (li, c)
                        heapq.heappush(pq, (ng + hh(c), ng, lj, c))
    return None


def route_net(net, occ_t, occ_v, hist, histv, pres, hard=False):
    net.paths = []; net.failed = []; net.comps = 0
    rest = set(net.cls)
    tried = set()
    while rest:
        seeds = [c for c in sorted(rest) if c not in tried]
        if not seeds:
            break
        seed = seeds[0]; tried.add(seed); net.comps += 1
        done = {seed}; rest.discard(seed)
        start = {l: set(net.cells[seed][l]) for l in L}
        while rest:
            goal = {l: set().union(*[net.cells[k][l] for k in rest]) for l in L}
            path = route_leg(net, start, goal, occ_t, occ_v, hist, histv, pres, hard)
            if not path:
                net.failed.append(sorted(rest))
                break
            li, c = path[-1]
            hit = [k for k in rest if c in net.cells[k][L[li]]]
            net.paths.append(path)
            done.add(hit[0]); rest.discard(hit[0]); tried |= done
            for l in L:
                start[l] |= net.cells[hit[0]][l]
            for lj, cj in path:
                start[L[lj]].add(cj)
    net.ft = [set() for _ in L]; net.fv = set()
    for p in net.paths:
        ft, fv = footprint(net.name, p, net.copper)
        for l in range(3):
            net.ft[l] |= ft[l]
        net.fv |= fv


def add_occ(net, occ_t, occ_v, s):
    for l in range(3):
        a = occ_t[l]
        for c in net.ft[l]:
            a[c] += s
    for c in net.fv:
        occ_v[c] += s


def conflicts(net, occ_t, occ_v):
    """cells of this net's paths inside another net's footprint (own footprint removed by the caller)"""
    bad = []
    for p in net.paths:
        prev = None
        for li, c in p:
            if c in net.copper[li] and (prev is None or prev[0] == li):
                prev = (li, c); continue
            if occ_t[li][c] > 0:
                bad.append((li, c))
            if prev is not None and prev[0] != li and occ_v[c] > 0:
                bad.append((-1, c))
            prev = (li, c)
    return bad


def negotiate(names, iters, log=True):
    """negotiated congestion over the named nets on mz.geo, then legalization. Returns (lines, open clusters)"""
    t0 = time.time()
    nets = []
    for n in names:
        nt = Net(n)
        if len(nt.cls) < 2:
            print('#', n, 'already one cluster', file=sys.stderr); continue
        nets.append(nt)
    print('# %d nets to route (%.0f s masks)' % (len(nets), time.time() - t0), file=sys.stderr, flush=True)
    occ_t = [array('h', bytes(2 * N)) for _ in L]; occ_v = array('h', bytes(2 * N))
    hist = [array('f', bytes(4 * N)) for _ in L]; histv = array('f', bytes(4 * N))
    pres = 0.5
    todo = list(nets)
    # nets with few clusters and short spans first in the first round
    todo.sort(key=lambda nt: len(nt.cls))
    for it in range(iters):
        for nt in todo:
            add_occ(nt, occ_t, occ_v, -1)
            route_net(nt, occ_t, occ_v, hist, histv, pres)
            add_occ(nt, occ_t, occ_v, +1)
        # conflicts
        bad = {}
        for nt in nets:
            add_occ(nt, occ_t, occ_v, -1)
            b = conflicts(nt, occ_t, occ_v)
            add_occ(nt, occ_t, occ_v, +1)
            if b:
                bad[nt.name] = b
        nfail = sum(len(nt.failed) for nt in nets)
        if os.environ.get('RR_DEBUG'):
            own_t = {}
            for nt in nets:
                for l in range(3):
                    for c in nt.ft[l]:
                        own_t.setdefault((l, c), []).append(nt.name)
            import collections
            pairs = collections.Counter()
            for nm, b in bad.items():
                for li, c in b:
                    if li >= 0:
                        for o in own_t.get((li, c), []):
                            if o != nm:
                                pairs[(nm, o, L[li], (c % W) // 10, (c // W) // 10)] += 1
            print('#   top', pairs.most_common(8), file=sys.stderr)
        ncells = sum(len(v) for v in bad.values())
        (print if log else (lambda *a, **k: None))('# round %d: %d nets conflict (%d cells), %d legs unrouted, pres %.2f, %.0f s'
              % (it, len(bad), ncells, nfail, pres, time.time() - t0), file=sys.stderr, flush=True)
        if not bad:
            break
        for v in bad.values():
            for li, c in v:
                if li < 0:
                    histv[c] += 1.0
                else:
                    hist[li][c] += 1.0
        pres = min(pres * 1.6, 8.0)
        todo = [nt for nt in nets if nt.name in bad]
    # legalize: commit nets one by one with the committed copper as hard obstacles, guided by the history costs;
    # nets that did not conflict in the last round go first, then by fewest conflict cells. Every committed leg is
    # legal against the fixed copper and every other committed leg; a leg that finds no room stays open.
    last = {nt.name: len(bad.get(nt.name, [])) for nt in nets}
    order = sorted(nets, key=lambda nt: (last[nt.name], len(nt.cls)))
    occ_t = [array('h', bytes(2 * N)) for _ in L]; occ_v = array('h', bytes(2 * N))
    out = []
    for nt in order:
        route_net(nt, occ_t, occ_v, hist, histv, 0.0, hard=True)
        add_occ(nt, occ_t, occ_v, +1)
        for p in nt.paths:
            out.append('# %s leg' % nt.name)
            out += mz.emit(nt.name, p)
        if log:
            print('#', nt.name, 'ok' if not nt.failed else 'partial %s' % nt.failed, file=sys.stderr, flush=True)
    opn = sum(nt.comps - 1 for nt in nets)
    print('# legal: %d nets complete, %d clusters open' % (sum(1 for nt in nets if not nt.failed), opn), file=sys.stderr)
    return out, opn


def main():
    arg = sys.argv[2]
    if arg.startswith('@'):
        txt = open(arg[1:]).read()
        names = json.loads(txt) if txt.lstrip().startswith('[') else [n.strip() for n in txt.split('\n') if n.strip()]
    else:
        names = arg.split(',')
    lines, _ = negotiate(names, int(sys.argv[4]) if len(sys.argv) > 4 else 40)
    out = lines
    txt = '\n'.join(out)
    open(sys.argv[3], 'w').write(txt + '\n')
    print('# wrote', sys.argv[3], len(out), 'lines', file=sys.stderr)


if __name__ == '__main__':
    main()
