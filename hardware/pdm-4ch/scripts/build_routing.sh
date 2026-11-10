#!/bin/zsh
# Routing build for pdm-4ch (decision 163). Run with KiCad closed:
#   hardware/pdm-4ch/scripts/build_routing.sh [runs=3] [passes=25]   (env FR_STRATS, KEEP_WORK optional)
# 1 fixed copper (locked) + fixed_routes.py, unlocked tracks/vias removed   (routing_build.py prep)
# 2 fills cleared; power outlines = keep-outs for foreign nets; antenna, CAN barrier, JP30/JP1, holes on all layers
# 3 Freerouting 2.5.0 headless, <runs> runs in parallel (max 3), each in its own folder
# 4 SES imported, zones refilled, GND stitching, dangling vias/stubs removed  (routing_build.py apply)
# 5 checks: pours whole, `kpcb drc` with parity
# 6 the best clean run (0 DRC errors, parity 0, pours whole, fewest unconnected) replaces the board only when it has
#   fewer unconnected items than the board now has. Env KEEP_WORK=<dir> uses that folder instead of a temp one.
set -u
RUNS=${1:-3}; PASSES=${2:-25}
[[ $RUNS -gt 3 ]] && RUNS=3
STRATS=(${=FR_STRATS:-prioritized sequential random})   # env FR_STRATS overrides, one per run
SCRIPTS=${0:A:h}; PROJ=${SCRIPTS:h}; REPO=${PROJ:h:h}
BOARD=$PROJ/ESP32-PDM-4CH.kicad_pcb
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
JAVA=${JAVA:-$HOME/.local/opt/jdk-25.0.4.1+1/Contents/Home/bin/java}
FR=${FREEROUTING:-$HOME/.local/opt/freerouting-2.5.0/freerouting-2.5.0.jar}
WORK=${KEEP_WORK:-$(mktemp -d -t pdm4-route)}
mkdir -p $WORK/proj
echo "work folder: $WORK"
cp $PROJ/*.kicad_sch $PROJ/*.kicad_pro $PROJ/fp-lib-table $PROJ/sym-lib-table $WORK/proj/ 2>/dev/null
cp $BOARD $WORK/proj/
$KPY -I $SCRIPTS/routing_build.py prep $WORK/proj/ESP32-PDM-4CH.kicad_pcb $WORK 2>&1 | grep -v -e assert -e swig -e '^$' || exit 1
[[ -f $WORK/route.dsn ]] || { echo "no DSN"; exit 1; }

drc() {  # board -> "errors unconnected parity"
  python3 $REPO/tools/kpcb.py pdm-4ch --pcb $1 drc 2>/dev/null | grep '^{' | head -1
}
# the reference: the board as it is now (only the locks may differ)
REF=$(drc $WORK/proj/ESP32-PDM-4CH.kicad_pcb); echo "board now: $REF"
REF_UNC=$(echo $REF | python3 -c 'import json,sys; print(json.load(sys.stdin)["unconnected"])')

for i in $(seq 1 $RUNS); do
  mkdir -p $WORK/r$i; cp $WORK/route.dsn $WORK/r$i/in.dsn
  # Freerouting is deterministic for one input: each run gets its own item-selection strategy
  ( cd $WORK/r$i && $JAVA -Djava.awt.headless=true -jar $FR --gui.enabled=false -de in.dsn -do out.ses \
      -mt 1 -mp $PASSES -is ${STRATS[$i]} > fr.log 2>&1 ) &
done
wait
BEST=""; BEST_UNC=999999
for i in $(seq 1 $RUNS); do
  R=$WORK/r$i
  [[ -f $R/out.ses ]] || { echo "r$i: no SES"; continue; }
  mkdir -p $R/proj; cp $WORK/proj/*.kicad_sch $WORK/proj/*.kicad_pro $WORK/proj/*-lib-table $R/proj/
  $KPY -I $SCRIPTS/routing_build.py apply $WORK $R/out.ses $R/proj/ESP32-PDM-4CH 2>&1 | grep -v -e assert -e swig -e '^$'
  mv $R/proj/ESP32-PDM-4CH.json $R/pour.json
  D=$(drc $R/proj/ESP32-PDM-4CH.kicad_pcb); echo "r$i: $D"; echo $D > $R/drc.json
  OK=$(python3 - $R <<'PY'
import json, sys
r = sys.argv[1]; d = json.load(open(r + '/drc.json')); p = json.load(open(r + '/pour.json'))
ok = d['errors'] == 0 and d['parity'] == 0 and not p['split'] and not d['bottom_smt'] and not d['hole_keepout']
print(d['unconnected'] if ok else -1)
PY
)
  if [[ $OK -ge 0 && $OK -lt $BEST_UNC ]]; then BEST=$i; BEST_UNC=$OK; fi
done
# compare with the board as it is now (another build may have landed meanwhile)
mkdir -p $WORK/now; cp $PROJ/*.kicad_sch $PROJ/*.kicad_pro $PROJ/*-lib-table $BOARD $WORK/now/
REF=$(drc $WORK/now/ESP32-PDM-4CH.kicad_pcb)
REF_UNC=$(echo $REF | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["unconnected"] if d["errors"]==0 else 999999)')
if [[ -n $BEST && $BEST_UNC -lt $REF_UNC ]]; then
  cp $WORK/r$BEST/proj/ESP32-PDM-4CH.kicad_pcb $BOARD
  echo "KEPT r$BEST: $BEST_UNC unconnected (board had $REF_UNC)"
else
  echo "board unchanged (best clean run: ${BEST:-none} $BEST_UNC, board $REF_UNC)"
fi
