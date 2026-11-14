"""Quilter trial (owner, 2026-11-14): export a copy of the pdm-4ch board for Quilter to route only the open connections.

Run under KiCad's Python, KiCad closed:
  KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
  $KPY -I hardware/pdm-4ch/scripts/quilter_export.py <out_dir>

The board in the repo is never changed. The copy in <out_dir>:
- every footprint, track, via and zone is locked (Quilter keeps parts inside the outline and pre-routed copper as is);
- dangling signal copper is pruned with routing_build.prune() (Quilter keeps orphan segments, so they would block);
- In1.Cu gets the user name "GND" (Quilter detects plane layers by name);
- export-only rule areas carry the build's router rules that are not in the board file: no tracks on In1.Cu
  (decision 165) and no tracks or vias under the antenna on the inner layers (the module keep-out covers F/B only).
Quilter's copper comes back only as tracks and vias; it goes through quilter_import (to be written once a candidate
exists) into fixed_routes.py and the normal build gates (decisions 163, 166, 172, 212, heat budget). Its pours are
never taken.
"""
import json, os, shutil, sys
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import routing_build as rb  # noqa: E402

NAME = 'ESP32-PDM-4CH'
# pours Quilter must keep (its "Preserved pours" table): the power copper and the In1 planes. GND-F/GND-B/GND-In2 and
# GND_CAN-F/B/In2 are left to Quilter so it may route through them; the build refills its own GND pours afterwards.
PRESERVE = ['VS-B-front', 'VS-B-rear', 'VS-B-spine', 'VS-F-drain', 'VS-In2', 'VBAT_IN-F', 'VBAT_IN-B',
            'VBAT_FL-F', 'VBAT_FL-B', 'OUT1-B', 'OUT1-F-J11', 'OUT1-F-U11', 'OUT2-F', 'OUT3-F', 'OUT4-F',
            'GND-In1', 'GND_CAN-In1']


def rule_area(b, name, layers, poly, tracks=True, vias=True):
    z = pcbnew.ZONE(b)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(l)
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowZoneFills(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    o = z.Outline()
    o.NewOutline()
    for p in poly:
        o.Append(p.x, p.y)
    z.SetLocked(True)
    b.Add(z)


def main(out):
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(PROJ):
        if f.endswith(('.kicad_sch', '.kicad_pro')) or f.endswith('-lib-table'):
            shutil.copy(os.path.join(PROJ, f), out)
    b = pcbnew.LoadBoard(os.path.join(PROJ, NAME + '.kicad_pcb'))
    pruned = rb.prune(b)
    for fp in b.GetFootprints():
        fp.SetLocked(True)
    for t in b.GetTracks():
        t.SetLocked(True)
    names = set()
    for z in b.Zones():
        z.SetLocked(True)
        names.add(z.GetZoneName())
    missing = [n for n in PRESERVE if n not in names]
    if missing:
        sys.exit('pours not found: %s' % missing)
    b.SetLayerName(pcbnew.In1_Cu, 'GND')
    bb = b.GetBoardEdgesBoundingBox()
    rect = [pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()), pcbnew.VECTOR2I(bb.GetRight(), bb.GetTop()),
            pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()), pcbnew.VECTOR2I(bb.GetLeft(), bb.GetBottom())]
    rule_area(b, 'Quilter: no tracks on In1 (decision 165)', [pcbnew.In1_Cu], rect, tracks=True, vias=False)
    ant = 0
    for fp in b.GetFootprints():
        for z in fp.Zones():
            if z.GetZoneName() == 'Antenna':
                o = z.Outline().Outline(0)
                rule_area(b, 'Quilter: antenna inner layers', [pcbnew.In1_Cu, pcbnew.In2_Cu],
                          [o.CPoint(i) for i in range(o.PointCount())])
                ant += 1
    if not ant:
        sys.exit('antenna keep-out not found')
    pcbnew.SaveBoard(os.path.join(out, NAME + '.kicad_pcb'), b)
    ox, oy = rb.origin(b)
    json.dump({'tracks': sum(1 for t in b.GetTracks() if t.GetClass() != 'PCB_VIA'),
               'vias': sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA'),
               'origin_nm': [ox, oy], 'pruned': pruned, 'preserve': PRESERVE},
              open(os.path.join(out, 'export.json'), 'w'), indent=1)
    open_items = unconnected(os.path.join(out, NAME + '.kicad_pcb'))
    with open(os.path.join(out, 'UPLOAD.md'), 'w') as f:
        f.write(UPLOAD % {'n': len(open_items), 'preserve': '\n'.join('- ' + p for p in PRESERVE),
                          'open': '\n'.join('- ' + s for s in open_items)})
    print('exported to', out, '| pruned', len(pruned), '| antenna areas', ant, '| unconnected', len(open_items))


def unconnected(pcb):
    import subprocess, tempfile
    kc = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
    with tempfile.TemporaryDirectory() as td:
        rep = os.path.join(td, 'drc.json')
        subprocess.run([kc, 'pcb', 'drc', '--format', 'json', '--schematic-parity', '-o', rep, pcb],
                       capture_output=True)
        d = json.load(open(rep))
    return [' <-> '.join(i['description'] for i in v['items']) for v in d['unconnected_items']]


UPLOAD = """# pdm-4ch – Quilter upload (trial, owner 2026-11-14)

Generated by `hardware/pdm-4ch/scripts/quilter_export.py`. Do not edit; re-run the script instead.

## Upload (quilter.ai, free tier)

1. New project. Upload the files one by one (Quilter takes no zip): `ESP32-PDM-4CH.kicad_pcb` (board, required),
   `ESP32-PDM-4CH.kicad_pro` and all five `.kicad_sch` sheets.
   Quilter does not document KiCad 10 (this board is KiCad 10 format). If the parser refuses it, stop and note it.
2. **Placement:** every part is inside the outline, so Quilter keeps every part where it is. Nothing to place.
3. **Stackup:** pick the stackup **from the input file** (top option): 4 layers, 1.6 mm, outer 2 oz, inner 0.5 oz;
   In1 is named GND. Do not pick a Quilter stock stackup: Quilter then deletes and regenerates the inner-layer copper,
   and our In2 routes (J6 bundle, exit column) live there.
4. **Preserved pours:** tick exactly these:
%(preserve)s
   Leave GND-F, GND-B, GND-In2 and GND_CAN-F/B/In2 unticked: Quilter may route through them; we only take its tracks
   and vias back and our build refills GND itself.
5. **Pre-routed copper:** all tracks and vias are locked and must stay. Keep-outs: the four hole keep-outs, the
   antenna keep-out, and two Quilter-only areas (no tracks on In1; no tracks/vias under the antenna on In1/In2).
6. **Fabricator:** JLCPCB. Do not lower any minimum below the board file's rules.
7. Submit. Results take 15 min to 24 h. Download the best candidates (fewest unrouted) as KiCad files and put them
   in a folder for the import step; do not open them over the repo board.

## What Quilter should route (%(n)s open items)

%(open)s

## Judging a candidate

A candidate counts only after its new tracks/vias go into `fixed_routes.py` and `build_routing.sh` accepts the
build: 0 DRC errors, parity 0, fewer unconnected, every pour gate (decisions 166, 172, 212), GND fragments with
>= 2 ties, VS-In2 one island >= 1012.1 mm2 with 40/40 thermal vias, heat budget at 40 C. Taking Quilter copper into
the build amends decisions 163/181 and is the owner's call.

## Terms to keep in mind

Free tier: personal/academic and eligible exploratory R&D; Quilter may use the input files for training (the repo is
public anyway). Check that putting the routed result into the MIT repo is fine under the current Quilter terms.
"""


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
