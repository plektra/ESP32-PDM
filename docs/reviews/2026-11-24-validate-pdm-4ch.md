# Validation pdm-4ch, re-check after decision 239 (2026-11-24)

Scope: `hardware/pdm-4ch` at commit 10b8fb1. Targeted re-check of what changed since the 2026-11-23 validation (b238c0a):
C10 moved to U5 VCC1, all non-CAN/USB signal copper rerouted, fab package rebuilt (decision 239). Nothing else changed in
the schematics (no `.kicad_sch` in the diff). Everything verified on 2026-11-23 and not touched since is not re-read; see
that report. No design file edited; work in scratch.

## Findings

### CRITICAL
None.

### MAJOR
None. (V1 of 2026-11-23 is fixed, see below.)

### MINOR
None.

## Checked and OK

- **V1 (U5 VCC1 bypass) fixed:** pcbnew read of the board. C10 at (166.25, 102.6) board coordinates, rotated -90, pad 2 (+3V3)
  1.47 mm from U5.1 (+3V3), pad 1 (GND) with its own GND via 0.72 mm away; U5.1 to pad 2 is on the logic side of U5 (x < 167.5, outside the
  can-barrier keep-out x 167.5-175.7). U5.4 GND is 5.3 mm from C10 pad 2 by distance, but both reach GND by vias to the GND layers (STATUS: U5.4 via 1.2 mm).
  Datasheet requirement (CA-IS305x v1.10 p. 5 Table 6-1, p. 18) is "0.1 uF as close as possible"; 1.5 mm is that.
- **Only C10 moved:** footprint position/rotation compared with b238c0a for all footprints: only C10 differs.
- **Power and fixed nets unchanged:** track/via sets identical to b238c0a for VS, +3V3 buck SW/CB/FB, CANH/CANL bus and XCVR, GND_CAN,
  USB_DP/DN, OUT1-4, VBAT_IN/FL, U30/Q30 gate nets, PROFET GND/IN/DEN/IS of U11/U12/U13/U14 partly (U11-U14 IN/DEN/GND nets). So the power path, the heat path and CAN
  routes of the earlier validations still apply. Signal nets (switch inputs, IS, LEDs, strap pins) are the re-routed ones.
- **ERC** (`kicad-cli sch erc --severity-all`): 5 `lib_symbol_mismatch` only (same as 2026-11-23).
- **Netlist export** runs (same "annotation errors" notice as before); schematics unchanged since the last validation, so nets are unchanged.
- **DRC** (`--schematic-parity --all-track-errors --severity-all`) on the new board: 0 errors, 0 unconnected pads, 4 warnings (3 silk clipped at edge, U1 library footprint note),
  1 parity item (`missing_footprint FL30`, intended). Same as STATUS states, so the whole new routing meets the clearance, annular and hole rules.
- **Rule 6 (no copper under U5 body):** no track, via or zone fill in the U5 body area between the pin rows on any layer. Only the SW4 In2 track and F.Cu via sit at x 167.05-167.25,
  i.e. at the pad inner ends, 0.3 mm west of the keep-out and 0.5 mm west of the body; logic-side copper that does not cross toward GND_CAN. The old board had the same SW4 pattern (+3V3 tracks too). Not a finding.
- **Heat budget:** `python3 tools/heat_budget.py --ambient 40 --currents 4,4,4,4`: 1.40 W/channel, 8.92 W, Tj 101 C. Unchanged (inputs checked 2026-11-18, p. 15).
- **CA-IS3050G pinout** (facts file `docs/part-facts/C528763.md`, datasheet p. 5 Fig. 6-1): 1 VCC1, 2 RXD, 3 TXD, 4 GND1, 5 GND2, 6 CANL, 7 CANH, 8 VCC2; the board's U5 pad nets match (1 +3V3, 2 IO18, 3 IO17, 4 GND, 5 GND_CAN, 6 CANL_XCVR, 7 CANH_XCVR, 8 VCC2). Recorded fact, page cited by the file; not re-read from the PDF in this run.
- **Work tree:** no `*.kicad_prl` or design file modified after the checks (git status clean).

## Not checked

- Whether the new copper of the re-routed signal nets is electrically sound beyond DRC (crosstalk, IS/ADC trace lengths, IO strap pins); the EMC reviewer has not re-run on it (STATUS says so).
- Gerber zip, CPL values and BOM re-derivation from the rebuilt package (CPL changed only in C10 according to the commit; not diffed here).
- Part facts, circuit math, invariants 1/4/9, firmware pin map: as in the 2026-11-23 report; no schematic change since.
- pdm-hc2 (shared `can` sheet C10 placement is a layout task when its layout starts).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
