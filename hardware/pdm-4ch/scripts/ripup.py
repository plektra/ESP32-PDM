"""Decision 214: targeted rip-up for the pdm-4ch routing.
ripup.py <geom.json> <fixed_routes.py> <plan.json> [net ...]   |   ripup.py --apply <fixed_routes.py> <plan.json>
geom.json comes from geom_export.py on the build base (all current copper). For each signal net that is still in
several clusters:
1. a blocker search on maze_route.py's own masks finds the cheapest way to join it when the movable copper of other
   nets may be crossed at a price (movable = listed in fixed_routes.py from the T-0236 harvest on, net not in
   KEEP_NETS). Pads, locked copper, the protected routes (CAN, USB, CC1, J6 bundle), GND, power pours and keep-outs
   stay hard. The nets whose movable copper the path crosses are the blockers.
2. a trial removes only the crossed fixed_routes.py lines of the blockers (segment mode; whole blocker nets as a
   fallback), routes the net first and then repairs the blockers with maze_route.py's router (or jointly with
   reroute.py's negotiated congestion), and counts the clusters left open.
3. the trial is kept only when fewer clusters stay open than before. The first kept trial is written to plan.json
   (nets, fixed_routes.py lines to delete, stub lines for their locked copper, new lines) and the script stops: the
   caller applies it (apply_plan in this file), rebuilds the geometry and runs it again.
Nets named on the command line are tried first (default: all open signal nets, fewest blockers first)."""
import collections, heapq, importlib.util, json, math, os, re, sys

if sys.argv[1] == '--apply':   # ripup.py --apply <fixed_routes.py> <plan.json>
    _APPLY = sys.argv[2:4]
    GEO = None
else:
    _APPLY = None
    GEO, FR, PLAN = sys.argv[1], sys.argv[2], sys.argv[3]
FIRST = sys.argv[4:]


def apply_plan(fr_path, plan_path):
    """apply plan.json to fixed_routes.py: delete the movable lines of the rerouted nets, add them to REROUTED_NETS,
    append their locked stubs and the new lines"""
    plan = json.load(open(plan_path))
    src = open(fr_path).read().split('\n')
    dele = set(plan['delete'])
    out = [l for i, l in enumerate(src, 1) if i not in dele]
    txt = '\n'.join(out)
    m = re.search(r"^REROUTED_NETS = (\[.*?\])$", txt, re.M)
    new = sorted(set(eval(m.group(1))) | set(plan['nets']))
    txt = txt[:m.start()] + 'REROUTED_NETS = %r' % new + txt[m.end():]
    txt = txt.rstrip('\n') + '\n\n# ---- Decision 214 rip-up: %s (with %s), open clusters %d -> %d\n' % (
        plan['net'], ', '.join(n for n in plan['nets'] if n != plan['net']) or '-', plan['before'], plan['after'])
    txt += '\n'.join(plan['stubs'] + plan['lines']) + '\n'
    open(fr_path, 'w').write(txt)


if _APPLY:
    apply_plan(*_APPLY)
    sys.exit(0)
_argv = sys.argv
sys.argv = [sys.argv[0], GEO, 'x']
_spec = importlib.util.spec_from_file_location('mz', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maze_route.py'))
mz = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(mz)
sys.argv = _argv
W, H, G, L = mz.W, mz.H, mz.G, mz.L

KEEP_NETS = {'GND', 'GND_CAN', 'VS', '/VBAT_IN', '/VBAT_FL', '/OUT1', '/OUT2', '/OUT3', '/OUT4',
             '/USB_DP', '/USB_DN', 'Net-(J3-CC1)', '/IO35', '/IO36', '/IO37', '/IO42', '/RXD0', '/TXD0',
             '/CAN/CANH_BUS', '/CAN/CANL_BUS', '/CAN/CANH_XCVR', '/CAN/CANL_XCVR'}
HARVEST_MARK = '# ---- Routed copper of the T-0236 build 2 board'
PEN = 300.0


# ---- fixed_routes.py lines (line number per T/V call)
def fr_lines(path):
    src = open(path).read().split('\n')
    first = next(i + 1 for i, l in enumerate(src) if l.startswith(HARVEST_MARK))
    recs = []
    for i, l in enumerate(src, 1):
        m = re.match(r"\s*([TV])\((.*)\)\s*(#.*)?$", l)
        if not m or i < first or l.rstrip().endswith('# keep'):   # '# keep': a deliberate stub, never ripped
            continue
        recs.append((i, l))
    return src, first, recs


def _call(line):
    """parse one T(...)/V(...) line -> ('T', net, layer, pts) / ('V', net, None, [pt])"""
    out = []

    def T(net, layer, *pts, w=0.2):
        out.append(('T', net, layer, [tuple(p) for p in pts]))

    def V(net, x, y, size=0.6, drill=0.3):
        out.append(('V', net, None, [(x, y)]))
    try:
        exec(line.strip(), {'T': T, 'V': V})
    except Exception:
        return None
    return out[0] if out else None


def rkey(net, pts):
    return (net, tuple(sorted((round(x, 2), round(y, 2)) for x, y in pts)))


def item_key(it):
    if 'at' in it:
        return rkey(it['net'], [it['at']])
    if 'seg' in it:
        s = it['seg']; return rkey(it['net'], [(s[0], s[1]), (s[2], s[3])])
    return None


src, FIRST_LINE, recs = fr_lines(FR)
listed_keys = set()   # every T/V item fixed_routes.py lists (any section): such copper needs no stub line
for _l in src:
    _c = _call(_l) if re.match(r"\s*[TV]\(", _l) else None
    if _c:
        if _c[0] == 'V':
            listed_keys.add(rkey(_c[1], _c[3]))
        else:
            for _a, _b in zip(_c[3], _c[3][1:]):
                listed_keys.add(rkey(_c[1], [_a, _b]))
movable_keys = {}      # key -> line number
lines_of_net = collections.defaultdict(list)
for i, l in recs:
    c = _call(l)
    if not c:
        continue
    kind, net, layer, pts = c
    lines_of_net[net].append(i)
    if kind == 'V':
        movable_keys[rkey(net, pts)] = i
    else:
        for a, b in zip(pts, pts[1:]):
            movable_keys[rkey(net, [a, b])] = i
ALL = mz.geo['items']


def movable(it):
    return it['net'] not in KEEP_NETS and not it['ref'] and item_key(it) in movable_keys


def clusters_of(items, net):
    return sorted({it['cl'] for it in items if it['net'] == net})


# ---- re-clustering after removing copper (union-find on shared raster cells)
def recluster(items, nets):
    nid = [100000000]
    for net in nets:
        own = [it for it in items if it['net'] == net]
        par = list(range(len(own)))

        def f(a):
            while par[a] != a:
                par[a] = par[par[a]]; a = par[a]
            return a
        seen = {}
        for k, it in enumerate(own):
            for l, ps in it['raw'].items():
                for c in mz.cells_of(ps):
                    o = seen.get((l, c))
                    if o is None:
                        seen[(l, c)] = k
                    else:
                        par[f(k)] = f(o)
        roots = {}
        for k, it in enumerate(own):
            r = f(k)
            if r not in roots:
                nid[0] += 1; roots[r] = nid[0]
            it['cl'] = roots[r]


def route_nets(order):
    """maze_route.py's main loop for the given nets on the current mz.geo; returns (open clusters, lines)"""
    lines = []; open_ = 0
    for net in order:
        cls = sorted({it['cl'] for it in mz.geo['items'] if it['net'] == net})
        if len(cls) < 2:
            continue
        tm, vm, cor = mz.masks(net)
        rest = set(cls); tried = set(); comps = 0
        while rest:
            cand = [c for c in sorted(rest) if c not in tried]
            if not cand:
                break
            seed = cand[0]; tried.add(seed); comps += 1
            done = {seed}; rest.discard(seed)
            laid = {l: set() for l in L}
            while rest:
                path = mz.route(net, done, rest, tm, vm, cor, laid)
                if not path:
                    break
                li, c = path[-1]
                hit = [it['cl'] for it in mz.geo['items'] if it['net'] == net and it['cl'] in rest and L[li] in it['layers']
                       and c in mz.erode(mz.cells_of(it['raw'][L[li]]))]
                if not hit:
                    break
                lines.append('# %s leg' % net)
                lines += mz.emit(net, path)
                done.add(hit[0]); rest.discard(hit[0]); tried |= done
                for lj, cj in path:
                    laid[L[lj]].add(cj)
        open_ += comps - 1
    return open_, lines


# ---- blocker search: movable foreign copper crossable at PEN per item
def blockers(net):
    hard_items = [it for it in ALL if it['net'] == net or not movable(it)]
    soft = [it for it in ALL if it['net'] != net and movable(it)]
    mz.geo['items'] = hard_items; mz.added.clear()
    tm, vm, cor = mz.masks(net)
    from PIL import Image, ImageDraw
    SL = {l: Image.new('I', (W, H), 0) for l in L}; VL = Image.new('I', (W, H), 0)
    for i, it in enumerate(soft):
        for l in it['layers']:
            if l in SL:
                for pl in it['t'][l]:
                    if len(pl) >= 3:
                        ImageDraw.Draw(SL[l]).polygon([mz.px(p) for p in pl], fill=i + 1)
                for pl in it['v'][l]:
                    if len(pl) >= 3:
                        ImageDraw.Draw(VL).polygon([mz.px(p) for p in pl], fill=i + 1)
    SLd = {l: SL[l].tobytes() for l in L}
    import array
    SLa = {l: array.array('i', SLd[l]) for l in L}; VLa = array.array('i', VL.tobytes())
    cls = clusters_of(ALL, net)
    seed = cls[0]
    start = {l: set() for l in L}; goal = {l: set() for l in L}
    for it in ALL:
        if it['net'] != net:
            continue
        for l in it['layers']:
            if l in start:
                c = mz.erode(mz.cells_of(it['raw'][l]))
                (start if it['cl'] == seed else goal)[l] |= c
    own = {l: start[l] | goal[l] for l in L}
    gp = [(c % W, c // W) for l in L for c in goal[l]]
    if not gp:
        return None
    gx0, gx1 = min(p[0] for p in gp), max(p[0] for p in gp); gy0, gy1 = min(p[1] for p in gp), max(p[1] for p in gp)
    hh = lambda c: math.hypot(max(gx0 - c % W, 0, c % W - gx1), max(gy0 - c // W, 0, c // W - gy1))
    dist = {}; prev = {}; pq = []
    for li, l in enumerate(L):
        for c in start[l]:
            dist[(li, c)] = 0.0; heapq.heappush(pq, (hh(c), 0.0, li, c))
    nb = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    found = None; n = 0
    while pq:
        f, g, li, c = heapq.heappop(pq)
        if g > dist.get((li, c), 1e18):
            continue
        n += 1
        if n > 3000000:
            break
        if c in goal[L[li]]:
            found = (li, c); break
        x, y = c % W, c // W; cl = SLa[L[li]][c]
        for dx, dy, w in nb:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            nc = ny * W + nx
            if tm[L[li]][nc] and nc not in own[L[li]]:
                continue
            nl = SLa[L[li]][nc]
            ng = g + w * (mz.IN2_COST if li == 1 else 1.0) + (PEN if nl and nl != cl else 0)
            if ng < dist.get((li, nc), 1e18):
                dist[(li, nc)] = ng; prev[(li, nc)] = (li, c); heapq.heappush(pq, (ng + hh(nc), ng, li, nc))
        if not vm[c] and c not in own[L[li]]:
            vl = VLa[c]
            for lj in range(3):
                if lj != li and not tm[L[lj]][c]:
                    ng = g + mz.VIA_COST + (PEN if vl and vl != cl else 0)
                    if ng < dist.get((lj, c), 1e18):
                        dist[(lj, c)] = ng; prev[(lj, c)] = (li, c); heapq.heappush(pq, (ng + hh(c), ng, lj, c))
    mz.geo['items'] = ALL
    if not found:
        return None
    blk = set(); crossed = set(); c = found
    while c in prev:
        p = prev[c]
        lab = VLa[c[1]] if p[0] != c[0] else SLa[L[c[0]]][c[1]]
        if lab:
            blk.add(soft[lab - 1]['net']); crossed.add(movable_keys[item_key(soft[lab - 1])])
        c = p
    return sorted(blk - {net}), crossed


_RR = []


def negotiator():
    """reroute.py (negotiated congestion + legalization) on the same geometry, imported once"""
    if not _RR:
        os.environ['REROUTE_GEO'] = GEO
        sp = importlib.util.spec_from_file_location('rr', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reroute.py'))
        rr = importlib.util.module_from_spec(sp); sp.loader.exec_module(rr); _RR.append(rr)
    return _RR[0]


def trial(nets_t, order, joint=False, lines_del=None):
    """lines_del: rip only the movable items of these fixed_routes.py lines (segment mode); None: every movable
    item of nets_t (whole-net mode)"""
    if lines_del is None:
        gone = lambda it: it['net'] in nets_t and movable(it)
    else:
        gone = lambda it: movable(it) and movable_keys[item_key(it)] in lines_del
    items = [dict(it) for it in ALL if not gone(it)]
    recluster(items, nets_t)
    before = sum(len(clusters_of(ALL, n)) - 1 for n in nets_t)
    if joint:   # all nets of the group together (negotiated congestion), then legalized
        rr = negotiator()
        rr.mz.geo['items'] = items; rr.mz.added.clear()
        lines, after = rr.negotiate(list(order), 10, log=False)
        rr.mz.geo['items'] = ALL
    else:
        mz.geo['items'] = items; mz.added.clear()
        after, lines = route_nets(order)
        mz.geo['items'] = ALL
    stubs = []
    for it in items:   # locked (not movable) track/via copper of the rerouted nets: kept as listed stubs
        if it['net'] in nets_t and not it['ref'] and not movable(it) and item_key(it) not in listed_keys:
            if 'at' in it:
                stubs.append("V(%r, %.6f, %.6f, size=%.3f, drill=%.3f)" % (it['net'], it['at'][0], it['at'][1], it.get('size', 0.6), it.get('drill', 0.3)))
            elif 'seg' in it:
                s = it['seg']
                stubs.append("T(%r, %r, (%.6f, %.6f), (%.6f, %.6f), w=%.3f)" % (it['net'], it['layer'], s[0], s[1], s[2], s[3], it.get('w', 0.2)))
    return before, after, lines, stubs


def main():
    open_nets = sorted({it['net'] for it in ALL if it['cl'] and len(clusters_of(ALL, it['net'])) > 1})
    order = [n for n in FIRST if n in open_nets] + [n for n in open_nets if n not in FIRST]
    print('# open signal nets:', len(open_nets), file=sys.stderr, flush=True)
    for net in order:
        if net in KEEP_NETS:
            continue
        r = blockers(net)
        if r is None:
            print('#', net, 'no path even across movable copper', file=sys.stderr, flush=True); continue
        b, crossed = r
        nets_t = [net] + b
        whole = sorted({i for n in nets_t for i in lines_of_net.get(n, [])})
        for ordr, joint, ld in (([net] + b, False, crossed), ([net] + b, True, crossed),
                                ([net] + b, False, None), ([net] + b, True, None)):
            before, after, lines, stubs = trial(set(nets_t), ordr, joint, ld)
            print('# %s: blockers %s (%s), open %d -> %d%s' % (net, b, 'segments %d' % len(ld) if ld is not None
                  else 'whole nets', before, after, ' (joint)' if joint else ''), file=sys.stderr, flush=True)
            if after < before:
                dele = sorted(ld) if ld is not None else whole
                json.dump({'net': net, 'nets': nets_t, 'before': before, 'after': after, 'delete': dele,
                           'stubs': stubs, 'lines': lines}, open(PLAN, 'w'), indent=0)
                print('# PLAN', net, nets_t, before, '->', after, file=sys.stderr)
                return
    print('# no improving trial', file=sys.stderr)
    json.dump(None, open(PLAN, 'w'))



if __name__ == '__main__':
    main()
