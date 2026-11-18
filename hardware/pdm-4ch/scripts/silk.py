"""Silkscreen of pdm-4ch (layout stage 6, decision 224). KiCad python, run with KiCad closed:
  silk.py [board.kicad_pcb]          (default: the project board; rewrites it in place)
Re-run after any part move or reroute (the build keeps the texts, but a moved part may now cover a label).
Same result on every run: every board text on F/B.Silkscreen is removed and drawn again, every kept reference is
placed again.
1 Reference designators: shown only for KEEP (parts looked for at bring-up and service: connectors, ICs, switches,
  fuses and the parts R54-R56 inspected after the T-0118 short test, cut/fit options, DNP fit positions, LEDs,
  buttons); every other one is hidden (it stays on F.Fab for the assembly drawing, fab/ESP32-PDM-4CH-assembly.pdf).
2 Each kept reference and each top label goes to the nearest free spot: not over a pad (+0.15 mm), another part's
  body (its F.Fab outline), a footprint's silk lines (+0.05 mm), another text or within 0.6 mm of the board edge. 1.0 mm text,
  0.8 mm if nothing fits; a label that fits nowhere stops the script.
3 Top labels: OUT1-OUT4 on the J11 pins, BATTERY / + / - at J10, PANEL at J5, CAN at J4.
4 Bottom (no parts there): pin legends of J5, J4, J11, J10 and the J6 service pads, board name and licence."""
import math, os, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import routing_build as rb

BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), 'ESP32-PDM-4CH.kicad_pcb')
M, MM = pcbnew.FromMM, pcbnew.ToMM
KEEP = ['J3', 'J4', 'J5', 'J6', 'J10', 'J11', 'U1', 'U3', 'U5', 'U30', 'Q30', 'U11', 'U12', 'U13', 'U14',
        'F1', 'F2', 'F3', 'F4', 'R54', 'R55', 'R56', 'JP1', 'JP30', 'L2', 'FL1', 'D103', 'D203', 'D303', 'D403',
        'R44', 'C20', 'C22', 'R73', 'D7', 'D8', 'SW_BOOT1', 'SW_RESET1']
SIZES = (1.0, 0.8)
EDGE = 0.6
PAD_GAP = 0.15         # JLCPCB silk-to-pad minimum
SILK_GAP = 0.05        # to other silk lines (KiCad: must not touch)
BODY_SHRINK = 0.3
REV = 'rev A 2026-11'

# bottom pin legends: connector -> {pad number: text}; the text sits beside the pad on the board side
LEGEND = {
    'J5': {'1': 'SW1', '2': 'SW2', '3': 'SW3', '4': 'SW4', '5': 'SW SUPPLY', '6': 'LED1', '7': 'LED2',
           '8': 'LED3', '9': 'LED4', '10': 'GND'},
    'J4': {'1': 'NET-C GND', '2': 'NET-S', '3': 'CAN-H', '4': 'CAN-L'},
    'J11': {'1': 'OUT1', '2': 'OUT2', '3': 'OUT3', '4': 'OUT4'},
    'J10': {'1': 'BAT +', '2': 'BAT -'},
    'J6': {'1': 'GND', '2': 'TXD0', '3': 'RXD0', '4': 'IO35', '5': 'IO36', '6': 'IO37', '7': 'IO42', '8': '+3V3'},
}


def main():
    b = pcbnew.LoadBoard(BOARD)
    ox, oy = rb.origin(b)
    P = lambda x, y: rb.P(b, x, y)
    edges = b.GetBoardEdgesBoundingBox()
    W, H = MM(edges.GetWidth()), MM(edges.GetHeight())

    # ---- clean slate: board texts on the silk layers go, references hidden except KEEP
    old = [d for d in b.GetDrawings() if d.GetClass() == 'PCB_TEXT' and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS)]
    if old:   # reload after b.Remove(): KiCad's SWIG layer breaks on the next lookup otherwise (routing_build.prep)
        for d in old:
            b.Remove(d)
        pcbnew.SaveBoard(BOARD, b)
        b = pcbnew.LoadBoard(BOARD)
        ox, oy = rb.origin(b)
    fps = {fp.GetReference(): fp for fp in b.GetFootprints()}
    missing = [r for r in KEEP if r not in fps]
    assert not missing, missing
    for ref, fp in fps.items():
        fp.Reference().SetVisible(ref in KEEP)
        fp.Value().SetVisible(False)
        if not any(it.GetClass() == 'PCB_TEXT' and it.GetLayer() == pcbnew.F_Fab and 'REFERENCE' in it.GetText()
                   for it in fp.GraphicalItems()):
            t = pcbnew.PCB_TEXT(fp); t.SetText('${REFERENCE}'); t.SetLayer(pcbnew.F_Fab)
            t.SetTextSize(pcbnew.VECTOR2I(M(1.0), M(1.0))); t.SetTextThickness(M(0.15))
            t.SetPosition(fp.GetPosition()); fp.Add(t)

    # ---- obstacles (mm boxes) per side
    def box(bb, inf=0.0):
        return (MM(bb.GetLeft() - ox) - inf, MM(bb.GetTop() - oy) - inf, MM(bb.GetRight() - ox) + inf, MM(bb.GetBottom() - oy) + inf)

    def body_box(fp):
        """the part body: bbox of its F.Fab outline (the courtyard minus BODY_SHRINK if it has none)"""
        bb = None
        for it in fp.GraphicalItems():
            if it.GetLayer() == pcbnew.F_Fab and it.GetClass() != 'PCB_TEXT':
                if bb is None:
                    bb = it.GetBoundingBox()
                else:
                    bb.Merge(it.GetBoundingBox())
        if bb is not None:
            return box(bb)
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount():
            a, t, c, d = box(cy.BBox(), -BODY_SHRINK)
            if c > a and d > t:
                return (a, t, c, d)
        return None

    def silk_boxes(it, inf=SILK_GAP):
        """a silk line as boxes: one per straight edge (a rectangle or polygon outline blocks only its lines, not
        the area inside), the bounding box for arcs and circles"""
        w = MM(it.GetWidth()) / 2 + inf
        pts = []
        st = it.GetShape()
        if st == pcbnew.SHAPE_T_RECT:
            c = it.GetRectCorners() if hasattr(it, 'GetRectCorners') else None
            pts = [(MM(q.x - ox), MM(q.y - oy)) for q in c] if c else []
            pts.append(pts[0]) if pts else None
        elif st == pcbnew.SHAPE_T_POLY:
            ps = it.GetPolyShape()
            for k in range(ps.OutlineCount()):
                o = ps.COutline(k)
                q = [(MM(o.CPoint(j).x - ox), MM(o.CPoint(j).y - oy)) for j in range(o.PointCount())]
                for a, e in zip(q, q[1:] + q[:1]):
                    pts.append(None); pts += [a, e]
        elif st == pcbnew.SHAPE_T_SEGMENT:
            pts = [(MM(it.GetStart().x - ox), MM(it.GetStart().y - oy)), (MM(it.GetEnd().x - ox), MM(it.GetEnd().y - oy))]
        if not pts:
            return [box(it.GetBoundingBox(), inf)]
        out = []
        for a, e in zip(pts, pts[1:]):
            if a is None or e is None:
                continue
            out.append((min(a[0], e[0]) - w, min(a[1], e[1]) - w, max(a[0], e[0]) + w, max(a[1], e[1]) + w))
        return out

    obst = {'F': [], 'B': []}   # (box, owner ref)
    for ref, fp in fps.items():
        for p in fp.Pads():
            for side, lay in (('F', pcbnew.F_Cu), ('B', pcbnew.B_Cu)):
                if p.IsOnLayer(lay) or p.HasHole():
                    obst[side].append((box(p.GetBoundingBox(), PAD_GAP), ref))
        bd = body_box(fp)
        if bd and not fp.IsDNP():   # an unfitted part has no body: only its pads and silk lines block
            obst['F'].append((bd, ref + '#body'))
        for it in fp.GraphicalItems():
            side = {pcbnew.F_SilkS: 'F', pcbnew.B_SilkS: 'B'}.get(it.GetLayer())
            if side and it.GetClass() != 'PCB_TEXT':
                for bx in silk_boxes(it):
                    obst[side].append((bx, ref + '#silk'))
    # vias are tented (mask over them): silk may cross them

    def hits(bx, side, own):
        if bx[0] < EDGE or bx[1] < EDGE or bx[2] > W - EDGE or bx[3] > H - EDGE:
            return True
        for o, who in obst[side]:
            if bx[0] < o[2] and bx[2] > o[0] and bx[1] < o[3] and bx[3] > o[1]:
                return True
        return False

    def tbox(t):   # the ink (what is printed and what KiCad's silk checks use), + 0.1 mm
        bb = t.GetEffectiveTextShape().BBox()
        return (MM(bb.GetLeft() - ox) - 0.1, MM(bb.GetTop() - oy) - 0.1, MM(bb.GetRight() - ox) + 0.1, MM(bb.GetBottom() - oy) + 0.1)

    def style(t, size, side):
        t.SetTextSize(pcbnew.VECTOR2I(M(size), M(size))); t.SetTextThickness(M(0.15 if size >= 1.0 else 0.13))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
        t.SetMirrored(side == 'B')

    def place(t, side, own, cx, cy, around, angles=(0, 90), maxd=6.0, row=None, sizes=SIZES):
        """put text t at the nearest free spot to (cx, cy) outside box `around` (or anywhere if None); with
        row=(dy, dx_max): only along the row y = cy +- dy, moving right up to dx_max (labels that must stay level
        with their pin)"""
        steps = int(maxd / 0.25)
        if row:
            cand = sorted((abs(i) * 0.05 + 3 * abs(j) * 0.05, i * 0.2, j * 0.2) for i in range(0, int(row[1] / 0.05) + 1)
                          for j in range(-int(row[0] / 0.05), int(row[0] / 0.05) + 1))   # 0.05 mm steps (x 0.25 below)
        else:
            cand = sorted((math.hypot(i, j) * 0.25, i, j) for i in range(-steps, steps + 1) for j in range(-steps, steps + 1)
                          if math.hypot(i, j) * 0.25 <= maxd)
        maxd = max(maxd, row[1] if row else 0)
        for size in sizes:
            style(t, size, side)
            shapes = []   # per angle: text box relative to its position
            for ang in angles:
                t.SetTextAngleDegrees(ang); t.SetPosition(P(cx, cy))
                bx = tbox(t)
                shapes.append((ang, (bx[0] - cx, bx[1] - cy, bx[2] - cx, bx[3] - cy)))
            reach = maxd + max(max(abs(v) for v in s) for _, s in shapes)
            near = [(o, who) for o, who in obst[side]
                    if o[2] > cx - reach and o[0] < cx + reach and o[3] > cy - reach and o[1] < cy + reach]
            saved = obst[side]; obst[side] = near
            found = None
            for d, i, j in cand:
                x, y = cx + i * 0.25, cy + j * 0.25
                for ang, s in shapes:
                    bx = (x + s[0], y + s[1], x + s[2], y + s[3])
                    if around and bx[0] < around[2] and bx[2] > around[0] and bx[1] < around[3] and bx[3] > around[1]:
                        continue
                    if not hits(bx, side, own):
                        found = (x, y, ang, bx); break
                if found:
                    break
            obst[side] = saved
            if found:
                x, y, ang, bx = found
                t.SetTextAngleDegrees(ang); t.SetPosition(P(x, y))
                obst[side].append((tbox(t), own + '#text'))
                return size
        probe = [(0.0, dy) for dy in (0.0, -2.0, 2.0)] + [tuple(map(float, q.split(','))) for q in os.environ.get('SILK_PROBE', '').split()]
        for dx, dy in probe:   # what blocks the anchor (and SILK_PROBE="dx,dy ..." offsets): printed for the layout session
            bx = (cx + dx + shapes[0][1][0], cy + dy + shapes[0][1][1], cx + dx + shapes[0][1][2], cy + dy + shapes[0][1][3])
            print('  at %+.1f,%+.1f blocked by' % (dx, dy), sorted({w for o, w in obst[side]
                  if bx[0] < o[2] and bx[2] > o[0] and bx[1] < o[3] and bx[3] > o[1]}))
        raise SystemExit('no free spot for %s (%s) near %.1f, %.1f' % (own, t.GetText(), cx, cy))

    placed = []
    def label(text, side, x, y, around=None, angles=(0, 90), maxd=6.0, row=None, sizes=SIZES):
        t = pcbnew.PCB_TEXT(b); t.SetText(text); t.SetLayer(pcbnew.F_SilkS if side == 'F' else pcbnew.B_SilkS)
        b.Add(t)
        s = place(t, side, 'label:' + text, x, y, around, angles, maxd, row, sizes)
        placed.append(('"%s"' % text, s))
        return t

    pad = lambda ref, n: [p for p in fps[ref].Pads() if p.GetNumber() == n][0]
    at = lambda p: (MM(p.GetPosition().x - ox), MM(p.GetPosition().y - oy))
    body = lambda ref: box(fps[ref].GetCourtyard(pcbnew.F_CrtYd).BBox())

    # ---- 3 top labels
    # OUT1-OUT4: one column, vertical, centred on each J11 pin; on the OUT1/OUT3 rows it falls between the pads of
    # the DNP TVS footprints D103/D303 (hidden under the diode only if one is ever fitted)
    j11 = body('J11')
    col = (at(pad('D103', '1'))[0] + at(pad('D103', '2'))[0]) / 2
    for n in '1234':
        x, y = at(pad('J11', n))
        label('OUT' + n, 'F', col - 0.2, y, angles=(90,), row=(0.2, 0.6), sizes=(0.8,))   # board minimum; full 1 mm legend on the bottom
    j10 = body('J10')
    label('BATTERY', 'F', (j10[0] + j10[2]) / 2, j10[1] - 1.2, around=j10, angles=(0,))
    label('+', 'F', j10[2] + 1.0, at(pad('J10', '1'))[1], around=j10, angles=(0,), maxd=3.0, sizes=(1.5, 1.0))
    label('-', 'F', j10[2] + 1.0, at(pad('J10', '2'))[1], around=j10, angles=(0,), maxd=3.0, sizes=(1.5, 1.0))
    j5, j4 = body('J5'), body('J4')
    # in the copper-free band between J5 and J4 (CAN barrier strip), each at the end of its own connector
    label('PANEL', 'F', j5[0] - 3.5, j5[3] - 0.5, around=j5, angles=(0,), maxd=4.0)
    label('CAN', 'F', j4[0] - 3.5, j4[1] + 0.8, around=j4, angles=(0,), maxd=4.0)

    # ---- 4 bottom legends: right/left of each pad toward the board inside, at the pad's height
    for ref, names in LEGEND.items():
        fp = fps[ref]
        cx = MM(fp.GetPosition().x - ox)
        for n, text in names.items():
            ps = [p for p in fp.Pads() if p.GetNumber() == n]
            x, y = at(ps[0])
            if ref in ('J5', 'J4'):
                x -= 3.5 + 0.35 * len(text)     # board side is west
            elif ref in ('J11',):
                x += 3.0 + 0.35 * len(text)     # east
            elif ref == 'J10':
                x = sum(at(p)[0] for p in ps) / len(ps); y += 3.0 if n == '2' else -3.0
            elif ref == 'J6':
                x += 2.0 + 0.35 * len(text)
            label(text, 'B', x, y, angles=(0,), maxd=2.0)
    label('ESP32-PDM pdm-4ch', 'B', 50.0, 66.0, angles=(0,), maxd=12.0)
    label(REV + '  CERN-OHL-S v2', 'B', 50.0, 69.0, angles=(0,), maxd=12.0)

    # ---- 1/2 references, smallest parts first (large parts search a wider radius)
    order = sorted(KEEP, key=lambda r: fps[r].GetCourtyard(pcbnew.F_CrtYd).Area() if fps[r].GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else 0)
    for ref in order:
        fp = fps[ref]; t = fp.Reference()
        t.SetLayer(pcbnew.F_SilkS); t.SetKeepUpright(True)
        own = body_box(fp)
        c = fp.GetPosition()
        reach = 8.0 if own is None else max(8.0, math.hypot(own[2] - own[0], own[3] - own[1]) / 2 + 5.0)
        s = place(t, 'F', ref, MM(c.x - ox), MM(c.y - oy), None if fp.IsDNP() else own, maxd=reach)
        placed.append((ref, s))

    pcbnew.SaveBoard(BOARD, b)
    small = ['%s %.1f' % (r, s) for r, s in placed if s < 1.0]
    print('silk: %d texts placed, %d below 1.0 mm: %s' % (len(placed), len(small), ', '.join(small)))


main()
