#!/usr/bin/env python3
"""Answer questions about a board's schematic in one call (via kicad-cli; the whole hierarchy).

  python3 tools/sch_query.py pdm-4ch parts [--sheet analog] [--match C1]      parts: ref, value, footprint, LCSC
                                                       (--sheet matches the sheet name, e.g. "Analog interface")
  python3 tools/sch_query.py pdm-4ch ref C14 [R12 …]                         a part and what each pin connects to
  python3 tools/sch_query.py pdm-4ch net SW_SUPPLY                            members of the nets matching a name
  python3 tools/sch_query.py pdm-4ch erc                                      ERC counts and violations
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD_SCH = {'pdm-4ch': 'hardware/pdm-4ch/ESP32-PDM-4CH.kicad_sch', 'pdm-hc2': 'hardware/pdm-hc2/ESP32-PDM-HC2.kicad_sch'}
KICAD_BIN_DIR = os.environ.get('KICAD_BIN_DIR', '/Applications/KiCad/KiCad.app/Contents/MacOS')
ENV = dict(os.environ, PATH=f"{KICAD_BIN_DIR}:{os.environ.get('PATH', '')}")


def netlist(board, tmp):
    out = Path(tmp) / 'net.xml'
    r = subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(out),
                        str(ROOT / BOARD_SCH[board])], capture_output=True, text=True, env=ENV)
    if r.returncode or not out.exists():
        sys.exit(f'kicad-cli failed: {r.stderr.strip()[-300:]}')
    root = ET.parse(out).getroot()
    comps = {}
    for c in root.iter('comp'):
        fields = {f.get('name'): (f.text or '') for f in c.iter('field')}
        sheet = c.find('sheetpath')
        comps[c.get('ref')] = dict(value=c.findtext('value'), footprint=c.findtext('footprint'),
                                   lcsc=fields.get('LCSC', ''), sheet=sheet.get('names') if sheet is not None else '',
                                   dnp=any(p.get('name') == 'dnp' for p in c.iter('property')))
    nets = [(n.get('name'), [(x.get('ref'), x.get('pin'), x.get('pinfunction') or '') for x in n.iter('node')])
            for n in root.iter('net')]
    return comps, nets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', choices=BOARD_SCH)
    ap.add_argument('what', choices=('parts', 'ref', 'net', 'erc'))
    ap.add_argument('names', nargs='*')
    ap.add_argument('--sheet', help='parts on sheets whose path contains this')
    ap.add_argument('--match', help='parts whose ref, value or footprint contains this')
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        if a.what == 'erc':
            out = Path(tmp) / 'erc.json'
            subprocess.run(['kicad-cli', 'sch', 'erc', '--format', 'json', '-o', str(out), str(ROOT / BOARD_SCH[a.board])],
                           capture_output=True, env=ENV)
            v = [x for s in json.loads(out.read_text())['sheets'] for x in s['violations']]
            print(f"{sum(x['severity'] == 'error' for x in v)} errors, {sum(x['severity'] == 'warning' for x in v)} warnings")
            for x in v:
                items = '; '.join(i.get('description', '') for i in x.get('items', []))
                print(f"  {x['severity']} {x['type']}: {x.get('description', '')} – {items}"[:220])
            return
        comps, nets = netlist(a.board, tmp)
        if a.what == 'parts':
            for ref in sorted(comps, key=lambda r: (r.rstrip('0123456789'), int(''.join(filter(str.isdigit, r)) or 0))):
                c = comps[ref]
                if a.sheet and a.sheet.lower() not in c['sheet'].lower():
                    continue
                if a.match and not any(a.match in (s or '') for s in (ref, c['value'], c['footprint'])):
                    continue
                print(f"{ref:7} {c['value'] or '':18} {c['lcsc'] or '-':10} {'DNP ' if c['dnp'] else ''}"
                      f"{(c['footprint'] or '').split(':')[-1]:32} {c['sheet']}")
        elif a.what == 'ref':
            for ref in a.names:
                c = comps.get(ref)
                if not c:
                    print(f'{ref}: not on this board')
                    continue
                print(f"{ref} {c['value']} {c['lcsc'] or 'no LCSC'} {'DNP ' if c['dnp'] else ''}{c['footprint']} "
                      f"({c['sheet']})")
                for name, nodes in nets:
                    for r, pin, fn in nodes:
                        if r == ref:
                            others = [f'{x}.{p}' for x, p, _ in nodes if x != ref]
                            shown = ', '.join(others[:20]) + (f' … and {len(others) - 20} more' if len(others) > 20 else '')
                            print(f"  pin {pin}{' ' + fn if fn else ''} → {name}: {shown or '(nothing else)'}")
        else:
            for name, nodes in nets:
                if any(n.lower() in name.lower() for n in a.names):
                    print(f"{name} ({len(nodes)}): " + ', '.join(f'{r}.{p}' for r, p, _ in nodes))


if __name__ == '__main__':
    main()
