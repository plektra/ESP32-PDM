# Validation re-check – pdm-4ch (T-0079), 2026-11-03

Scope: changes since 5397e4099fa0 (`git diff 5397e4099fa0 -- hardware lib docs/design-notes.md`). Only T-0078 (U5 CA-IS3050G pin numbers 2/3) changed the design: `lib/ESP32-PDM.kicad_sym`, the `can.kicad_sch` lib_symbols cache (pdm-4ch, 4 lines), `docs/design-notes.md` §8.5, `STATUS.md`.

## Findings

None.

## Checked and OK

- Pinout: CA-IS305x datasheet v1.10 (pcbparts.dev mirror of LCSC C528763), Table 6-1, SOIC8 column: VCC1 1, RXD 2, TXD 3, GND1 4, GND2 5, CANL 6, CANH 7. I read the table myself. Symbol now matches.
- Change is minimal: only the two pin numbers swapped in lib and sheet cache; names, types and positions unchanged, so no wire moved.
- Netlist (`sch_query ref U5`): U5.3 TXD on /IO17 (U1.21, R70.2); U5.2 RXD on /IO18 (U1.22); pins 1, 4–8 unchanged. This matches ARCHITECTURE pin map (IO17 CAN TX, IO18 RX). R70 series resistor stays on TXD.
- ERC: 0 errors, 5 warnings (BC817 ×4, USB4145 J3 lib_symbol_mismatch); none on U5, so the lib and sheet copies agree.
- Docs: design-notes §8.5 Pinout row and Symbol bullet, and STATUS.md, are consistent with the datasheet and netlist. No `*.kicad_prl` or other design file changed.
- Part count and parts unchanged (no BOM, heat or cost effect).

## Not checked

- Untouched circuits (out of scope). The footprint land pattern remains as accepted earlier.
- No visual check of Fig. 6-1 pin-position text (the extracted figure text is ambiguous); Table 6-1 and the cached facts file p. 5 agree.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
