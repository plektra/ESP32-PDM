#!/usr/bin/env python3
"""Build a JLCPCB order package for one board: Gerber + drill zip, BOM and CPL for PCBA.

    python3 tools/jlc_package.py pdm-4ch [--force]

Writes hardware/<board>/fab/: <stem>-gerbers.zip, <stem>-bom-jlc.csv, <stem>-cpl-jlc.csv and package-report.md.
Upload the zip on jlcpcb.com (quote), then the BOM and CPL in the PCBA step.

Gate: kicad-cli DRC with schematic parity must show 0 errors, 0 unconnected items and 0 parity issues (--force
writes the package anyway and says so in the report).

BOM/CPL rules: a part is machine-placed only if it has an LCSC number, is not DNP and is not on the board's
hand-solder list (decision 85: the THT connectors). Everything left out is listed in the report with the reason.
CPL rotations are KiCad's; the parts in ROTATION_CHECK must be checked in JLCPCB's placement preview.
"""
import csv
import io
import json
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
            'U3': 'EasyEDA draws the package rotated 90 deg',
            'U11': 'EasyEDA draws the package rotated 90 deg',
            'U12': 'EasyEDA draws the package rotated 90 deg',
            'U13': 'EasyEDA draws the package rotated 90 deg',
            'U14': 'EasyEDA draws the package rotated 90 deg',
            'D7': 'C2286: JLCPCB pad 1 = anode, KiCad pad 1 = cathode (T-0160)',
            'D8': 'C2286: JLCPCB pad 1 = anode, KiCad pad 1 = cathode (T-0160)',
        }),
    'pdm-hc2': dict(stem='hardware/pdm-hc2/ESP32-PDM-HC2', hand_solder={'J4', 'J5', 'J10', 'J11'}, rotation_check={}),
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
    with cpl.open('w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for ref in placed:
            p = pos[ref]
            w.writerow([ref, f"{float(p['PosX']):.4f}mm", f"{float(p['PosY']):.4f}mm",
                        'Top' if p['Side'] == 'top' else 'Bottom', f"{float(p['Rot']):.1f}"])

    lcscs = sorted(k for k in groups if isinstance(k, str))
    report += ['', f'BOM `{bom.name}`: {len(groups)} lines, {len(placed)} placed parts, {len(lcscs)} unique LCSC parts.',
               f'CPL `{cpl.name}`: {len(placed)} rows, sides: ' +
               ('all top' if not bad_side else f'NOT TOP: {", ".join(bad_side)} (decision 122)'), '',
               '## Left out of BOM/CPL', '', '| Ref | Value | LCSC | Why |', '|---|---|---|---|']
    report += [f'| {r} | {v} | {l} | {why} |' for r, v, l, why in left_out]
    report += ['', '## Check in the JLCPCB placement preview', '']
    report += [f'- {r}: {why}' for r, why in cfg['rotation_check'].items() if r in placed]
    report += ['', '## Unique LCSC parts', '', ' '.join(lcscs), '']
    (out / 'package-report.md').write_text('\n'.join(report))
    print('\n'.join(report[:6]))
    print(f'wrote {out.relative_to(ROOT)}/: {zpath.name}, {bom.name}, {cpl.name}, package-report.md; '
          f'{len(placed)} placed, {len(left_out)} left out')


if __name__ == '__main__':
    main()
