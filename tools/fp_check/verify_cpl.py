"""Place EasyEDA pads by the CPL (JLCPCB: Mid X/Y, y up, rotation CCW) and measure the distance to the board's
real pads (absolute, from pcbnew) of the same number. Run under KiCad's python."""
import csv, json, math, sys
import pcbnew

board = pcbnew.LoadBoard(sys.argv[1])
cpl = {r['Designator']: r for r in csv.DictReader(open(sys.argv[2]))}
easy = json.load(open(sys.argv[3]))
swap = {'C2286': {'1': '2', '2': '1'}}          # LED: EasyEDA pad 1 = anode = KiCad pad 2
worst_all = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    try:
        code = fp.GetFieldText('LCSC')
    except Exception:
        code = ''
    if ref not in cpl or code not in easy or not easy[code].get('footprint'):
        continue
    r = cpl[ref]
    mx, my = float(r['Mid X'][:-2]), float(r['Mid Y'][:-2])
    a = math.radians(float(r['Rotation']))
    kp = {}
    for p in fp.Pads():
        q = p.GetPosition()
        kp.setdefault(p.GetNumber(), []).append((pcbnew.ToMM(q.x), -pcbnew.ToMM(q.y)))
    errs = []
    for e in easy[code]['footprint']['pads']:
        n = swap.get(code, {}).get(str(e['number']), str(e['number']))
        if n not in kp:
            continue
        ex, ey = e['x'], -e['y']
        X = mx + ex * math.cos(a) - ey * math.sin(a)
        Y = my + ex * math.sin(a) + ey * math.cos(a)
        errs.append(min(math.hypot(X - x, Y - y) for x, y in kp[n]))
    if errs:
        worst_all.append((max(errs), ref, code, len(errs)))
worst_all.sort(reverse=True)
for w, ref, code, n in worst_all[:25]:
    print(f'{ref:10} {code:10} pads {n:3} worst {w:.3f} mm')
print(f'{len(worst_all)} parts checked; over 0.5 mm: {[r for w, r, c, n in worst_all if w > 0.5]}')
