"""Decision 215: base board + geometry for the one-pass router (pf_route.py / pf_core.c). KiCad python:
  pf_export.py <board> <out dir> [moves.json]
1 applies the part moves (ref -> [x, y, rot], mm from the outline corner),
2 removes the signal copper that is rerouted: every track/via of a 'sig' or 'v3' net narrower than 0.5 mm, except the
  KEEP nets (USB pair, CC1, CAN) and fixed_routes.KEEP_TRACKS; GND vias/tracks a moved part now collides with go too,
3 writes <out>/base.kicad_pcb (zones unfilled) and <out>/geo.json: every pad, kept track and via as polygons at the
  inflations the router needs, holes, power-pour outlines, rule areas, and the nets to route with their clusters.
Coordinates: mm from the board outline corner."""
import json, os, sys
import pcbnew
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import routing_build as rb, fixed_routes as fr

M, MM = pcbnew.FromMM, pcbnew.ToMM
LAY = {'F.Cu': pcbnew.F_Cu, 'In2.Cu': pcbnew.In2_Cu, 'B.Cu': pcbnew.B_Cu}
MARGIN = 0.04          # raster margin (half a 0.05 mm cell on the diagonal)
HALF = 0.1             # half of a 0.2 mm track
VIA_R = 0.3
ESCAPE = 0.6           # a pad's escape zone: class clearances drop to the board's 0.2 mm within this of the pad
KEEP = {'/USB_DP', '/USB_DN', 'Net-(J3-CC1)', '/CAN/CANH_BUS', '/CAN/CANL_BUS', '/CAN/CANH_XCVR', '/CAN/CANL_XCVR'}
CAN_SIDE = (75.7, 51.4)   # x, y: pads beyond both belong to the isolated CAN side (never routed here)


def polys(ps, ox, oy):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.COutline(i)
        out.append([(round(MM(o.CPoint(j).x - ox), 4), round(MM(o.CPoint(j).y - oy), 4)) for j in range(o.PointCount())])
    return out


def clr(net):
    return max(fr.CLASSES[rb.net_class(net)][1] / 1000, 0.2) if net else 0.2


# local power links at J3 routed here too: VBUS at 0.3 mm (a wider track cannot leave the 0.5 mm pitch pins)
WIDTH = {'Net-(F2-Pad1)': 0.3, 'Net-(D3-A)': 0.4}


def rip_net(net):
    return net and net not in KEEP and (rb.net_class(net) in ('sig', 'v3') or net in WIDTH)


def main():
    board, out = sys.argv[1], sys.argv[2]
    moves = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
    os.makedirs(out, exist_ok=True)
    b = pcbnew.LoadBoard(board)
    ox, oy = rb.origin(b)
    for ref, (x, y, rot) in moves.items():
        fp = b.FindFootprintByReference(ref)
        assert fp and not fp.IsFlipped(), ref
        fp.SetPosition(rb.P(b, x, y)); fp.SetOrientationDegrees(rot)
    rb.barrier_gnd(b)
    keep = set()
    for n, a, e in getattr(fr, 'KEEP_TRACKS', ()):
        pa, pe = rb.P(b, *a), rb.P(b, *e)
        keep.add((n, *sorted([(pa.x // 2000, pa.y // 2000), (pe.x // 2000, pe.y // 2000)])))
    # pads of moved parts: GND copper that now touches a foreign pad goes
    moved_pads = [p for ref in moves for p in b.FindFootprintByReference(ref).Pads()]
    gone = []
    for t in list(b.GetTracks()):
        net = t.GetNetname()
        if rip_net(net):
            if t.GetClass() != 'PCB_VIA':
                a, e = t.GetStart(), t.GetEnd()
                if (net, *sorted([(a.x // 2000, a.y // 2000), (e.x // 2000, e.y // 2000)])) in keep or MM(t.GetWidth()) >= 0.5:
                    continue
            gone.append(t)
        elif net in rb.GND_NETS and moved_pads:
            for p in moved_pads:
                if p.GetNetname() == net or not p.IsOnLayer(t.GetLayer()) and t.GetClass() != 'PCB_VIA':
                    continue
                bb = p.GetBoundingBox(); bb.Inflate(M(0.2) + t.GetWidth() // 2)
                pts = [t.GetPosition()] if t.GetClass() == 'PCB_VIA' else \
                    [pcbnew.VECTOR2I(t.GetStart().x + (t.GetEnd().x - t.GetStart().x) * i // 8,
                                     t.GetStart().y + (t.GetEnd().y - t.GetStart().y) * i // 8) for i in range(9)]
                if any(bb.Contains(q) for q in pts):
                    gone.append(t); break
    for t in gone:
        b.Remove(t)
    for z in b.Zones():
        z.UnFill()
    base = os.path.join(out, 'base.kicad_pcb')
    pcbnew.SaveBoard(base, b)
    b = pcbnew.LoadBoard(base)
    print('removed', len(gone), 'tracks/vias; moved', len(moves), 'parts', flush=True)

    b.BuildConnectivity()
    conn = b.GetConnectivity()
    items = [p for fp in b.GetFootprints() for p in fp.Pads()] + list(b.GetTracks())
    uid = lambda x: x.m_Uuid.AsString()
    cid, k = {}, 0
    for it in items:
        if it.GetNetCode() <= 0 or uid(it) in cid or not rip_net(it.GetNetname()):
            continue
        k += 1
        stack = [it]
        while stack:
            x = stack.pop()
            if uid(x) in cid:
                continue
            cid[uid(x)] = k
            for y in conn.GetConnectedItems(x):
                if y.GetNetCode() == it.GetNetCode() and uid(y) not in cid and y.GetClass() != 'ZONE':
                    stack.append(y)

    def shape(it, lay, inf):
        ps = pcbnew.SHAPE_POLY_SET()
        it.TransformShapeToPolygon(ps, lay, M(inf), M(0.01), pcbnew.ERROR_OUTSIDE)
        return polys(ps, ox, oy)

    geo = {'items': [], 'zones': [], 'margin': MARGIN,
           'size': [MM(b.GetBoardEdgesBoundingBox().GetWidth()), MM(b.GetBoardEdgesBoundingBox().GetHeight())]}
    for it in items:
        net = it.GetNetname()
        lays = [ln for ln, l in LAY.items() if it.IsOnLayer(l)]
        is_pad = it.GetClass() == 'PAD'
        c = clr(net)
        e = {'net': net, 'layers': lays, 'cl': cid.get(uid(it), 0), 'kind': 'pad' if is_pad else 'via' if it.GetClass() == 'PCB_VIA' else 'track',
             'ref': it.GetParentFootprint().GetReference() + '.' + it.GetNumber() if is_pad else '',
             'at': [round(MM(it.GetPosition().x - ox), 4), round(MM(it.GetPosition().y - oy), 4)]}
        if is_pad:
            e['smd'] = not it.HasHole()
        for key, inf in (('tf', c + HALF + MARGIN), ('tb', 0.2 + HALF + MARGIN), ('v', c + VIA_R + MARGIN), ('raw', 0),
                         ('esc', ESCAPE), ('vpad', VIA_R + MARGIN)):
            if key == 'esc' and not (is_pad and rip_net(net)):
                continue
            if key == 'vpad' and not (is_pad and not it.HasHole()):
                continue
            e[key] = {ln: shape(it, LAY[ln], inf) for ln in lays}
        if is_pad and it.HasHole():
            for key, inf in (('hole_t', 0.25 + HALF + MARGIN), ('hole_v', 0.25 + VIA_R + MARGIN)):
                ps = pcbnew.SHAPE_POLY_SET()
                it.TransformHoleToPolygon(ps, M(inf), M(0.01), pcbnew.ERROR_OUTSIDE)
                e[key] = polys(ps, ox, oy)
            if net in rb.GND_NETS and lays:   # In2 tracks stay 0.9 mm off GND THT pads (thermal relief on the plane)
                e['gndtht'] = shape(it, pcbnew.In2_Cu, 1.3)
        if lays or 'hole_t' in e:
            geo['items'].append(e)
    for z in b.Zones():
        name = z.GetZoneName()
        if z.GetIsRuleArea():
            if name.startswith(rb.SLIVER):
                continue
            lays = [ln for ln, l in LAY.items() if z.IsOnLayer(l)]
            geo['zones'].append({'name': name, 'net': '', 'layers': lays or list(LAY), 'poly': polys(z.Outline(), ox, oy), 'kind': 'rule'})
            continue
        net = z.GetNetname()
        if net in rb.GND_NETS:
            continue
        zc = MM(z.GetLocalClearance() or M(0.2))
        for ln, l in LAY.items():
            if not z.IsOnLayer(l):
                continue
            d = {'name': name, 'net': net, 'layers': [ln], 'poly': polys(z.Outline(), ox, oy), 'zc': zc,
                 'kind': 'corridor' if name in rb.CORRIDOR_POURS else 'pour'}
            geo['zones'].append(d)
            if name in rb.CORRIDOR_POURS:
                ps = pcbnew.SHAPE_POLY_SET()
                for r in rb.PROFETS:
                    vs = [p.GetPosition() for p in b.FindFootprintByReference(r).Pads()
                          if p.GetNumber() == fr.THERMAL_PAD and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
                    k_ = M(fr.THERMAL_KEEP_MM)
                    ps.Append(rb.rect_poly(min(v.x for v in vs) - k_, min(v.y for v in vs) - k_,
                                           max(v.x for v in vs) + k_, max(v.y for v in vs) + k_))
                geo['zones'].append({'name': name + '-thermal', 'net': net, 'layers': [ln], 'poly': polys(ps, ox, oy), 'kind': 'thermal'})
    for name, (x1, y1, x2, y2) in rb.KEEPOUTS.items():
        geo['zones'].append({'name': name, 'net': '', 'layers': list(LAY), 'poly': [[(x1, y1), (x2, y1), (x2, y2), (x1, y2)]], 'kind': 'rule'})
    geo['width'] = {n: WIDTH.get(n, fr.CLASSES[rb.net_class(n)][0] / 1000) for n in {e['net'] for e in geo['items']} if rip_net(n)}
    geo['clr'] = {n: clr(n) for n in geo['width']}
    json.dump(geo, open(os.path.join(out, 'geo.json'), 'w'))
    print('items', len(geo['items']), 'zones', len(geo['zones']), 'nets to route', len(geo['width']), 'clusters', k)


main()
