"""Routing build steps for pdm-4ch (decision 163). Runs under KiCad's Python (pcbnew).

Called by build_routing.sh; every step works on files in a work folder, never on the repo board.

  prep  <board> <work>        lock existing copper on the first build, drop unlocked tracks/vias, add fixed routes,
                              clear fills -> work/base.kicad_pcb, pour baseline -> work/baseline.json,
                              router copy (power outlines as planes minus pad escapes, keep-outs on all layers,
                              GND pours removed except the In1 planes) -> work/route.dsn
  apply <work> <ses> <out>    add the routed wires/vias from the SES to base, pour, stitch, clean, check pours
                              -> out.kicad_pcb and out.json (pour check)

Coordinates in fixed_routes.py are mm from the board's top-left outline corner.
"""
import json, os, re, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixed_routes  # noqa: E402

M = pcbnew.FromMM
MM = pcbnew.ToMM
POWER_NETS = {'VS', '/VBAT_IN', '/VBAT_FL', '/OUT1', '/OUT2', '/OUT3', '/OUT4'}
GND_NETS = {'GND', 'GND_CAN'}
ALL_CU = (pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
# keep-outs on all copper layers for the router (mm, board-relative): antenna strip, CAN barrier, JP30, JP1
KEEPOUTS = {
    'antenna': (45.85, 0.0, 92.5, 4.5),
    'can-barrier': (67.5, 47.3, 75.7, 75.1),
    'can-barrier-top': (75.7, 47.3, 100.1, 51.4),
    'jp30': (35.1, 46.0, 41.1, 48.0),
    'jp1': (29.05, 60.6, 29.55, 61.8),
}
# DSN net classes: (width um, clearance um, layers)
SIG_LAYERS = ('F.Cu', 'In2.Cu', 'B.Cu')       # no signal on In1.Cu (EMC rule 3)
HV = {'VS', '/VBAT_IN'}
P6 = {'Net-(D2-K)', 'Net-(D3-K)', 'Net-(F1-Pad2)', 'Net-(F4-Pad2)', '/Analog interface/SW_SUPPLY', 'Net-(F3-Pad1)',
      'Net-(J4-Pin_2)', 'Net-(D11-K)', 'Net-(C22-Pad2)', '/OUT1', '/OUT2', '/OUT3', '/OUT4', '/VBAT_FL'}
P4 = {'Net-(F2-Pad1)', 'Net-(C4-Pad1)', 'Net-(D3-A)', 'Net-(U5-VCC2)', 'Net-(Q30-G)', 'Net-(U30-VCAP)'}
BUCK_TOP = {'Net-(U3-SW)', 'Net-(U3-CB)'}      # buck SW/CB on F.Cu only (no via in the loop)


def origin(b):
    box = b.GetBoardEdgesBoundingBox()
    return box.GetX(), box.GetY()


def P(b, x, y):
    ox, oy = origin(b)
    return pcbnew.VECTOR2I(ox + M(x), oy + M(y))


def fill(b):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def islands(b):
    """filled islands per copper zone (name|layer -> count, area mm2)"""
    out = {}
    for z in b.Zones():
        if z.GetIsRuleArea():
            continue
        for lay in z.GetLayerSet().Seq():
            if lay not in ALL_CU:
                continue
            ps = z.GetFilledPolysList(lay)
            out['%s|%s' % (z.GetZoneName(), b.GetLayerName(lay))] = [ps.OutlineCount(), round(ps.Area() / 1e12, 1)]
    return out


def add_fixed(b):
    """fixed tracks/vias from fixed_routes.py, locked; skipped when an identical item is already there"""
    have = set()
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            have.add(('v', t.GetPosition().x, t.GetPosition().y))
        else:
            have.add(('t', t.GetLayer(), *sorted([(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)])))
    n = 0
    for r in fixed_routes.TRACKS:
        net = b.FindNet(r['net']); lay = b.GetLayerID(r['layer'])
        pts = [P(b, *p) for p in r['pts']]
        for a, e in zip(pts, pts[1:]):
            key = ('t', lay, *sorted([(a.x, a.y), (e.x, e.y)]))
            if key in have:
                continue
            t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(e); t.SetWidth(M(r.get('width', 0.2)))
            t.SetLayer(lay); t.SetNet(net); t.SetLocked(True); b.Add(t); have.add(key); n += 1
    for r in fixed_routes.VIAS:
        p = P(b, *r['at'])
        if ('v', p.x, p.y) in have:
            continue
        v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetWidth(M(r.get('size', 0.6))); v.SetDrill(M(r.get('drill', 0.3))); v.SetNet(b.FindNet(r['net']))
        v.SetLocked(True); b.Add(v); n += 1
    return n


def rect_poly(x1, y1, x2, y2):
    ps = pcbnew.SHAPE_POLY_SET(); ps.NewOutline()
    for x, y in ((x1, y1), (x2, y1), (x2, y2), (x1, y2)):
        ps.Append(int(x), int(y))
    return ps


def keepout(b, name, x1, y1, x2, y2):
    z = pcbnew.ZONE(b); z.SetIsRuleArea(True)
    z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)
    ls = pcbnew.LSET()
    for l in ALL_CU:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    a = P(b, x1, y1); e = P(b, x2, y2)
    ps = rect_poly(a.x, a.y, e.x, e.y); ps.thisown = 0
    z.SetOutline(ps); z.SetZoneName(name); b.Add(z)


def prep(board, work):
    b = pcbnew.LoadBoard(board)
    tracks = list(b.GetTracks())
    first = not any(t.IsLocked() for t in tracks)
    if first:   # first build: the stage 4-5 power copper and the T-0207/T-0208 links become fixed copper
        for t in tracks:
            t.SetLocked(True)
        for z in b.Zones():
            z.SetLocked(True)
    removed = 0
    for t in tracks:
        if not t.IsLocked():
            b.Remove(t); removed += 1
    nfix = add_fixed(b)
    fill(b)
    json.dump(islands(b), open(os.path.join(work, 'baseline.json'), 'w'), indent=0)
    for z in b.Zones():
        z.UnFill()
    pcbnew.SaveBoard(os.path.join(work, 'base.kicad_pcb'), b)
    print('prep: first build (locked existing copper)' if first else 'prep: locked copper kept',
          '| removed unlocked', removed, '| fixed routes added', nfix, flush=True)

    # ---- router copy
    for z in list(b.Zones()):
        if z.GetIsRuleArea():
            ls = pcbnew.LSET()
            for l in ALL_CU:
                ls.AddLayer(l)
            z.SetLayerSet(ls)            # hole keep-outs on all four layers
            continue
        net = z.GetNetname()
        if net in GND_NETS:
            if z.GetLayer() != pcbnew.In1_Cu:
                b.Remove(z)              # GND pours on F/In2/B are refilled after routing
            continue
        # power outline = keep-out for foreign nets, minus a small escape around each foreign pad/via/track end
        lay = z.GetLayer()
        ol = pcbnew.SHAPE_POLY_SET(z.Outline())
        cut = pcbnew.SHAPE_POLY_SET()
        esc = M(fixed_routes.ESCAPE_MM)
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() == net or not pad.IsOnLayer(lay):
                    continue
                bb = pad.GetBoundingBox()
                cut.Append(rect_poly(bb.GetLeft() - esc, bb.GetTop() - esc, bb.GetRight() + esc, bb.GetBottom() + esc))
        for t in b.GetTracks():
            if t.GetNetname() == net:
                continue
            if t.GetClass() == 'PCB_VIA':
                pts = [t.GetPosition()]
            elif t.GetLayer() == lay:
                pts = [t.GetStart(), t.GetEnd()]
            else:
                continue
            for p in pts:
                cut.Append(rect_poly(p.x - esc - M(0.3), p.y - esc - M(0.3), p.x + esc + M(0.3), p.y + esc + M(0.3)))
        if cut.OutlineCount():
            cut.Simplify()
            ol.BooleanSubtract(cut)
        ol.Fracture()
        if ol.OutlineCount() == 0:
            b.Remove(z); continue
        ko = pcbnew.SHAPE_POLY_SET(ol)
        ol.thisown = 0
        z.SetOutline(ol)
        # Freerouting lets foreign nets cross a plane; the same outline as a keep-out protects the pour
        k = pcbnew.ZONE(b); k.SetIsRuleArea(True)
        k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowZoneFills(False)
        k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
        k.SetLayer(lay); ko.thisown = 0; k.SetOutline(ko); k.SetZoneName('pour-' + z.GetZoneName()); b.Add(k)
    for name, r in KEEPOUTS.items():
        keepout(b, name, *r)
    # board-edge strip: the router does not know the 0.5 mm copper-to-edge rule
    bb = b.GetBoardEdgesBoundingBox(); W = MM(bb.GetWidth()); H = MM(bb.GetHeight()); e = fixed_routes.EDGE_STRIP_MM
    for i, r in enumerate(((0, 0, W, e), (0, H - e, W, H), (0, 0, e, H), (W - e, 0, W, H))):
        keepout(b, 'edge%d' % i, *r)
    rp = os.path.join(work, 'route.kicad_pcb')
    pcbnew.SaveBoard(rp, b)
    raw = os.path.join(work, 'raw.dsn')
    ok = pcbnew.ExportSpecctraDSN(b, raw)
    print('dsn export', ok, flush=True)
    patch_classes(raw, os.path.join(work, 'route.dsn'))


def patch_classes(src, dst):
    t = open(src).read()
    m = re.search(r'\n    \(class kicad_default(.*?)\n      \(circuit', t, re.S)
    nets = [n.strip('"') for n in re.findall(r'"[^"]*"|[^\s"()]+', m.group(1))]
    via = re.search(r'\(use_via\s+"?([^")\s]+)', t[m.start():]).group(1)
    groups = {}
    for n in nets:
        g = ('hv' if n in HV else 'buck' if n in BUCK_TOP else 'p6' if n in P6 else 'p4' if n in P4
             else 'gnd' if n in GND_NETS else 'v3' if n == '+3V3' else 'sig')
        groups.setdefault(g, []).append(n)
    rules = fixed_routes.CLASSES
    out = []
    for g, ns in groups.items():
        w, c, layers = rules[g]
        q = ' '.join('"%s"' % n for n in ns)
        lay = '\n        (use_layer %s)' % ' '.join(layers) if layers else ''
        out.append(f'    (class {g} {q}\n      (circuit\n        (use_via "{via}"){lay}\n      )\n'
                   f'      (rule\n        (width {w})\n        (clearance {c})\n      )\n    )')
    rb = t.index('(rule', m.end()); rc = t.index('\n      )', rb); ce = t.index('\n    )', rc + 1) + len('\n    )')
    open(dst, 'w').write(t[:m.start()] + '\n' + '\n'.join(out) + t[ce:])
    print('classes', {g: len(v) for g, v in groups.items()}, flush=True)


# ---------------------------------------------------------------- SES apply
def sexp(s):
    st = [[]]
    for tk in re.findall(r'\(|\)|"[^"]*"|[^\s()]+', s):
        if tk == '(':
            st.append([])
        elif tk == ')':
            x = st.pop(); st[-1].append(x)
        else:
            st[-1].append(tk.strip('"') if tk.startswith('"') else tk)
    return st[0][0]


def kids(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def apply(work, ses, out):
    b = pcbnew.LoadBoard(os.path.join(work, 'base.kicad_pcb'))
    ox, oy = origin(b)
    have = set()
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            have.add(('v', round(MM(t.GetPosition().x), 2), round(MM(t.GetPosition().y), 2)))
        else:
            have.add(('t', b.GetLayerName(t.GetLayer()), *sorted([(round(MM(t.GetStart().x), 2), round(MM(t.GetStart().y), 2)),
                                                                   (round(MM(t.GetEnd().x), 2), round(MM(t.GetEnd().y), 2))])))
    S = sexp(open(ses).read())
    routes = kids(S, 'routes')[0]
    res = kids(routes, 'resolution')[0]
    div = {'um': 1000.0, 'mm': 1.0, 'mil': 1000 / 25.4}[res[1]] * float(res[2])

    def pt(x, y):   # SES -> KiCad internal (SES y is up)
        return pcbnew.VECTOR2I(M(float(x) / div), M(-float(y) / div))
    nw = nv = 0
    for net in kids(kids(routes, 'network_out')[0], 'net'):
        n = b.FindNet(net[1])
        for w in net[2:]:
            if not isinstance(w, list):
                continue
            if w[0] == 'wire':
                p = kids(w, 'path')[0]; lay = p[1]; width = M(float(p[2]) / div); c = p[3:]
                pts = [pt(c[i], c[i + 1]) for i in range(0, len(c), 2)]
                for a, e in zip(pts, pts[1:]):
                    key = ('t', lay, *sorted([(round(MM(a.x), 2), round(MM(a.y), 2)), (round(MM(e.x), 2), round(MM(e.y), 2))]))
                    if key in have or (a.x == e.x and a.y == e.y):
                        continue
                    t = pcbnew.PCB_TRACK(b); t.SetStart(a); t.SetEnd(e); t.SetWidth(width)
                    t.SetLayer(b.GetLayerID(lay)); t.SetNet(n); b.Add(t); nw += 1
            elif w[0] == 'via':
                p = pt(w[2], w[3])
                if ('v', round(MM(p.x), 2), round(MM(p.y), 2)) in have:
                    continue
                m = re.search(r'_(\d+):(\d+)_um', w[1])
                v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                v.SetWidth(M(int(m.group(1)) / 1000)); v.SetDrill(M(int(m.group(2)) / 1000)); v.SetNet(n)
                b.Add(v); nv += 1
    print('apply: tracks', nw, 'vias', nv, flush=True)
    fill(b)
    rs = clean(b)
    fill(b)
    st = stitch(b)
    fill(b)
    rs += clean(b)
    fill(b)
    base = json.load(open(os.path.join(work, 'baseline.json')))
    now = islands(b)
    split = {k: (base[k], now.get(k)) for k in base
             if k.split('|')[0].split('-')[0] in ('VS', 'VBAT_IN', 'VBAT_FL', 'OUT1', 'OUT2', 'OUT3', 'OUT4')
             and (now.get(k, [0])[0] > base[k][0] or now.get(k, [0, 0])[1] < base[k][1] * (1 - fixed_routes.POUR_LOSS_MAX))}
    pcbnew.SaveBoard(out + '.kicad_pcb', b)
    json.dump({'split': split, 'stitch': st, 'removed': rs, 'tracks': nw, 'vias': nv}, open(out + '.json', 'w'), indent=1)
    print('pours:', 'whole' if not split else 'SPLIT %s' % split, '| stitch vias', st, '| cleaned', rs, flush=True)


def clean(b):
    """remove unlocked dangling vias and track stubs (free ends), repeated until stable"""
    removed = 0
    for _ in range(10):
        b.BuildConnectivity()
        conn = b.GetConnectivity()
        gone = []
        for t in b.GetTracks():
            if t.IsLocked():
                continue
            if t.GetClass() == 'PCB_VIA':
                if conn.GetConnectedItems(t).__len__() == 0 or b_via_one_layer(b, t):
                    gone.append(t)
            else:
                for end in (t.GetStart(), t.GetEnd()):
                    if not touches(b, t, end):
                        gone.append(t); break
        if not gone:
            break
        for t in gone:
            b.Remove(t)
        removed += len(gone)
    return removed


def _items_at(b, t, p, lay):
    n = t.GetNetCode()
    for o in b.GetTracks():
        if o is t or o.GetNetCode() != n:
            continue
        if o.GetClass() == 'PCB_VIA':
            if (o.GetPosition() - p).EuclideanNorm() <= o.GetWidth(pcbnew.F_Cu) // 2 and (lay is None or o.IsOnLayer(lay)):
                return True
        elif lay is None or o.GetLayer() == lay:
            if o.GetStart() == p or o.GetEnd() == p or o.HitTest(p, 0):
                return True
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() == n and (lay is None or pad.IsOnLayer(lay)) and pad.HitTest(p):
                return True
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != n:
            continue
        for zl in z.GetLayerSet().Seq():
            if (lay is None or zl == lay) and zl in ALL_CU and z.GetFilledPolysList(zl).Contains(p):
                return True
    return False


def touches(b, t, p):
    return _items_at(b, t, p, t.GetLayer())


def b_via_one_layer(b, v):
    hit = 0
    for lay in ALL_CU:
        if _items_at(b, v, v.GetPosition(), lay):
            hit += 1
    return hit < 2


def stitch(b):
    """GND stitching vias on a 5 mm grid where all four layers are GND fill with 0.5 mm margin"""
    pitch = M(fixed_routes.STITCH_PITCH_MM)
    ox, oy = origin(b)
    box = b.GetBoardEdgesBoundingBox()
    added = 0
    for netname in ('GND', 'GND_CAN'):
        net = b.FindNet(netname)
        fills = {}
        for z in b.Zones():
            if z.GetIsRuleArea() or z.GetNetname() != netname:
                continue
            for l in z.GetLayerSet().Seq():
                if l in ALL_CU:
                    s = fills.setdefault(l, pcbnew.SHAPE_POLY_SET())
                    s.Append(z.GetFilledPolysList(l))
        if len(fills) < 4:
            continue
        for l, s in fills.items():
            s.Simplify(); s.Deflate(M(0.75), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, M(0.01))
        vias = [t.GetPosition() for t in b.GetTracks() if t.GetClass() == 'PCB_VIA']
        added += tie_islands(b, net, fills, vias)
        y = box.GetY() + pitch // 2
        while y < box.GetBottom():
            x = box.GetX() + pitch // 2
            while x < box.GetRight():
                p = pcbnew.VECTOR2I(x, y)
                if all(s.Contains(p) for s in fills.values()) and all((p - q).EuclideanNorm() > pitch * 0.6 for q in vias):
                    v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                    v.SetWidth(M(0.6)); v.SetDrill(M(0.3)); v.SetNet(net); b.Add(v); vias.append(p); added += 1
                x += pitch
            y += pitch
    return added


def isl_ok(isl, p):
    d = pcbnew.SHAPE_POLY_SET(isl); d.Deflate(M(0.75), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, M(0.01))
    return d.Contains(p)


def layer_free(b, p, lay, clr=None):
    """no pad, track or via of any net within clr of p on this layer and no rule area (a foreign pour is refilled
    around the via; the pour check catches a split)"""
    clr = clr or M(0.65)
    for t in b.GetTracks():
        if t.IsOnLayer(lay) and t.GetEffectiveShape(lay).Collide(p, clr):
            return False
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.IsOnLayer(lay) and pad.GetEffectiveShape(lay).Collide(p, clr):
                return False
            if pad.HasHole() and (pad.GetPosition() - p).EuclideanNorm() < clr + max(pad.GetSize(lay).x, pad.GetSize(lay).y):
                return False
    for z in b.Zones():
        if z.GetIsRuleArea() and z.IsOnLayer(lay) and z.Outline().Collide(p, clr):
            return False
    return True


def tie_islands(b, net, fills, vias):
    """one via into every F/B fill island of this net that has no via or THT pad yet (0.5 mm search grid)"""
    tht = [p.GetPosition() for fp in b.GetFootprints() for p in fp.Pads()
           if p.GetNetCode() == net.GetNetCode() and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
    added = 0
    step = M(0.25)
    f03 = {}   # fills deflated by the via radius (+0.01): a via there lies inside same-net copper
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != net.GetNetCode():
            continue
        for l in z.GetLayerSet().Seq():
            if l in ALL_CU:
                f03.setdefault(l, pcbnew.SHAPE_POLY_SET()).Append(z.GetFilledPolysList(l))
    for l, f in f03.items():
        f.Simplify(); f.Deflate(M(0.31), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, M(0.01))
    fills = f03
    if pcbnew.In1_Cu not in fills:
        return 0
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != net.GetNetCode():
            continue
        for lay in (pcbnew.F_Cu, pcbnew.B_Cu):
            if not z.IsOnLayer(lay):
                continue
            ps = z.GetFilledPolysList(lay)
            for i in range(ps.OutlineCount()):
                isl = pcbnew.SHAPE_POLY_SET(); isl.AddOutline(ps.COutline(i))
                for h in range(ps.HoleCount(i)):
                    isl.AddHole(ps.CHole(i, h))
                if any(isl.Contains(q) for q in vias + tht):
                    continue
                bb = isl.BBox(); done = False
                y = bb.GetY()
                while y < bb.GetBottom() and not done:
                    x = bb.GetX()
                    while x < bb.GetRight():
                        p = pcbnew.VECTOR2I(x, y)
                        if (fills[lay].Contains(p) and isl.Contains(p) and fills[pcbnew.In1_Cu].Contains(p)
                                and all((l in fills and fills[l].Contains(p)) or layer_free(b, p, l, M(0.55))
                                        for l in ALL_CU if l not in (lay, pcbnew.In1_Cu))
                                and all((p - q).EuclideanNorm() > M(0.8) for q in vias)):
                            v = pcbnew.PCB_VIA(b); v.SetPosition(p); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
                            v.SetWidth(M(0.6)); v.SetDrill(M(0.3)); v.SetNet(net); b.Add(v); vias.append(p)
                            added += 1; done = True; break
                        x += step
                    y += step
    return added


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'prep':
        prep(sys.argv[2], sys.argv[3])
    elif cmd == 'apply':
        apply(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == 'islands':
        b = pcbnew.LoadBoard(sys.argv[2]); fill(b); print(json.dumps(islands(b), indent=0))
