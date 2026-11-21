import json, math, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
out = {}
for fp in b.GetFootprints():
    ref = fp.GetReference()
    f = fp.GetField('LCSC') if hasattr(fp, 'GetField') else None
    try:
        lcsc = fp.GetFieldText('LCSC')
    except Exception:
        lcsc = f.GetText() if f else ''
    rot = fp.GetOrientationDegrees()
    o = fp.GetPosition()
    a = math.radians(rot)
    pads = []
    for p in fp.Pads():
        pos = p.GetPosition() - o
        x = pos.x * math.cos(a) - pos.y * math.sin(a)
        y = pos.x * math.sin(a) + pos.y * math.cos(a)
        s = p.GetSize()
        pads.append(dict(n=p.GetNumber(), x=round(pcbnew.ToMM(x), 3), y=round(pcbnew.ToMM(y), 3),
                         w=round(pcbnew.ToMM(s.x), 3), h=round(pcbnew.ToMM(s.y), 3),
                         rot=round((p.GetOrientationDegrees() - rot) % 180, 1),
                         drill=round(pcbnew.ToMM(p.GetDrillSize().x), 3), net=p.GetNetname()))
    out[ref] = dict(fp=str(fp.GetFPID().GetUniStringLibItemName()), lcsc=lcsc, rot=rot,
                    value=fp.GetValue(), pads=pads)
json.dump(out, open(sys.argv[2], 'w'), indent=1)
