# Validation pdm-4ch, re-check after T-0246 (T-0247), 2026-11-13

Scope: `git diff 8304312d902d -- hardware lib docs/design-notes.md`. Changed: `ESP32-PDM-4CH.kicad_pcb`, `scripts/*` (build_routing.sh, routing_build.py, fixed_routes.py), STATUS.md, design-notes §8.20. No schematic, symbol, footprint or library change, so part facts, circuit math and ERC are unchanged and not repeated.

## Findings

### MINOR
- **M1 – Dangling copper left by the maze pass.** `kpcb drc` shows 13 new `via_dangling` / `track_dangling` warnings (e.g. vias on +3V3, SW4_IO, IO5, IO6, IO7, IO11, IO17, IO18, SW1_IO, SW2_IO, VBAT_SENSE; 5.8 mm +3V3 track on B.Cu ending short of J6.8). Base commit had none. They are half-routes in the 52 open nets, not shorts (0 errors). Mechanism: none now; they become stubs if the board is ever released with them. Fix: the next pass either completes or removes them (`finish()` clean-up). Covered by the already-known open items; no extra work.
- **M2 – 0.2 mm signal tracks below the v3 class (known, flagged by the fixer).** +3V3 gets 160 mm of 0.2 mm copper. Branch currents are <0.1 A (clamp diodes, pull-ups), so there is no failure mechanism. Only +3V3 feeds to U1/U5/L1 must stay on the pour/0.3 mm; the diff shows no change to the locked 0.3–1.2 mm tracks (counts per width unchanged: 232×0.4, 55×0.6, 51×0.3, 12×0.5, 10×0.8, 8×0.25, 1×1.2). Fix: widen when the maze emits class width (already listed).

No CRITICAL or MAJOR finding. The board is intentionally unfinished (52 unconnected); that is stated honestly in STATUS.md, the fix report and §8.20 and is not a defect of the change.

## Checked and OK
- Reported numbers reproduced: `python3 tools/kpcb.py pdm-4ch drc` → 0 errors, 427 warnings, 52 unconnected, parity 0, no bottom SMT, no hole keep-out hit.
- Footprints 226 → 226, zones 40 → 40; no part, pour outline or hole moved by the diff (counts equal; only tracks/vias added: 940 → 1397 segments, 362 → 414 vias).
- All added segments are 0.2 mm; no power, output or 16 A copper added or changed (the width histogram of locked classes is identical). Added nets are signal nets (+3V3 branches, SW2, R3-Pad2, IO13/IO7/IO41/IO3, SW_SENSE, Q3/Q4/Q6 nodes, EN, U12/U14-IS, LED_K3, SW_SUPPLY). SW_SUPPLY 6.8 mm at 0.2 mm is the 10 k sense/divider side (R49 10 k, C54, TVS), not a current path.
- Heat budget rerun `heat_budget.py --ambient 40 --currents 4,4,4,4`: 1.40 W/ch, 8.92 W, enclosure 45.4 °C, Tj 101 °C – matches claim.
- Statement "VS-In2 1 island 1165.5 mm², 40/40 thermal vias inside" taken from build log (fix report, `thermal_check`); not re-measured here. It is ≥1012.1 and the change cost only 1.7 %.
- F2-Pad1/D3-A open items are the USB VBUS path of J3 (F2 = mSMD050-60V on USB), not a battery path.
- Scope discipline: change is no bigger than its item (scripts + signal copper); decision 176 amendment (Q-0072) is recorded as owner ruling in §8.20.
- Working tree clean after my runs (no *.kicad_prl change).

## Not checked
- Pour islands other than VS-In2 and the 3 GND "missing connection" items (known zone islands, stated open); clearance of the 0.2 mm copper against the JLCPCB capability beyond KiCad DRC (0 errors).
- Whether a 52-net open board can be handed on; routing completion is a later task.
- Schematic, libraries, ERC, netlist: unchanged since the base commit (diff empty).

<!-- findings:begin -->
```json
[
  {
    "id": "V1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "ESP32-PDM-4CH.kicad_pcb: dangling vias/tracks on +3V3, SW4_IO, IO5/6/7/11/17/18, SW1_IO, SW2_IO, VBAT_SENSE",
    "summary": "Maze pass 1 left 13 dangling vias/track stubs (none in base); no short, 0 DRC errors",
    "fix": "Complete or remove them in the next routing pass (finish() clean-up)",
    "door": "two-way",
    "reason": "signal copper only, a git revert or a rebuild undoes it (policy: layout)",
    "touches": [],
    "cost_delta_usd": 0.0
  },
  {
    "id": "V2",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "fixed_routes.py / maze_route.py: +3V3 branches 0.2 mm",
    "summary": "160 mm of +3V3 at 0.2 mm, below 0.3 mm v3 class; currents <0.1 A so no failure, known to the fixer",
    "fix": "Make maze_route.py emit the class width and widen in the next pass",
    "door": "two-way",
    "reason": "layout rule, reversible by rebuild",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
