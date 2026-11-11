# pdm-4ch – close the last connections by build (T-0211) – blocked

Date: 2026-11-11 · Role: pcb-fixer (unattended) · Board: `hardware/pdm-4ch/ESP32-PDM-4CH.kicad_pcb`

## Result

**Not finished: the board still has 78 unconnected items**, with 0 DRC errors and parity 0. The board file is
unchanged. No better clean build came out of the repo scripts. The schematic, `lib/`, the outline, the hole
keep-outs and the scripts are untouched.

The stage cannot reach 0 within its own rules. The open items are held by power-copper outlines and by locked
fixed routes. Changing either needs a ruling on power copper or the floorplan, and the build scripts are outside
this package's gate. Details and options: design-notes §8.18.

## Builds

| Build | Input | Result |
|---|---|---|
| b1 | `build_routing.sh 3`, repo scripts and board | r1: 0 errors, 79 unconnected → board unchanged (78). r2/r3 stopped, because they were identical to r1 |
| b2 | scratch copy: VS-In2 with a signal corridor (x 36–45.5 / y 6–30, x 45.5–56.5 / y 17–23) | 0 errors, 75 unconnected, pours whole (VS-In2 one island, 904 of 1220 mm²) |
| b3 | scratch copy: b2, plus the USB In2 run under U1 moved to B.Cu | 0 errors, 78 unconnected: 30 west, 44 strip, 4 J3. Moving the USB run to B.Cu only shifts the blockage, and the west group stays closed while the OUT3-F strip and the via keep-out in the remaining VS-In2 stay |

Scratch copies lived in the job folder and were never copied into the repo.

## Findings

- **MAJOR (blocked, one-way): the west channel parts are walled in by power copper (27 items).**
  - The open nets: DEN, SW_IN1–4, +3V3 (D102/D202/D402), IO0/2/3/5, EN, NTC, U12/U14-IS and R60.
  - The build makes every power outline a keep-out for foreign tracks and vias:
    - In2 is VS-In2 over x 26.5–56.5, y < 34;
    - B.Cu is the VS spine, VS-B-front and VS-B-rear;
    - F.Cu is closed by OUT2-F and the OUT3-F strip (x 44.3–45.85).
  - The only legal layer change is the 0.65 mm strip at x ≈ 46.15, and the USB pair uses it.
  - The locked USB In2 run under U1 (y 18.95/19.4) closes In2 east of x 56.5. So even the b2 corridor did not route
    one of these nets: IO2/IO5 still end at x 44.
- **MAJOR (blocked, one-way): the U1 strip and analog block are congested (47 items, 42 with the corridor).**
  - Q3–Q6 with R17–R24/R50/R51 sit right under U1's bottom pin row and the locked fan-out vias.
  - The U1 legs run south in the 6 mm strip between the VS copper and the CAN barrier.
  - Closing this needs room, which means a placement change (stage 4 work).
- **MAJOR (blocked, two-way): the scripts gate (T-0210) is still in force.** Decision 163 puts hand routing into
  `scripts/fixed_routes.py`, but the pcb-fixer gate admits only the board file and notes. So no fixed route could be
  added the way the brief asks. The T-0210 patch is still unapplied.
- **MINOR (method): parallel runs are identical.** All three b1 runs had the same board hash and score in every
  pass, so `-is` does not vary Freerouting 2.5.0 here. One run per input is enough; differences between stages come
  from input changes.
- **MINOR: J3 (4 items).** VBUS A4/A9/B4/B9 → F2.1 needs a fixed In2 route, because no via may sit in OUT1-B. Also
  D3-A and one GND island.

## Questions for the owner (one-way doors)

1. May the channel block get a signal corridor?
   - Notch VS-In2 as in b2: it stays whole, and it carries about 11 % of the load current.
   - Open a gap in the OUT3-F strip for a via row, with OUT3 joined on B.Cu.
   - Re-route the USB In2 run under U1.
2. Or should the four channel signal columns move out of the VS/OUT outlines, toward U1 (a placement stage)?
3. Or may the build put signal vias (not tracks) through VS-In2, with a higher pour-loss limit?
4. And, for the method itself: widen the pcb-fixer gate to `hardware/<board>/scripts/` (a `/system` change), so
   that fixed routes can be committed as decision 163 intends.

## Checks

- `kpcb drc` (board, unchanged): 0 errors, 425 warnings, 78 unconnected, parity 0. No bottom SMT, nothing in a
  hole keep-out, nothing parked.
- `python3 tools/fix_check.py --scope pdm-4ch`: **NOT READY**. Its only failure is "78 unconnected items left",
  the item this stage is blocked on.

- **Re-check after the orchestrator's return ("78 unconnected items left"):** this is the blocked item itself.
  Nothing within the stage rules can close it:
  - every further build of the same input gives the same result (b1);
  - fixed routes cannot be committed (scripts gate);
  - the corridor and floorplan changes that would open the west group change power copper (one-way door).
  The item stays blocked for the owner's ruling, and the board stays at the T-0210 build.

Safety: no copper changed. The corridor options touch VS copper on In2 between the PROFET tabs. Before any of them
lands, the pour check and a heat-budget recheck (decision 9) are needed. A competent person reviews the board before
installation, in particular the battery path, the VS copper and the outputs.

<!-- fix:begin -->
```json
{
  "done": [],
  "blocked": [
    {"id": "T-0211", "door": "one-way", "reason": "0 unconnected is not reachable under the stage rules: the west channel signals (27 items) are walled in by the VS-In2, VS spine/front/rear and OUT2/OUT3-F outlines (only the 0.65 mm via strip at x 46.15, used by USB), and the U1 strip/analog block (47 items) is congested; needs an owner ruling on a VS-In2/OUT3-F signal corridor, moving the channel signal columns, or signal vias through VS-In2 (design-notes 8.18)"},
    {"id": "T-0211-scripts", "door": "two-way", "reason": "the pcb-fixer merge gate still rejects hardware/pdm-4ch/scripts/ (T-0210 finding), so fixed routes cannot be added to fixed_routes.py as decision 163 requires; needs a /system gate change or a package scoped to scripts/"}
  ],
  "refs": [],
  "decisions": [
    {"area": "pdm-4ch", "text": "Routing build runs one Freerouting run per input: the three parallel runs of one build were identical (same hash and score each pass), -is does not vary Freerouting 2.5.0 here"},
    {"area": "pdm-4ch", "text": "Board left at the T-0210 build (0 errors, 78 unconnected): the T-0211 rebuild gave 79, and the VS-In2 corridor experiments stayed on scratch copies because they change power copper"}
  ],
  "checks": {"drc": "0 errors, 425 warnings, 78 unconnected", "parity": "0", "fix_check": "NOT READY (78 unconnected items left)"}
}
```
<!-- fix:end -->


## Rejected by the orchestrator

- 78 unconnected items left
