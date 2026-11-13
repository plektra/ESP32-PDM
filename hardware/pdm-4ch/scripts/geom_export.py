"""T-0241 generator for the channel bus; needs T-0241-next-build.patch applied (net_class, CORRIDOR_POURS,
PROFETS, THERMAL_PAD in routing_build.py / fixed_routes.py).
geom_export.py <board> <out.json> <scripts dir>: copper geometry for maze_route.py (KiCad python).
Items: net, layers, cluster, polygon at track inflation (clearance + 0.1 half width + margin) and via inflation
(clearance + 0.3 via radius + margin), plus raw copper polygon (for start/goal cells). Coordinates mm board-relative."""
import json, sys
import pcbnew
sys.path.insert(0, sys.argv[3])
import routing_build as rb, fixed_routes as fr

b = pcbnew.LoadBoard(sys.argv[1])
rb.fill(b)
ox, oy = rb.origin(b)
M, MM = pcbnew.FromMM, pcbnew.ToMM
LAY = {'F.Cu': pcbnew.F_Cu, 'In2.Cu': pcbnew.In2_Cu, 'B.Cu': pcbnew.B_Cu}
MARGIN = 0.06


def polys(ps):
    out = []
    for i in range(ps.OutlineCount()):
        o = ps.COutline(i)
        out.append([(round(MM(o.CPoint(j).x - ox), 3), round(MM(o.CPoint(j).y - oy), 3)) for j in range(o.PointCount())])
    return out


def clr(net):
    return fr.CLASSES[rb.net_class(net)][1] / 1000


# clusters per net (connectivity)
b.BuildConnectivity()
conn = b.GetConnectivity()
items = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        items.append(p)
items += list(b.GetTracks())
cid = {}
for it in items:
    n = it.GetNetCode()
    if n <= 0 or id(it) in cid or it.GetNetname() in rb.GND_NETS or it.GetNetname() in rb.POWER_NETS:
        continue
    k = len(cid) + 1
    stack = [it]
    while stack:
        x = stack.pop()
        if id(x) in cid:
            continue
        cid[id(x)] = k
        for y in conn.GetConnectedItems(x):
            if y.GetNetCode() == n and id(y) not in cid and y.GetClass() != 'ZONE':
                stack.append(y)

out = {'items': [], 'zones': [], 'size': [MM(b.GetBoardEdgesBoundingBox().GetWidth()), MM(b.GetBoardEdgesBoundingBox().GetHeight())]}
for it in items:
    net = it.GetNetname()
    lays = [ln for ln, l in LAY.items() if it.IsOnLayer(l)]
    if not lays:
        continue
    c = clr(net) if net else 0.2
    e = {'net': net, 'layers': lays, 'cl': cid.get(id(it), 0), 'via': it.GetClass() == 'PCB_VIA',
         'ref': it.GetParentFootprint().GetReference() + '.' + it.GetNumber() if it.GetClass() == 'PAD' else ''}
    for key, inf in (('t', c + 0.1 + MARGIN), ('v', c + 0.3 + MARGIN), ('raw', 0)):
        d = {}
        for ln in lays:
            ps = pcbnew.SHAPE_POLY_SET()
            it.TransformShapeToPolygon(ps, LAY[ln], M(inf), M(0.02), pcbnew.ERROR_OUTSIDE)
            d[ln] = polys(ps)
        e[key] = d
    if it.GetClass() == 'PAD' and it.HasHole():   # drilled hole blocks every layer
        ps = pcbnew.SHAPE_POLY_SET()
        it.TransformShapeToPolygon(ps, pcbnew.F_Cu, M(0.25 + 0.3), M(0.02), pcbnew.ERROR_OUTSIDE)
        e['hole'] = polys(ps)
        if net in rb.GND_NETS:      # keep In2 tracks off GND THT pads (starved thermal relief on the In2 plane)
            ps = pcbnew.SHAPE_POLY_SET()
            it.TransformShapeToPolygon(ps, pcbnew.In2_Cu, M(0.9), M(0.02), pcbnew.ERROR_OUTSIDE)
            e['gndtht'] = polys(ps)
    out['items'].append(e)
# zones: power-pour outlines (track keep-out for foreign nets; VS-In2 = corridor, only thermal fields),
# rule areas, router keep-outs
for z in b.Zones():
    if z.GetIsRuleArea():
        lays = [ln for ln, l in LAY.items() if z.IsOnLayer(l)]
        out['zones'].append({'net': '', 'layers': lays or list(LAY), 'poly': polys(z.Outline()), 'kind': 'rule'})
        continue
    net = z.GetNetname()
    if net in rb.GND_NETS:
        continue
    for ln, l in LAY.items():
        if not z.IsOnLayer(l):
            continue
        if z.GetZoneName() in rb.CORRIDOR_POURS:
            ps = pcbnew.SHAPE_POLY_SET()
            for r in rb.PROFETS:
                vs = [p.GetPosition() for p in b.FindFootprintByReference(r).Pads()
                      if p.GetNumber() == fr.THERMAL_PAD and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH]
                k_ = M(fr.THERMAL_KEEP_MM)
                ps.Append(rb.rect_poly(min(v.x for v in vs) - k_, min(v.y for v in vs) - k_, max(v.x for v in vs) + k_, max(v.y for v in vs) + k_))
            out['zones'].append({'net': net, 'layers': [ln], 'poly': polys(ps), 'kind': 'thermal'})
            out['zones'].append({'net': net, 'layers': [ln], 'poly': polys(z.Outline()), 'kind': 'corridor',
                                 'zc': MM(z.GetLocalClearance() or M(0.2))})
        else:
            out['zones'].append({'net': net, 'layers': [ln], 'poly': polys(z.Outline()), 'kind': 'pour',
                                 'zc': MM(z.GetLocalClearance() or M(0.2))})
# T-0251: net-class track width per net (mm); maze_route.py emits it and sizes its keep-outs with it
out['width'] = {e['net']: fr.CLASSES[rb.net_class(e['net'])][0] / 1000 for e in out['items'] if e['net']}
for name, r in rb.KEEPOUTS.items():
    x1, y1, x2, y2 = r
    out['zones'].append({'net': '', 'layers': list(LAY), 'poly': [[(x1, y1), (x2, y1), (x2, y2), (x1, y2)]], 'kind': name})
json.dump(out, open(sys.argv[2], 'w'))
print('items', len(out['items']), 'zones', len(out['zones']))
