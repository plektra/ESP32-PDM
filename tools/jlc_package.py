#!/usr/bin/env python3
"""Build a JLCPCB order package for one board: Gerber + drill zip, BOM and CPL for PCBA.

    python3 tools/jlc_package.py pdm-4ch [--force]

Writes hardware/<board>/fab/: <stem>-gerbers.zip, <stem>-bom-jlc.csv, <stem>-cpl-jlc.csv and package-report.md.
Upload the zip on jlcpcb.com (quote), then the BOM and CPL in the PCBA step.

Gate: kicad-cli DRC with schematic parity must show 0 errors, 0 unconnected items and 0 parity issues (--force
writes the package anyway and says so in the report).

BOM/CPL rules: a part is machine-placed only if it has an LCSC number, is not DNP and is not on the board's
hand-solder list (decision 85: the THT connectors). Everything left out is listed in the report with the reason.
CPL rotation and position: KiCad's, corrected per LCSC part by CPL_FIX where JLCPCB's EasyEDA footprint is drawn
rotated or has its origin elsewhere (found by tools/fp_check/, docs/reviews/2026-11-21-footprints-pdm-4ch.md). A fix
applies only when the KiCad footprint is the one it was measured on; otherwise the report flags the part. Confirm the
corrected parts and those in rotation_check in JLCPCB's placement preview.
"""
import csv
import io
import json
import math
import re
import subprocess
import sys
import tempfile
import zipfile
from collections import OrderedDict
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
KICAD_CLI = Path(os.environ.get('KICAD_APP', '/Applications/KiCad/KiCad.app')) / 'Contents/MacOS/kicad-cli'

BOARDS = {
    'pdm-4ch': dict(
        stem='hardware/pdm-4ch/ESP32-PDM-4CH',
        hand_solder={'J4', 'J5', 'J10', 'J11'},           # decision 85
        rotation_check={                                  # STATUS.md open items
            'D7': 'C2286: EasyEDA pad 1 = anode, KiCad pad 1 = cathode; no fix needed, anode on Net-(D7-A) at 0 deg',
            'D8': 'C2286: EasyEDA pad 1 = anode, KiCad pad 1 = cathode; no fix needed, anode on Net-(D8-A) at 0 deg',
        }),
    'pdm-hc2': dict(stem='hardware/pdm-hc2/ESP32-PDM-HC2', hand_solder={'J4', 'J5', 'J10', 'J11'}, rotation_check={}),
}
# LCSC: (KiCad footprint it was measured on, rotation to add in deg, tx, ty). (tx, ty) = where the EasyEDA footprint
# origin sits in the KiCad footprint frame (mm, y down); it turns with the part. JLCPCB rotation = KiCad + correction.
CPL_FIX = {
    'C5219203': ('TI_DDF0008A', 180, 0, 0),                          # LM74502H-Q1
    'C528763': ('SOIC-8_7.5x5.85mm_P1.27mm', 270, 0, 0),             # CA-IS3050G
    'C22427220': ('SOT-23-6', 270, 0, 0),                            # LMR51610
    'C534868': ('Infineon_PG-TDSO-14_ThermalVias', 270, 0, 0),       # BTT6050-1ERA
    'C2145': ('SOT-23-3', 180, 0, 0),                                # MMBT5551
    'C22466350': ('SOT-23', 180, 0, 0),                              # BAT54C
    'C7420333': ('SOT-23', 180, 0, 0),                               # BAT54S
    'C2687131': ('SOT-23', 180, 0, 0),                               # PESD2CAN
    'C5464765': ('Infineon_PG-HSOF-8-1', 270, -1.60, -1.80),         # AGM601LL, aligned on the lead pads
    'C58069': ('TO-252-2', 0, -1.56, 0),                             # L78M05
    'C2913206': ('ESP32-S2-MINI-1', 0, 0, 2.55),                     # ESP32-S3-MINI-1 module
    'C165948': ('USB_C_Receptacle_HRO_TYPE-C-31-M-12', 0, 0, -1.57),
}
GERBER_LAYERS = 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'


def cli(*args):
    r = subprocess.run([str(KICAD_CLI), *map(str, args)], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f'jlc_package: kicad-cli {args[:3]} failed:\n{r.stderr[-800:]}')
    return r


def drc(pcb, tmp):
    out = tmp / 'drc.json'
    subprocess.run([str(KICAD_CLI), 'pcb', 'drc', '--format', 'json', '--schematic-parity', '--severity-all',
                    '-o', str(out), str(pcb)], capture_output=True, text=True)
    if not out.exists():
        sys.exit('jlc_package: DRC did not run')
    rep = json.loads(out.read_text())
    v = rep.get('violations', [])
    parity = [x for x in rep.get('schematic_parity', [])
              if not (x.get('type') == 'missing_footprint' and not x.get('items'))]
    return dict(errors=sum(x.get('severity') == 'error' for x in v),
                warnings=sum(x.get('severity') == 'warning' for x in v),
                unconnected=len(rep.get('unconnected_items', [])), parity=len(parity))


def natural(ref):
    m = re.match(r'([A-Za-z]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    force = '--force' in sys.argv
    if len(args) != 1 or args[0] not in BOARDS:
        sys.exit(f'usage: jlc_package.py {{{"|".join(BOARDS)}}} [--force]')
    board = args[0]
    cfg = BOARDS[board]
    stem = ROOT / cfg['stem']
    pcb, sch = stem.with_suffix('.kicad_pcb'), stem.with_suffix('.kicad_sch')
    name = stem.name
    out = stem.parent / 'fab'
    out.mkdir(exist_ok=True)
    report = [f'# JLCPCB package: {board}', '']

    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        # ---- gate
        d = drc(pcb, tmp)
        ok = d['errors'] == 0 and d['unconnected'] == 0 and d['parity'] == 0
        report.append(f"DRC gate: {d['errors']} errors, {d['warnings']} warnings, {d['unconnected']} unconnected, "
                      f"{d['parity']} parity issues - {'pass' if ok else 'FAIL'}")
        if not ok and not force:
            sys.exit('jlc_package: DRC gate failed: ' + report[-1] + ' (use --force to build anyway)')

        # ---- Gerbers + drill
        g = tmp / 'gerbers'
        g.mkdir()
        cli('pcb', 'export', 'gerbers', '-o', g, '--layers', GERBER_LAYERS, '--subtract-soldermask', pcb)
        cli('pcb', 'export', 'drill', '-o', g, '--format', 'excellon', '--excellon-units', 'mm',
            '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', pcb)
        files = sorted(p for p in g.iterdir() if p.is_file())
        zpath = out / f'{name}-gerbers.zip'
        with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in files:
                zi = zipfile.ZipInfo(p.name, date_time=(2020, 1, 1, 0, 0, 0))  # stable zip bytes
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, re.sub(r'(?m)^(G04 #@! TF\.CreationDate|; #@! TF\.CreationDate|%TF\.CreationDate).*\n',
                                      '', p.read_text(errors='replace')))
        report += ['', f'Gerber zip `{zpath.name}`: ' + ', '.join(p.name for p in files)]

        # ---- BOM from the schematic
        cli('sch', 'export', 'bom', sch, '-o', tmp / 'bom.csv', '--fields',
            'Reference,Value,Footprint,LCSC,${DNP},${EXCLUDE_FROM_BOM},${EXCLUDE_FROM_BOARD}',
            '--labels', 'Ref,Value,Footprint,LCSC,DNP,ExBOM,ExBoard', '--group-by', '', '--ref-range-delimiter', '')
        sym = {r['Ref']: r for r in csv.DictReader(io.StringIO((tmp / 'bom.csv').read_text()))}

        # ---- positions from the board
        cli('pcb', 'export', 'pos', pcb, '-o', tmp / 'pos.csv', '--format', 'csv', '--units', 'mm', '--side', 'both')
        pos = {r['Ref']: r for r in csv.DictReader(io.StringIO((tmp / 'pos.csv').read_text()))}

    placed, left_out = [], []
    for ref in sorted(set(sym) | set(pos), key=natural):
        s, p = sym.get(ref), pos.get(ref)
        why = None
        if s is None:
            why = 'footprint only (no symbol)'
        elif s['DNP']:
            why = 'DNP'
        elif s['ExBOM'] or s['ExBoard']:
            why = 'excluded from BOM/board'
        elif ref in cfg['hand_solder']:
            why = 'hand-soldered THT connector (decision 85)'
        elif not s['LCSC'].strip():
            why = 'no LCSC number'
        elif p is None:
            why = 'NOT ON THE BOARD - check'
        if why:
            left_out.append((ref, (s or p)['Value' if s else 'Val'], s['LCSC'] if s else '', why))
        else:
            placed.append(ref)
    bad_side = [r for r in placed if pos[r]['Side'] != 'top']

    groups = OrderedDict()
    for ref in placed:
        s = sym[ref]
        fp = s['Footprint'].split(':')[-1]
        # One BOM line per LCSC part: JLCPCB warns "multiple lines matched to the same part" when the
        # same part appears under different value spellings (0.1uF/100nF, 1uF/1uF/50V).
        key = s['LCSC'].strip() or (s['Value'], fp)
        groups.setdefault(key, {'val': s['Value'], 'fp': fp, 'refs': []})['refs'].append(ref)
    bom = out / f'{name}-bom-jlc.csv'
    with bom.open('w', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(['Comment', 'Designator', 'Footprint', 'JLCPCB Part #'])
        for key, g in sorted(groups.items(), key=lambda kv: natural(kv[1]['refs'][0])):
            w.writerow([g['val'], ','.join(sorted(g['refs'], key=natural)), g['fp'], key if isinstance(key, str) else ''])
    cpl = out / f'{name}-cpl-jlc.csv'
    fixed, fix_wrong = [], []
    with cpl.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for ref in placed:
            p = pos[ref]
            x0, y0, rot = float(p['PosX']), float(p['PosY']), float(p['Rot'])
            x, y = x0, y0
            fix = CPL_FIX.get(sym[ref]['LCSC'].strip())
            fp = sym[ref]['Footprint'].split(':')[-1]
            if fix and fix[0] != fp:
                fix_wrong.append(f'{ref}: CPL_FIX measured on {fix[0]}, board has {fp}; not applied, re-run tools/fp_check')
            elif fix:
                _, d, tx, ty = fix
                a = math.radians(rot)                     # pos.csv: y up, rotation counter-clockwise
                x += tx * math.cos(a) + ty * math.sin(a)
                y += tx * math.sin(a) - ty * math.cos(a)
                fixed.append(f'{ref}: rotation {rot:.0f} -> {(rot + d) % 360:.0f} deg'
                             + (f', origin {x - x0:+.2f} / {y - y0:+.2f} mm' if tx or ty else ''))
                rot = (rot + d) % 360
            w.writerow([ref, f"{x:.4f}mm", f"{y:.4f}mm", 'Top' if p['Side'] == 'top' else 'Bottom', f"{rot:.1f}"])

    lcscs = sorted(k for k in groups if isinstance(k, str))
    report += ['', f'BOM `{bom.name}`: {len(groups)} lines, {len(placed)} placed parts, {len(lcscs)} unique LCSC parts.',
               f'CPL `{cpl.name}`: {len(placed)} rows, sides: ' +
               ('all top' if not bad_side else f'NOT TOP: {", ".join(bad_side)} (decision 122)'), '',
               '## Left out of BOM/CPL', '', '| Ref | Value | LCSC | Why |', '|---|---|---|---|']
    report += [f'| {r} | {v} | {l} | {why} |' for r, v, l, why in left_out]
    report += ['', '## Check in the JLCPCB placement preview', '']
    report += [f'- {r}: {why}' for r, why in cfg['rotation_check'].items() if r in placed]
    report += [f'- **{m}**' for m in fix_wrong]
    report += ['', '## CPL corrected against the JLCPCB footprints (CPL_FIX; the preview should show these)', '']
    report += [f'- {m}' for m in fixed]
    report += ['', '## Unique LCSC parts', '', ' '.join(lcscs), '']
    (out / 'package-report.md').write_text('\n'.join(report))
    print('\n'.join(report[:6]))
    print(f'wrote {out.relative_to(ROOT)}/: {zpath.name}, {bom.name}, {cpl.name}, package-report.md; '
          f'{len(placed)} placed, {len(left_out)} left out')


if __name__ == '__main__':
    main()
