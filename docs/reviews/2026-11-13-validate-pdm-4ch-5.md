# Validation pdm-4ch, re-check since 0599ea8 (T-0267), 2026-11-13

Scope: `git diff 0599ea829088 -- hardware lib docs/design-notes.md`. Changed: T-0266 (ch4 DEN via moved off pad R402.1),
`fixed_routes.py`, STATUS.md, design-notes.md. No schematic, library or footprint change. The PCB diff is otherwise
only UUID and segment re-ordering from the rebuild.

## Findings

None. (Earlier MINOR M1, the DEN via inside R402.1, is resolved.)

## Checked and OK

- The old DEN via (37.60/24.30, board-local) and its stub are gone. `/DEN` vias in the PCB: (138.55, 75.37) new, plus the unchanged ones. The new via has an F.Cu 45° link to R402.1 and the B.Cu stub ends at it (PCB segments, `fixed_routes.py` lines 1345+).
- DRC (`kicad-cli pcb drc`, new vs. the 0599ea8 board): 0 errors and the same 46 unconnected pads. The warning classes are the same (via_dangling /IO13, 2 holes_co_located on +3V3, silk). Total 407 vs 417: the difference is the 9 library-config warnings, which come from running the old file in scratch. The DEN pads left unconnected are R202.1 and R302.1 (ch2/ch3, listed as boxed-in in STATUS), not ch4.
- Via-to-pad distance: 0.97 mm centre to R401.1 and 1.26 mm to R402.1, so the 0.6 mm via has a gap of about 0.35 mm to the pads. DRC clean, and the via is not on any pad.
- Change size: only `/DEN` copper plus `/DEN` in `DROP_NETS`. The ch4 DEN signal is low-speed, so the longer stub has no effect. No power copper or part changed. The STATUS claims (pours, 40/40 thermal vias) are not re-derived, see below.

## Not checked

- Pour island counts and VS-In2 area/thermal via count after the move (taken from the fixer report; heat budget unchanged since no power copper changed).
- Gerber against the JLCPCB footprint.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
