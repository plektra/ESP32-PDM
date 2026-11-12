"""T-0241 generator for the channel bus; needs T-0241-next-build.patch applied (net_class, CORRIDOR_POURS,
PROFETS, THERMAL_PAD in routing_build.py / fixed_routes.py).
maze_route.py <geom.json> <nets (comma list) | @file> [out.py]: A* on a 0.1 mm grid over F.Cu/In2.Cu/B.Cu.
Connects the clusters of each net (cluster 1 = the one with the first item, joined to every other cluster one by
one), avoiding foreign copper (class clearance), foreign power-pour outlines, rule areas/router keep-outs, the
VS-In2 thermal fields and the 0.5 mm edge rule. In2 inside VS-In2 (the Q-0071 corridor) costs extra. Prints
fixed_routes.py lines (T/V)."""
import heapq, json, math, sys
from PIL import Image, ImageDraw

G = 0.1
L = ['F.Cu', 'In2.Cu', 'B.Cu']
geo = json.load(open(sys.argv[1]))
W, H = int(geo['size'][0] / G) + 1, int(geo['size'][1] / G) + 1
VIA_COST = 25.0
CORRIDOR_COST = 3.0
CORRIDOR_BAND = 1.5
IN2_COST = 1.3
EDGE = 0.5 + 0.1 + 0.06
EDGE_V = 0.5 + 0.3 + 0.06


def px(p):
    return (p[0] / G, p[1] / G)


def blank():
    return Image.new('1', (W, H), 0)


def draw_polys(d, polys, outline_w=0):
    for pl in polys:
        if len(pl) >= 3:
            d.polygon([px(p) for p in pl], fill=1, outline=1, width=outline_w) if outline_w else d.polygon([px(p) for p in pl], fill=1)


def edge_mask(m, e):
    d = ImageDraw.Draw(m)
    k = int(math.ceil(e / G))
    d.rectangle([0, 0, W, k], fill=1); d.rectangle([0, H - k - 1, W, H], fill=1)
    d.rectangle([0, 0, k, H], fill=1); d.rectangle([W - k - 1, 0, W, H], fill=1)


added = []   # (net, kind, layer, pts) of routed copper


def masks(net):
    tm = {l: blank() for l in L}
    vm = blank()
    cor = blank()
    td = {l: ImageDraw.Draw(tm[l]) for l in L}
    vd = ImageDraw.Draw(vm)
    for it in geo['items']:
        if it['net'] == net and net:
            continue
        for l in it['layers']:
            if l in td:
                draw_polys(td[l], it['t'][l])
                draw_polys(vd, it['v'][l])
        if 'gndtht' in it:
            draw_polys(td['In2.Cu'], it['gndtht'])
        if 'hole' in it:
            for l in L:
                draw_polys(td[l], it['hole'])
            draw_polys(vd, it['hole'])
    for z in geo['zones']:
        if z['kind'] == 'corridor':
            if z['net'] != net:
                draw_polys(ImageDraw.Draw(cor), z['poly'])
                # In2 slots only >= CORRIDOR_BAND inside the outline: a track never reaches the pour edge, so the
                # pour cannot be split (every corridor run is an internal slot with a via at each end)
                for pl in z['poly']:
                    td['In2.Cu'].line([px(p) for p in pl] + [px(pl[0])], fill=1, width=int(2 * CORRIDOR_BAND / G))
            continue
        if z['net'] == net and net:
            continue
        w = int(math.ceil(2 * (z.get('zc', 0) + 0.1 + 0.06) / G)) if z['kind'] == 'pour' else 4
        for l in z['layers']:
            if l in td:
                draw_polys(td[l], z['poly'])
                for pl in z['poly']:   # pour: a foreign track stays a zone clearance outside the outline
                    td[l].line([px(p) for p in pl] + [px(pl[0])], fill=1, width=w)
        if z['kind'] != 'pour' or z['layers'] != ['In2.Cu'] or True:
            draw_polys(vd, z['poly'], outline_w=5)
    for (n, kind, l, pts) in added:
        if n == net:
            continue
        if kind == 't':
            for d, wmm in ((td[l], 1.0), (vd, 1.4)):   # round joins: a disc at every vertex
                d.line([px(p) for p in pts], fill=1, width=int(round(wmm / G)))
                for p in pts:
                    x, y = px(p); r = wmm / 2 / G
                    d.ellipse([x - r, y - r, x + r, y + r], fill=1)
        else:
            x, y = px(pts[0])
            for l2 in L:
                r = 0.66 / G
                td[l2].ellipse([x - r, y - r, x + r, y + r], fill=1)
            r = 0.86 / G
            vd.ellipse([x - r, y - r, x + r, y + r], fill=1)
    for l in L:
        edge_mask(tm[l], EDGE)
    edge_mask(vm, EDGE_V)
    return ({l: bytearray(tm[l].tobytes('raw', '1;I') if False else tm[l].convert('L').tobytes()) for l in L},
            bytearray(vm.convert('L').tobytes()), bytearray(cor.convert('L').tobytes()))


def cells_of(polys):
    m = blank(); draw_polys(ImageDraw.Draw(m), polys)
    bb = m.getbbox()
    if not bb:
        return set()
    data = m.convert('L').tobytes()
    s = set()
    for y in range(bb[1], bb[3]):
        row = y * W
        for x in range(bb[0], bb[2]):
            if data[row + x]:
                s.add(row + x)
    return s


def route(net, src_cl, dst_cl, tm, vm, cor):
    own = [it for it in geo['items'] if it['net'] == net]
    start = {l: set() for l in L}; goal = {l: set() for l in L}
    for it in own:
        for l in it['layers']:
            if l not in start:
                continue
            c = cells_of(it['raw'][l])
            if it['cl'] in src_cl:
                start[l] |= c
            elif it['cl'] in dst_cl:
                goal[l] |= c
    for (n, kind, l, pts) in added:      # copper routed earlier for this net belongs to the source side
        pass
    gpts = [(c % W, c // W) for l in L for c in goal[l]]
    if not gpts or not any(start.values()):
        return None
    gx0, gx1 = min(p[0] for p in gpts), max(p[0] for p in gpts)
    gy0, gy1 = min(p[1] for p in gpts), max(p[1] for p in gpts)

    def h(c):
        x, y = c % W, c // W
        dx = max(gx0 - x, 0, x - gx1); dy = max(gy0 - y, 0, y - gy1)
        return math.hypot(dx, dy)
    own_cells = {l: start[l] | goal[l] for l in L}
    dist = {}; prev = {}; pq = []
    for li, l in enumerate(L):
        for c in start[l]:
            dist[(li, c)] = 0.0
            heapq.heappush(pq, (h(c), 0.0, li, c))
    nb = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)]
    n = 0
    while pq:
        f, g, li, c = heapq.heappop(pq)
        if g > dist.get((li, c), 1e18):
            continue
        n += 1
        if n > 3000000:
            return None
        if c in goal[L[li]]:
            path = [(li, c)]
            while path[-1] in prev:
                path.append(prev[path[-1]])
            return path[::-1]
        x, y = c % W, c // W
        tml = tm[L[li]]
        for dx, dy, w in nb:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H):
                continue
            nc = ny * W + nx
            if tml[nc] and nc not in own_cells[L[li]]:
                continue
            cost = w * (IN2_COST * (CORRIDOR_COST if cor[nc] else 1.0) if li == 1 else 1.0)
            ng = g + cost
            if ng < dist.get((li, nc), 1e18):
                dist[(li, nc)] = ng; prev[(li, nc)] = (li, c)
                heapq.heappush(pq, (ng + h(nc), ng, li, nc))
        if not vm[c] and c not in own_cells[L[li]]:
            for lj in range(3):
                if lj != li and (not tm[L[lj]][c]):
                    ng = g + VIA_COST
                    if ng < dist.get((lj, c), 1e18):
                        dist[(lj, c)] = ng; prev[(lj, c)] = (li, c)
                        heapq.heappush(pq, (ng + h(c), ng, lj, c))
    return None


def emit(net, path):
    lines = []
    segs = []; cur = [path[0]]
    for st in path[1:]:
        if st[0] != cur[-1][0]:
            segs.append(cur); cur = [st]
        else:
            cur.append(st)
    segs.append(cur)
    for i, s in enumerate(segs):
        pts = [((c % W) * G, (c // W) * G) for _, c in s]
        # keep corners only
        keep = [pts[0]]
        for a, b2, c2 in zip(pts, pts[1:], pts[2:]):
            if (b2[0] - a[0], b2[1] - a[1]) != (c2[0] - b2[0], c2[1] - b2[1]) and \
               not (abs((b2[0] - a[0]) - (c2[0] - b2[0])) < 1e-6 and abs((b2[1] - a[1]) - (c2[1] - b2[1])) < 1e-6):
                keep.append(b2)
        keep.append(pts[-1])
        keep = [(round(x, 2), round(y, 2)) for x, y in keep]
        if len(keep) >= 2 and keep[0] != keep[-1]:
            lines.append("T(%r, %r, %s)" % (net, L[s[0][0]], ', '.join('(%.2f, %.2f)' % p for p in keep)))
            added.append((net, 't', L[s[0][0]], keep))
        if i + 1 < len(segs):
            p = keep[-1] if keep else pts[-1]
            lines.append("V(%r, %.2f, %.2f)" % (net, p[0], p[1]))
            added.append((net, 'v', None, [p]))
    return lines


if __name__ == '__main__':
    arg = sys.argv[2]
    nets = open(arg[1:]).read().split() if arg.startswith('@') else arg.split(',')
    out = []
    for net in nets:
        cls = sorted({it['cl'] for it in geo['items'] if it['net'] == net})
        if len(cls) < 2:
            print('#', net, 'already one cluster', file=sys.stderr); continue
        tm, vm, cor = masks(net)
        done = {cls[0]}
        rest = set(cls[1:])
        ok = True
        while rest:
            best = None
            path = route(net, done, rest, tm, vm, cor)
            if not path:
                print('#', net, 'FAILED clusters', sorted(rest), file=sys.stderr); ok = False; break
            # which cluster did we reach
            li, c = path[-1]
            hit = [it['cl'] for it in geo['items'] if it['net'] == net and it['cl'] in rest and L[li] in it['layers']
                   and c in cells_of(it['raw'][L[li]])]
            lines = emit(net, path)
            out.append('# %s: clusters %s -> %s' % (net, sorted(done), hit[:1]))
            out += lines
            done |= set(hit[:1]); rest -= set(hit[:1])
            for it in geo['items']:   # new copper joins the source side for the next leg
                pass
            tm, vm, cor = masks(net)
        print('#', net, 'ok' if ok else 'partial', file=sys.stderr)
    txt = '\n'.join(out)
    print(txt)
    if len(sys.argv) > 3:
        open(sys.argv[3], 'w').write(txt + '\n')
