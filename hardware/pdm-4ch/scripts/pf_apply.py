"""Decision 215: put the router's result on the base board. KiCad python:
  pf_apply.py <work dir> [out.kicad_pcb]
Adds <work>/routes.json (pf_route.py) to <work>/base.kicad_pcb as locked tracks and vias, refills the zones and saves
<work>/routed.kicad_pcb (or the given file). Check it with `kicad-cli pcb drc`."""
import json, os, sys
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import routing_build as rb

work = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(work, 'routed.kicad_pcb')
b = pcbnew.LoadBoard(os.path.join(work, 'base.kicad_pcb'))
r = json.load(open(os.path.join(work, 'routes.json')))
M = pcbnew.FromMM
nt = 0
for t in r['tracks']:
    net = b.FindNet(t['net']); lay = b.GetLayerID(t['layer'])
    for a, e in zip(t['pts'], t['pts'][1:]):
        s = pcbnew.PCB_TRACK(b); s.SetStart(rb.P(b, *a)); s.SetEnd(rb.P(b, *e)); s.SetWidth(M(t['width']))
        s.SetLayer(lay); s.SetNet(net); s.SetLocked(True); b.Add(s); nt += 1
for v in r['vias']:
    x = pcbnew.PCB_VIA(b); x.SetPosition(rb.P(b, *v['at'])); x.SetViaType(pcbnew.VIATYPE_THROUGH)
    x.SetWidth(pcbnew.F_Cu, M(0.6)); x.SetDrill(M(0.3)); x.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    x.SetNet(b.FindNet(v['net'])); x.SetLocked(True); b.Add(x)
rb.fill(b)
pcbnew.SaveBoard(out, b)
print('added', nt, 'segments,', len(r['vias']), 'vias ->', out)
