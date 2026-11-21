"""Corrected CPL rows: JLCPCB rotation = KiCad rotation + correction; position = KiCad origin + rotated origin offset.
Offsets (tx, ty) are where the EasyEDA footprint origin sits in the KiCad footprint frame (mm, y down)."""
import csv, math, sys

FIX = {  # LCSC: (rotation correction deg, tx, ty, note)
    'C5219203': (180, 0, 0, 'U30 LM74502H DDF'),
    'C528763': (270, 0, 0, 'U5 SOIC-8 WB'),
    'C22427220': (270, 0, 0, 'U3 SOT-23-6'),
    'C534868': (270, 0, 0, 'U11-U14 TDSO-14'),
    'C2145': (180, 0, 0, 'Q3-Q6 SOT-23'),
    'C22466350': (180, 0, 0, 'D12-D15 SOT-23'),
    'C2687131': (180, 0, 0, 'D9 SOT-23'),
    'C7420333': (180, 0, 0, 'D102-D402 SOT-23'),
    'C5464765': (270, -1.60, -1.80, 'Q30 TOLL'),
    'C58069': (0, -1.56, 0, 'U6 TO-252'),
    'C2913206': (0, 0, 2.55, 'U1 module'),
    'C165948': (0, 0, -1.57, 'J3 USB-C'),
}
lcsc_of = dict(a.split('=') for a in sys.argv[2:])
rows = list(csv.DictReader(open(sys.argv[1])))
print('| Ref | LCSC | KiCad rot | JLCPCB rot | Mid X | Mid Y | corrected Mid X | corrected Mid Y |')
print('|---|---|---|---|---|---|---|---|')
for r in rows:
    code = lcsc_of.get(r['Designator'])
    if code not in FIX:
        continue
    d, tx, ty, _ = FIX[code]
    rot = float(r['Rotation'])
    a = math.radians(rot)
    bx = tx * math.cos(a) + ty * math.sin(a)          # board frame, y down
    by = -tx * math.sin(a) + ty * math.cos(a)
    x = float(r['Mid X'].rstrip('mm')); y = float(r['Mid Y'].rstrip('mm'))
    print(f"| {r['Designator']} | {code} | {rot:.0f} | {(rot + d) % 360:.0f} | {x:.2f} | {y:.2f} | "
          f"{x + bx:.2f} | {y - by:.2f} |")
