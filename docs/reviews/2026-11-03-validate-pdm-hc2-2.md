# Validation pdm-hc2, re-check of changes since 5397e4099fa0 (T-0080, 2026-11-03)

Scope: `git diff 5397e4099fa0 -- hardware lib docs/design-notes.md`. Only one change exists: T-0078 / T-0076, U5 CA-IS3050G
TXD/RXD pin numbers (shared `lib/ESP32-PDM.kicad_sym` and `hardware/pdm-hc2/can.kicad_sch`, plus design-notes §8.5 and STATUS).

## Findings

None. CRITICAL 0, MAJOR 0, MINOR 0.

## Checked and OK

- Pin numbers: Chipanalog CA-IS305x v1.10, p. 5, Fig. 6-1 (rendered) and Table 6-1: SOIC8-WB 1 VCC1, 2 RXD, 3 TXD, 4 GND1,
  5 GND2, 6 CANL, 7 CANH, 8 VCC2. The symbol `CA-IS3050G` now matches (lib lines 2049–2185: TXD "3" input, RXD "2" output;
  other pins unchanged). Source PDF fetched through pcbparts.dev (C528763), not just the cached facts file.
- The CA-IS3052G has 2/3 the other way round (p. 6, Table 6-2); the part on the BOM is C528763 = CA-IS3050G (jlc_get_part), so the right column was used.
- Change is minimal: 4 lines in the lib, 4 lines in the embedded `lib_symbol` of `can.kicad_sch`, pin positions untouched, no wire moved, no part change.
  The embedded copy equals the lib symbol (ERC shows no `lib_symbol_mismatch` on U5).
- Netlist of pdm-hc2 HEAD (`tools/sch_query.py ref U5`): U5.3 TXD = /IO17 (U1.21, R70.2); U5.2 RXD = /IO18 (U1.22); 1 = +3V3; 6 CANL, 7 CANH
  via FL1; 5 = GND_CAN; 8 = VCC2 net. R70 pull-up stays on TXD, which is the intended side (weak internal TXD pull-up per part-facts p. 15).
- ERC pdm-hc2: 0 errors, 5 `lib_symbol_mismatch` (Q3–Q6, J3), unchanged from before.
- Docs: design-notes §8.5 pinout row and the dated Symbol line agree with the datasheet; STATUS entry matches the diff. Worktree has no other modified files.

## Not checked

- Anything not in the diff (other circuits, footprints, heat budget; no output changed).
- Bring-up CAN loopback test on hardware (already planned in the fix report).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
