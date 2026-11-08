#!/usr/bin/env python3
"""Scripted PCB editing and checks for the pcb-fixer agent (decision 130). Runs under KiCad's bundled Python
(it re-runs itself there when `pcbnew` is missing). Every command takes the board name first.

  python3 tools/kpcb.py pdm-4ch sync                 import/refresh footprints and nets from the schematic
  python3 tools/kpcb.py pdm-4ch list [--refs J10,Q30] [--off] [--nets]
  python3 tools/kpcb.py pdm-4ch place --file moves.json         [{"ref": "J10", "x": 3, "y": 20, "rot": 90}, ...]
  python3 tools/kpcb.py pdm-4ch place J10 3 20 90
  python3 tools/kpcb.py pdm-4ch zone --net VS --layer F.Cu --pts 10,10 40,10 40,30 10,30 [--priority 1]
                                     [--clearance 0.3] [--min-width 0.25] [--name VS-top] [--thermal 0.5,0.5|solid]
  python3 tools/kpcb.py pdm-4ch track --net /SW1 --width 0.25 --layer F.Cu --pts 10,10 20,10 20,15
  python3 tools/kpcb.py pdm-4ch via --net GND --at 12,14 [--size 0.6 --drill 0.3]
  python3 tools/kpcb.py pdm-4ch delete --net /SW1 | --zone VS-top | --track-at 12,14
  python3 tools/kpcb.py pdm-4ch text "BATTERY +" --at 5,3 [--layer F.SilkS --size 1.2 --rot 0]
  python3 tools/kpcb.py pdm-4ch fill                 refill all zones
  python3 tools/kpcb.py pdm-4ch drc                  DRC with schematic parity: counts and the first violations
  python3 tools/kpcb.py pdm-4ch render out.png [--layers F.Cu,B.Cu,F.SilkS,Edge.Cuts,F.CrtYd]

Coordinates are millimetres from the board's top-left outline corner (x right, y down); rot in degrees. New
footprints from `sync` are parked in a grid to the right of the board until placed. Only the top side is used
(decision 122): `place` never flips a part to the bottom. The schematic is never touched.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KICAD_APP = Path(os.environ.get('KICAD_APP', '/Applications/KiCad/KiCad.app'))
KICAD_PY = KICAD_APP / 'Contents/Frameworks/Python.framework/Versions/Current/bin/python3'
KICAD_CLI = KICAD_APP / 'Contents/MacOS/kicad-cli'
STOCK_FP = KICAD_APP / 'Contents/SharedSupport/footprints'
BOARDS = {'pdm-4ch': 'hardware/pdm-4ch/ESP32-PDM-4CH', 'pdm-hc2': 'hardware/pdm-hc2/ESP32-PDM-HC2'}

try:
    import pcbnew
except ImportError:
    if KICAD_PY.exists() and os.environ.get('KPCB_REEXEC') != '1':
        os.execve(str(KICAD_PY), [str(KICAD_PY), '-I', __file__, *sys.argv[1:]], dict(os.environ, KPCB_REEXEC='1'))
    sys.exit('kpcb: KiCad Python with pcbnew not found (set KICAD_APP)')

MM = pcbnew.FromMM
TO_MM = pcbnew.ToMM


PCB_OVERRIDE = None  # --pcb: work on another board file (the orchestrator's gate reads the base version this way)


def paths(board):
    stem = ROOT / BOARDS[board]
    return (Path(PCB_OVERRIDE) if PCB_OVERRIDE else stem.with_suffix('.kicad_pcb')), stem.with_suffix('.kicad_sch')


def origin(b):
    """Top-left corner and size of the Edge.Cuts outline (board coordinates are relative to it)."""
    box = b.GetBoardEdgesBoundingBox()
    return box.GetX(), box.GetY(), box.GetWidth(), box.GetHeight()


def to_board(b, x, y):
    ox, oy, _, _ = origin(b)
    return pcbnew.VECTOR2I(ox + MM(float(x)), oy + MM(float(y)))


def rel(b, p):
    ox, oy, _, _ = origin(b)
    return round(TO_MM(p.x - ox), 3), round(TO_MM(p.y - oy), 3)


def layer_id(b, name):
    lid = b.GetLayerID(name)
    if lid < 0:
        sys.exit(f'kpcb: unknown layer {name}')
    return lid


def net(b, name, create=False):
    n = b.FindNet(name)
    if n is None and create:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
    if n is None:
        sys.exit(f'kpcb: no net {name!r} on the board (run sync first; names as in `list --nets`)')
    return n


def pts(b, items):
    out = []
    for s in items:
        x, y = s.split(',')
        out.append(to_board(b, x, y))
    return out


def save(b, board):
    pcbnew.SaveBoard(str(paths(board)[0]), b)


def on_board(b, f):
    ox, oy, w, h = origin(b)
    p = f.GetPosition()
    return ox <= p.x <= ox + w and oy <= p.y <= oy + h


# ---------------------------------------------------------------- netlist import

def export_netlist(sch, d):
    out = Path(d) / 'net.xml'
    r = subprocess.run([str(KICAD_CLI), 'sch', 'export', 'netlist', '--format', 'kicadxml', '-o', str(out), str(sch)],
                       capture_output=True, text=True)
    if r.returncode or not out.exists():
        sys.exit(f'kpcb: netlist export failed: {(r.stderr or r.stdout).strip()[-300:]}')
    return ET.parse(out).getroot()


def lib_dirs(board_dir):
    """Footprint library nickname -> folder: KiCad's stock libraries, overridden by the project fp-lib-table."""
    dirs = {p.stem: p for p in STOCK_FP.glob('*.pretty')}
    table = board_dir / 'fp-lib-table'
    if table.exists():
        for name, uri in re.findall(r'\(name "([^"]+)"\)\(type "[^"]+"\)\(uri "([^"]+)"\)', table.read_text()):
            dirs[name] = Path(uri.replace('${KIPRJMOD}', str(board_dir))).resolve()
    return dirs


def cmd_sync(b, board, args):
    pcb_path, sch = paths(board)
    with tempfile.TemporaryDirectory() as d:
        root = export_netlist(sch, d)
    dirs = lib_dirs(pcb_path.parent)
    comps = {}
    for c in root.iter('comp'):
        props = {p.get('name'): p.get('value') for p in c.iter('property')}
        if 'exclude_from_board' in props:
            continue
        sp = c.find('sheetpath')
        fields = {f.get('name'): (f.text or '') for f in c.iter('field')}
        comps[c.get('ref')] = dict(fp=c.findtext('footprint') or '', value=c.findtext('value') or '',
                                   dnp='dnp' in props, no_bom='exclude_from_bom' in props,
                                   no_pos='exclude_from_pos_files' in props, fields=fields,
                                   path=(sp.get('tstamps') if sp is not None else '/') + (c.findtext('tstamps') or ''))
    pad_nets = {}
    for n in root.iter('net'):
        for node in n.iter('node'):
            pad_nets[(node.get('ref'), node.get('pin'))] = n.get('name')
    have = {f.GetReference(): f for f in b.GetFootprints()}
    _, _, w, _ = origin(b)
    park = [TO_MM(w) + 10, 0.0]
    added, replaced, removed, nofp = [], [], [], []
    for ref, c in sorted(comps.items()):
        if not c['fp']:
            nofp.append(ref)
            continue
        f = have.get(ref)
        if f is None or f.GetFPIDAsString() != c["fp"]:
            pos = f.GetPosition() if f is not None else None
            rot = f.GetOrientationDegrees() if f is not None else 0
            if f is not None:
                b.Remove(f)
                replaced.append(ref)
            lib, name = c['fp'].split(':', 1)
            if lib not in dirs:
                sys.exit(f'kpcb: footprint library {lib!r} of {ref} not found')
            f = pcbnew.FootprintLoad(str(dirs[lib]), name)
            if f is None:
                sys.exit(f'kpcb: footprint {c["fp"]} of {ref} not found in {dirs[lib]}')
            f.SetFPID(pcbnew.LIB_ID(lib, name))
            b.Add(f)
            if pos is None:
                f.SetPosition(to_board(b, park[0], park[1]))
                park[1] += TO_MM(f.GetBoundingBox(False).GetHeight()) + 2
                if park[1] > 120:
                    park = [park[0] + 25, 0.0]
                added.append(ref)
            else:
                f.SetPosition(pos)
                f.SetOrientationDegrees(rot)
        f.SetReference(ref)
        f.SetValue(c['value'])
        f.SetPath(pcbnew.KIID_PATH(c['path']))
        f.SetDNP(c['dnp'])
        f.SetExcludedFromBOM(c['no_bom'])
        f.SetExcludedFromPosFiles(c['no_pos'])
        for k, v in c['fields'].items():  # schematic parity compares the symbol fields (LCSC, …)
            if k not in ('Reference', 'Value', 'Footprint'):
                f.SetField(k, v)
                fld = f.GetField(k)
                if fld is not None:
                    fld.SetVisible(False)  # data only, never on the silkscreen
        for pad in f.Pads():
            name = pad_nets.get((ref, pad.GetNumber()))
            if name:
                pad.SetNet(net(b, name, create=True))
            else:
                pad.SetNetCode(0)
    for ref, f in have.items():
        if ref not in comps or not comps[ref]['fp']:
            b.Remove(f)
            removed.append(ref)
    save(b, board)
    print(json.dumps(dict(added=len(added), replaced=replaced, removed=removed, no_footprint=nofp,
                          footprints=len(b.GetFootprints()))))


# ---------------------------------------------------------------- editing

def cmd_list(b, board, args):
    if args.nets:
        print(json.dumps(sorted(str(n) for n in b.GetNetsByName().keys() if str(n))))
        return
    refs = set(args.refs.split(',')) if args.refs else None
    out = []
    for f in sorted(b.GetFootprints(), key=lambda f: f.GetReference()):
        if (refs and f.GetReference() not in refs) or (args.off and on_board(b, f)):
            continue
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        box = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        x0, y0 = rel(b, pcbnew.VECTOR2I(box.GetX(), box.GetY()))
        x, y = rel(b, f.GetPosition())
        out.append(dict(ref=f.GetReference(), value=f.GetValue(), fp=str(f.GetFPID().GetLibItemName()),
                        x=x, y=y, rot=round(f.GetOrientationDegrees(), 1),
                        side='bottom' if f.IsFlipped() else 'top', on_board=on_board(b, f),
                        box=[x0, y0, round(TO_MM(box.GetWidth()), 2), round(TO_MM(box.GetHeight()), 2)],
                        nets=sorted({p.GetNetname() for p in f.Pads() if p.GetNetname()})[:8]))
    print(json.dumps(out))


def cmd_place(b, board, args):
    moves = (json.loads(Path(args.file).read_text()) if args.file
             else [dict(ref=args.ref, x=args.x, y=args.y, rot=args.rot or 0)])
    fps = {f.GetReference(): f for f in b.GetFootprints()}
    for m in moves:
        f = fps.get(m['ref'])
        if f is None:
            sys.exit(f"kpcb: no footprint {m['ref']} (run sync)")
        if f.IsFlipped():  # decision 122: top side only
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetPosition(to_board(b, m['x'], m['y']))
        f.SetOrientationDegrees(float(m.get('rot', 0)))
    save(b, board)
    print(f'placed {len(moves)}')


def cmd_zone(b, board, args):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer_id(b, args.layer))
    z.SetNet(net(b, args.net))
    ol = z.Outline()
    ol.NewOutline()
    for p in pts(b, args.pts):
        ol.Append(p.x, p.y)
    z.SetAssignedPriority(args.priority)
    z.SetLocalClearance(MM(args.clearance))
    z.SetMinThickness(MM(args.min_width))
    if args.name:
        z.SetZoneName(args.name)
    if args.thermal == 'solid':
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    else:
        gap, spoke = (float(v) for v in args.thermal.split(','))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(gap))
        z.SetThermalReliefSpokeWidth(MM(spoke))
    b.Add(z)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    save(b, board)
    print(f'zone {args.name or args.net} on {args.layer}')


def cmd_track(b, board, args):
    p = pts(b, args.pts)
    n, lid = net(b, args.net), layer_id(b, args.layer)
    for a, c in zip(p, p[1:]):
        t = pcbnew.PCB_TRACK(b)
        t.SetStart(a)
        t.SetEnd(c)
        t.SetWidth(MM(args.width))
        t.SetLayer(lid)
        t.SetNet(n)
        b.Add(t)
    save(b, board)
    print(f'{len(p) - 1} segments on {args.net}')


def cmd_via(b, board, args):
    v = pcbnew.PCB_VIA(b)
    x, y = args.at.split(',')
    v.SetPosition(to_board(b, x, y))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(MM(args.size))
    v.SetDrill(MM(args.drill))
    v.SetNet(net(b, args.net))
    b.Add(v)
    save(b, board)
    print(f'via {args.net} at {args.at}')


def cmd_delete(b, board, args):
    gone = 0
    if args.net:
        for t in list(b.GetTracks()):
            if t.GetNetname() == args.net:
                b.Remove(t)
                gone += 1
    if args.zone:
        for z in list(b.Zones()):
            if z.GetZoneName() == args.zone and not z.GetIsRuleArea():
                b.Remove(z)
                gone += 1
    if args.track_at:
        x, y = args.track_at.split(',')
        p = to_board(b, x, y)
        for t in list(b.GetTracks()):
            if t.HitTest(p, MM(0.1)):
                b.Remove(t)
                gone += 1
    save(b, board)
    print(f'deleted {gone}')


def cmd_text(b, board, args):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(args.text)
    x, y = args.at.split(',')
    t.SetPosition(to_board(b, x, y))
    t.SetLayer(layer_id(b, args.layer))
    t.SetTextSize(pcbnew.VECTOR2I(MM(args.size), MM(args.size)))
    t.SetTextThickness(MM(args.size * 0.15))
    t.SetTextAngleDegrees(args.rot)
    b.Add(t)
    save(b, board)
    print(f'text {args.text!r}')


def cmd_fill(b, board, args):
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    save(b, board)
    print('zones filled')


# ---------------------------------------------------------------- checks

def drc_report(pcb_path):
    """kicad-cli DRC with schematic parity on one board file; returns the parsed JSON report."""
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / 'drc.json'
        r = subprocess.run([str(KICAD_CLI), 'pcb', 'drc', '--format', 'json', '--schematic-parity',
                            '--severity-all', '-o', str(out), str(pcb_path)], capture_output=True, text=True)
        if not out.exists():
            sys.exit(f'kpcb: DRC failed: {(r.stderr or r.stdout).strip()[-300:]}')
        return json.loads(out.read_text())


def drc_summary(rep, box=None):
    """Counts. With box (x0, y0, x1, y1 in mm, absolute) a violation counts only when one of its items lies on the
    board: parts still parked beside it are not judged yet. Parity leaves out a missing footprint of a symbol that
    has none in the schematic (e.g. a DNP placeholder)."""
    def on(x):
        if box is None:
            return True
        return any(box[0] <= i['pos']['x'] <= box[2] and box[1] <= i['pos']['y'] <= box[3]
                   for i in x.get('items', []) if 'pos' in i)
    v = [x for x in rep.get('violations', []) if on(x)]
    parity = [x for x in rep.get('schematic_parity', [])
              if not (x.get('type') == 'missing_footprint' and not x.get('items'))]
    return dict(errors=sum(1 for x in v if x.get('severity') == 'error'),
                warnings=sum(1 for x in v if x.get('severity') == 'warning'),
                unconnected=len(rep.get('unconnected_items', [])), parity=len(parity))


def board_box(b):
    ox, oy, w, h = origin(b)
    return TO_MM(ox), TO_MM(oy), TO_MM(ox + w), TO_MM(oy + h)


def hole_intruders(b):
    """Parts (other than the mounting holes) whose courtyard reaches into a hole keep-out circle (decision 123)."""
    circles = []
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetZoneName().startswith('Keep-out H'):
            box = z.GetBoundingBox()
            circles.append((box.GetCenter().x, box.GetCenter().y, box.GetWidth() / 2))
    bad = set()
    for f in b.GetFootprints():
        if f.GetReference().startswith('H'):
            continue
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        box = cy.BBox() if cy.OutlineCount() else f.GetBoundingBox(False)
        for cx, cyy, r in circles:
            dx = max(box.GetX() - cx, 0, cx - (box.GetX() + box.GetWidth()))
            dy = max(box.GetY() - cyy, 0, cyy - (box.GetY() + box.GetHeight()))
            if dx * dx + dy * dy < r * r:
                bad.add(f.GetReference())
    return sorted(bad)


def bottom_smt(b):
    return sorted(f.GetReference() for f in b.GetFootprints()
                  if f.IsFlipped() and any(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in f.Pads()))


def cmd_drc(b, board, args):
    rep = drc_report(paths(board)[0])
    s = drc_summary(rep, board_box(b))
    s['bottom_smt'] = bottom_smt(b)
    s['hole_keepout'] = hole_intruders(b)
    s['parked'] = sorted(f.GetReference() for f in b.GetFootprints() if not on_board(b, f))
    print(json.dumps(s))
    for key in ('violations', 'schematic_parity', 'unconnected_items'):
        shown = 0
        for x in rep.get(key, []):
            if key == 'violations' and x.get('severity') not in ('error', 'warning'):
                continue
            if shown >= args.show:
                break
            shown += 1
            items = '; '.join(i.get('description', '') for i in x.get('items', []))[:160]
            print(f"  {key} {x.get('severity', '')} {x.get('type', '')}: {x.get('description', '')} – {items}")


def cmd_outline(b, board, args):
    """Fingerprint of what the layout stages must not change: the Edge.Cuts outline and the hole keep-outs."""
    edges = sorted(tuple(round(TO_MM(v), 3) for v in (d.GetStart().x, d.GetStart().y, d.GetEnd().x, d.GetEnd().y))
                   for d in b.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts)
    keep = sorted((z.GetZoneName(), round(TO_MM(z.GetBoundingBox().GetCenter().x), 3),
                   round(TO_MM(z.GetBoundingBox().GetCenter().y), 3), round(TO_MM(z.GetBoundingBox().GetWidth()), 3))
                  for z in b.Zones() if z.GetIsRuleArea() and z.GetZoneName().startswith('Keep-out H'))
    print(json.dumps(dict(edges=edges, keepouts=keep)))


def cmd_render(b, board, args):
    out = Path(args.out).resolve()
    with tempfile.TemporaryDirectory() as d:
        pdf = Path(d) / 'board.pdf'
        r = subprocess.run([str(KICAD_CLI), 'pcb', 'export', 'pdf', '--layers', args.layers, '--mode-single',
                            '-o', str(pdf), str(paths(board)[0])], capture_output=True, text=True)
        if not pdf.exists():
            sys.exit(f'kpcb: export failed: {(r.stderr or r.stdout).strip()[-300:]}')
        py = os.environ.get('PDM_PDF_PYTHON', 'python3')
        code = ('import sys\ntry:\n import pypdfium2 as p;d=p.PdfDocument(sys.argv[1]);'
                'd[0].render(scale=float(sys.argv[3])).to_pil().save(sys.argv[2])\n'
                'except ImportError:\n import pymupdf;d=pymupdf.open(sys.argv[1]);'
                'd[0].get_pixmap(dpi=int(72*float(sys.argv[3]))).save(sys.argv[2])')
        r = subprocess.run([py, '-I', '-c', code, str(pdf), str(out), str(args.scale)], capture_output=True, text=True)
        if r.returncode:
            sys.exit(f'kpcb: render needs pypdfium2 or pymupdf in $PDM_PDF_PYTHON: {r.stderr.strip()[-200:]}')
    print(out)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('board', choices=sorted(BOARDS))
    ap.add_argument('--pcb', help='board file to use instead of the board\'s own (read-only checks)')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('sync')
    sub.add_parser('outline')
    s = sub.add_parser('list')
    s.add_argument('--refs')
    s.add_argument('--off', action='store_true', help='only parts not yet on the board')
    s.add_argument('--nets', action='store_true', help='net names only')
    s = sub.add_parser('place')
    s.add_argument('ref', nargs='?')
    s.add_argument('x', nargs='?', type=float)
    s.add_argument('y', nargs='?', type=float)
    s.add_argument('rot', nargs='?', type=float)
    s.add_argument('--file')
    s = sub.add_parser('zone')
    s.add_argument('--net', required=True)
    s.add_argument('--layer', required=True)
    s.add_argument('--pts', nargs='+', required=True)
    s.add_argument('--priority', type=int, default=0)
    s.add_argument('--clearance', type=float, default=0.3)
    s.add_argument('--min-width', type=float, default=0.25)
    s.add_argument('--name')
    s.add_argument('--thermal', default='0.5,0.5')
    s = sub.add_parser('track')
    s.add_argument('--net', required=True)
    s.add_argument('--width', type=float, required=True)
    s.add_argument('--layer', default='F.Cu')
    s.add_argument('--pts', nargs='+', required=True)
    s = sub.add_parser('via')
    s.add_argument('--net', required=True)
    s.add_argument('--at', required=True)
    s.add_argument('--size', type=float, default=0.6)
    s.add_argument('--drill', type=float, default=0.3)
    s = sub.add_parser('delete')
    s.add_argument('--net')
    s.add_argument('--zone')
    s.add_argument('--track-at')
    s = sub.add_parser('text')
    s.add_argument('text')
    s.add_argument('--at', required=True)
    s.add_argument('--layer', default='F.SilkS')
    s.add_argument('--size', type=float, default=1.2)
    s.add_argument('--rot', type=float, default=0)
    sub.add_parser('fill')
    s = sub.add_parser('drc')
    s.add_argument('--show', type=int, default=15)
    s = sub.add_parser('render')
    s.add_argument('out')
    s.add_argument('--layers', default='F.Cu,B.Cu,F.SilkS,Edge.Cuts,F.CrtYd')
    s.add_argument('--scale', type=float, default=4.0)
    a = ap.parse_args()
    if a.cmd == 'place' and not a.file and a.ref is None:
        ap.error('place needs REF X Y [ROT] or --file')
    global PCB_OVERRIDE
    PCB_OVERRIDE = a.pcb
    b = pcbnew.LoadBoard(str(paths(a.board)[0]))
    globals()['cmd_' + a.cmd](b, a.board, a)


if __name__ == '__main__':
    main()
