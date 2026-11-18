"""EMC E25 (review 2026-11-17, design-notes §8.24): report-only layout checks, run by build_routing.sh on each result.
KiCad python:  emc_report.py <board.kicad_pcb>
Prints one line per check and never fails the build; the numbers show E22/E23/E24-type slips after a reroute.
1 filter: copper path from each RF filter cap to its series resistor (rule: <= 5 mm; LED and switch inputs),
2 TVS order: on every connector line with a TVS, the stub from the connector->load path to the TVS pad
  (0 = the line runs through the TVS pad; rule: flow-through, report > 1 mm),
  and a GND via within 2.5 mm of every connector-line TVS and filter-cap GND pad,
3 FB-SW: the smallest gap between buck FB copper and SW copper on one layer (rule 5 of 2026-10-30: away from SW).
Path lengths run over the track centre lines (pad centre to pad centre, vias count 0), as in the review."""
import heapq, math, os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import routing_build as rb

MM = pcbnew.ToMM
FILTER_R = ['R19', 'R22', 'R25', 'R28', 'R34', 'R35', 'R36', 'R37']
FILTER_C = ['C50', 'C51', 'C52', 'C53', 'C14', 'C15', 'C16', 'C17']
FILTER_MAX = 5.0
CONNECTORS = ['J3', 'J4', 'J5']
TVS_VALUES = ('SMAJ', 'SMBJ', 'PESD', 'H5VL')
STUB_MAX = 1.0
FB_NET, SW_NET = 'Net-(U3-FB)', 'Net-(U3-SW)'
FB_SW_MIN = 2.0
GND_VIA_MAX = 2.5   # TVS / filter-cap GND pad centre to the nearest GND via (review 2026-11-17: 0.8-2.0 mm at the TVS)


class Net:
    """copper graph of one net: nodes are pad centres, track ends, via centres and T points"""

    def __init__(self, b, net, ox, oy):
        self.adj = {}
        xy = lambda p: (round(MM(p.x - ox), 4), round(MM(p.y - oy), 4))
        segs, vias, self.pads = [], [], {}
        for t in b.GetTracks():
            if t.GetNetname() != net:
                continue
            if t.GetClass() == 'PCB_VIA':
                vias.append((xy(t.GetPosition()), MM(t.GetWidth(pcbnew.F_Cu)) / 2))
            else:
                segs.append((t.GetLayer(), xy(t.GetStart()), xy(t.GetEnd()), MM(t.GetWidth()) / 2))
        pads = []
        for fp in b.GetFootprints():
            for p in fp.Pads():
                if p.GetNetname() != net:
                    continue
                key = fp.GetReference() + '.' + p.GetNumber()
                bb = p.GetBoundingBox()
                box = (MM(bb.GetLeft() - ox), MM(bb.GetTop() - oy), MM(bb.GetRight() - ox), MM(bb.GetBottom() - oy))
                c = xy(p.GetPosition())
                self.pads.setdefault(key, c)
                pads.append((key, c, box, p.HasHole(), p.IsOnLayer(pcbnew.F_Cu), p.IsOnLayer(pcbnew.B_Cu)))
        for lay, a, e, hw in segs:
            self.edge((lay, a), (lay, e), math.dist(a, e))
        # vias join the layers at their centre
        for c, r in vias:
            for lay, a, e, hw in segs:
                for q in (a, e):
                    if math.dist(q, c) <= r + 1e-3:
                        self.edge(('via', c), (lay, q), 0)
        # pads: a track end inside the pad joins the pad centre (length of the inside part counted as 0)
        for key, c, box, tht, onf, onb in pads:
            for lay, a, e, hw in segs:
                on = tht or (lay == pcbnew.F_Cu and onf) or (lay == pcbnew.B_Cu and onb)
                for q in (a, e):
                    if on and box[0] - 1e-3 <= q[0] <= box[2] + 1e-3 and box[1] - 1e-3 <= q[1] <= box[3] + 1e-3:
                        self.edge(('pad', key), (lay, q), 0)
        # T joints: a track end lying on another track of the same layer
        for lay, a, e, hw in segs:
            for q in (a, e):
                for lay2, a2, e2, hw2 in segs:
                    if lay2 != lay or q in (a2, e2):
                        continue
                    d, s = seg_dist(q, a2, e2)
                    if d <= max(hw, hw2) + 1e-3:
                        L = math.dist(a2, e2)
                        self.edge((lay, q), (lay, a2), s * L)
                        self.edge((lay, q), (lay, e2), (1 - s) * L)

    def edge(self, u, v, w):
        self.adj.setdefault(u, []).append((v, w))
        self.adj.setdefault(v, []).append((u, w))

    def dist(self, pa, pb):
        src, dst = ('pad', pa), ('pad', pb)
        if src not in self.adj or dst not in self.adj:
            return math.inf
        best = {src: 0.0}
        h, k = [(0.0, 0, src)], 0
        while h:
            d, _, u = heapq.heappop(h)
            if u == dst:
                return d
            if d > best.get(u, math.inf):
                continue
            for v, w in self.adj[u]:
                nd = d + w
                if nd < best.get(v, math.inf):
                    best[v] = nd
                    k += 1
                    heapq.heappush(h, (nd, k, v))
        return math.inf


def seg_dist(q, a, e):
    dx, dy = e[0] - a[0], e[1] - a[1]
    L2 = dx * dx + dy * dy
    s = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx + (q[1] - a[1]) * dy) / L2))
    return math.dist(q, (a[0] + s * dx, a[1] + s * dy)), s


def copper_pieces(b, net, ox, oy):
    """per layer: list of (kind, geometry) - track capsules and pad boxes"""
    out = {}
    for t in b.GetTracks():
        if t.GetNetname() == net and t.GetClass() != 'PCB_VIA':
            a, e = t.GetStart(), t.GetEnd()
            out.setdefault(t.GetLayer(), []).append(('seg', ((MM(a.x - ox), MM(a.y - oy)), (MM(e.x - ox), MM(e.y - oy))),
                                                     MM(t.GetWidth()) / 2))
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() != net:
                continue
            bb = p.GetBoundingBox()
            box = (MM(bb.GetLeft() - ox), MM(bb.GetTop() - oy), MM(bb.GetRight() - ox), MM(bb.GetBottom() - oy))
            for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
                if p.IsOnLayer(lay):
                    out.setdefault(lay, []).append(('box', box, fp.GetReference() + '.' + p.GetNumber()))
    return out


def samples(piece, step=0.05):
    if piece[0] == 'seg':
        (a, e), hw = piece[1], piece[2]
        n = max(1, int(math.dist(a, e) / step))
        return [((a[0] + (e[0] - a[0]) * i / n, a[1] + (e[1] - a[1]) * i / n), hw) for i in range(n + 1)]
    x1, y1, x2, y2 = piece[1]
    pts = []
    nx, ny = max(1, int((x2 - x1) / step)), max(1, int((y2 - y1) / step))
    for i in range(nx + 1):
        pts += [((x1 + (x2 - x1) * i / nx, y1), 0), ((x1 + (x2 - x1) * i / nx, y2), 0)]
    for j in range(ny + 1):
        pts += [((x1, y1 + (y2 - y1) * j / ny), 0), ((x2, y1 + (y2 - y1) * j / ny), 0)]
    return pts


def gap(pa, pb):
    best = math.inf
    sb = samples(pb)
    for q, hq in samples(pa):
        for r, hr in sb:
            best = min(best, math.dist(q, r) - hq - hr)
    return best


def main():
    b = pcbnew.LoadBoard(sys.argv[1])
    ox, oy = rb.origin(b)
    nets = {}
    get = lambda n: nets.setdefault(n, Net(b, n, ox, oy))
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    warn = 0
    # 1 filter cap <-> resistor
    for r in FILTER_R:
        for c in FILTER_C:
            if r not in fps or c not in fps:
                continue
            for pr in fps[r].Pads():
                for pc in fps[c].Pads():
                    n = pr.GetNetname()
                    if n and n == pc.GetNetname() and n not in rb.GND_NETS:
                        d = get(n).dist(r + '.' + pr.GetNumber(), c + '.' + pc.GetNumber())
                        bad = d > FILTER_MAX
                        warn += bad
                        print('emc filter %-4s %-4s %-22s path %6.1f mm%s' % (r, c, n[-22:], d, '  > %.0f mm  CHECK' % FILTER_MAX if bad else ''))
    # 2 TVS order on connector lines
    tvs = [fp for fp in b.GetFootprints() if fp.GetReference().startswith('D') and fp.GetValue().startswith(TVS_VALUES)]
    for j in CONNECTORS:
        if j not in fps:
            continue
        for pj in fps[j].Pads():
            n = pj.GetNetname()
            if not n or n in rb.GND_NETS or n.startswith('unconnected'):
                continue
            g = get(n)
            jk = j + '.' + pj.GetNumber()
            for d_ in tvs:
                for pt in d_.Pads():
                    if pt.GetNetname() != n:
                        continue
                    tk = d_.GetReference() + '.' + pt.GetNumber()
                    jt = g.dist(jk, tk)
                    worst, at = 0.0, ''
                    for key in g.pads:
                        if key.split('.')[0] in (j, d_.GetReference()):
                            continue
                        jx, tx = g.dist(jk, key), g.dist(tk, key)
                        if math.isinf(jx) or math.isinf(tx) or math.isinf(jt):
                            continue
                        stub = (jt + tx - jx) / 2
                        if stub > worst:
                            worst, at = stub, key
                    bad = worst > STUB_MAX
                    warn += bad
                    print('emc tvs    %-5s %-6s %-22s J->TVS %5.1f mm, TVS stub %4.1f mm%s%s' % (
                        jk, tk, n[-22:], jt, worst, ' (toward %s)' % at if at else '', '  CHECK' if bad else ''))
    # 2b GND via at every connector-line TVS and filter cap (rule: a via within 2 mm, not fill or grid stitching luck)
    gvias = [(MM(t.GetPosition().x - ox), MM(t.GetPosition().y - oy)) for t in b.GetTracks()
             if t.GetClass() == 'PCB_VIA' and t.GetNetname() == 'GND']
    tvs_j = {d_.GetReference() for d_ in tvs for pt in d_.Pads()
             if any(pt.GetNetname() == pj.GetNetname() for j in CONNECTORS if j in fps for pj in fps[j].Pads())}
    for ref in sorted(tvs_j) + [c for c in FILTER_C if c in fps]:
        for p in fps[ref].Pads():
            if p.GetNetname() == 'GND':
                q = (MM(p.GetPosition().x - ox), MM(p.GetPosition().y - oy))
                d = min((math.dist(q, v) for v in gvias), default=math.inf)
                bad = d > GND_VIA_MAX
                warn += bad
                if bad:
                    print('emc gnd    %-6s nearest GND via %.1f mm  > %.1f mm  CHECK' % (ref + '.' + p.GetNumber(), d, GND_VIA_MAX))
    # 3 FB <-> SW
    fb, sw = copper_pieces(b, FB_NET, ox, oy), copper_pieces(b, SW_NET, ox, oy)
    best, where = math.inf, ''
    for lay in fb:
        for pa in fb[lay]:
            for pb in sw.get(lay, []):
                g_ = gap(pa, pb)
                if g_ < best:
                    best, where = g_, b.GetLayerName(lay)
    bad = best < FB_SW_MIN
    warn += bad
    print('emc fb-sw  smallest gap %.2f mm on %s%s' % (best, where, '  < %.1f mm  CHECK' % FB_SW_MIN if bad else ''))
    print('emc report: %d item(s) to check (report only)' % warn)


main()
