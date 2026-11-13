#!/bin/zsh
# Routing build for pdm-4ch (decision 163 as amended by Q-0072: no Freerouting). Run with KiCad closed:
#   hardware/pdm-4ch/scripts/build_routing.sh            (env KEEP_WORK, LAND_BEST optional)
# 1 fixed copper (locked) + fixed_routes.py (hand routes, the kept T-0236 copper and the maze_route.py routes),
#   unlocked tracks/vias removed                                              (routing_build.py prep)
# 2 zones refilled, GND stitching, dangling vias/stubs removed, pour + thermal checks  (routing_build.py apply -)
# 3 checks: `kpcb drc` with parity
# 4 the result (0 DRC errors, parity 0, pours whole) replaces the board only when it has fewer unconnected items
#   than the board now has. Env LAND_BEST=1 lands it even without fewer unconnected: use it once after
#   fixed_routes.py changed, so the board is again the output of the scripts.
# Every signal track comes from fixed_routes.py; new routes are generated with geom_export.py + maze_route.py.
set -u
RUNS=1
SCRIPTS=${0:A:h}; PROJ=${SCRIPTS:h}; REPO=${PROJ:h:h}
BOARD=$PROJ/ESP32-PDM-4CH.kicad_pcb
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
WORK=${KEEP_WORK:-$(mktemp -d -t pdm4-route)}
mkdir -p $WORK/proj
echo "work folder: $WORK"
cp $PROJ/*.kicad_sch $PROJ/*.kicad_pro $PROJ/fp-lib-table $PROJ/sym-lib-table $WORK/proj/ 2>/dev/null
cp $BOARD $WORK/proj/
$KPY -I $SCRIPTS/routing_build.py prep $WORK/proj/ESP32-PDM-4CH.kicad_pcb $WORK 2>&1 | grep -v -e assert -e swig -e '^$' || exit 1

drc() {  # board -> "errors unconnected parity"
  python3 $REPO/tools/kpcb.py pdm-4ch --pcb $1 drc 2>/dev/null | grep '^{' | head -1
}
# the reference: the board as it is now (only the locks may differ)
REF=$(drc $WORK/proj/ESP32-PDM-4CH.kicad_pcb); echo "board now: $REF"
REF_UNC=$(echo $REF | python3 -c 'import json,sys; print(json.load(sys.stdin)["unconnected"])')

BEST=""; BEST_UNC=999999
for i in $(seq 1 $RUNS); do
  R=$WORK/r$i
  mkdir -p $R/proj; cp $WORK/proj/*.kicad_sch $WORK/proj/*.kicad_pro $WORK/proj/*-lib-table $R/proj/
  $KPY -I $SCRIPTS/routing_build.py apply $WORK - $R/proj/ESP32-PDM-4CH 2>&1 | grep -v -e assert -e swig -e '^$'
  mv $R/proj/ESP32-PDM-4CH.json $R/pour.json
  D=$(drc $R/proj/ESP32-PDM-4CH.kicad_pcb); echo "r$i: $D"; echo $D > $R/drc.json
  OK=$(python3 - $R <<'PY'
import json, sys
r = sys.argv[1]; d = json.load(open(r + '/drc.json')); p = json.load(open(r + '/pour.json'))
ok = d['errors'] == 0 and d['parity'] == 0 and not p['split'] and not d['bottom_smt'] and not d['hole_keepout']
print(d['unconnected'] if ok else -1)
PY
)
  OK=${OK:--1}   # T-0259: a crashed prep/apply leaves no result: never "kept"
  if [[ $OK -ge 0 && $OK -lt $BEST_UNC ]]; then BEST=$i; BEST_UNC=$OK; fi
done
# compare with the board as it is now (another build may have landed meanwhile)
mkdir -p $WORK/now; cp $PROJ/*.kicad_sch $PROJ/*.kicad_pro $PROJ/*-lib-table $BOARD $WORK/now/
REF=$(drc $WORK/now/ESP32-PDM-4CH.kicad_pcb)
REF_UNC=$(echo $REF | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["unconnected"] if d["errors"]==0 else 999999)')
if [[ -n $BEST && ( $BEST_UNC -lt $REF_UNC || ${LAND_BEST:-0} == 1 ) ]]; then
  cp $WORK/r$BEST/proj/ESP32-PDM-4CH.kicad_pcb $BOARD
  echo "KEPT r$BEST: $BEST_UNC unconnected (board had $REF_UNC)"
else
  echo "board unchanged (best clean run: ${BEST:-none} $BEST_UNC, board $REF_UNC)"
fi
