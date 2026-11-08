# Validation pdm-4ch – re-check since a58f6c897a96 (T-0192)

Date: 2026-11-08 · Scope: pdm-4ch, changes only (`git diff a58f6c897a96 -- hardware lib docs/design-notes.md`)

Changed: T-0190 / T-0187 – C3 on `power-usb` (+3V3 at L1 output) C377773 2.2 µF/50 V 0805 → C170101 2.2 µF/100 V X7R 1206. Documents: design-notes §8.8, STATUS.md. No lib change.

## Findings

None.

## Checked and OK

- Diff of `hardware/pdm-4ch/power-usb.kicad_sch`: only C3 Value, Footprint (C_1206_3216Metric) and LCSC changed; no net, symbol or position edit.
- `sch_query ref C3`: pin 1 on +3V3 (L1.2, C8, U1.3 …), pin 2 on GND – connection unchanged.
- C170101 facts (`docs/part-facts/C170101.md`, Samsung MLCC catalog Nov 2015 p. 45 row 48, p. 4 codes): 2.2 µF ±10 %, 100 V, X7R, 1206 3.2×1.6 mm, so the 1206 footprint matches and the voltage rating is far above 3.3 V.
- U3 output capacitor: design-notes §8.8 cites TI SLUSEY1B §8.2.2.5 (no C_OUT maximum, no ESR limit); same nominal value and ceramic class, C8 22 µF stays the main output capacitor.
- Change size: one component, no extra parts; part already on the BOM (C1, C30, channel caps), so unique parts −1.
- STATUS.md and design-notes §8.8 agree with the schematic; the "layout needs the 1206 land" note is recorded.

## Not checked

- Effective capacitance of C170101 at 3.3 V bias (no curve read; the note says qualitative). The part is only a secondary 2.2 µF beside C8 (22 µF), so loop impact is nil by the datasheet statement.
- Samsung soft-termination suffix S: electrical identity with the catalog's base part is inferred (cached facts note this).
- ERC and netlist were not rerun; the fix report states ERC 0 errors/5 warnings and nets unchanged, and the diff shows no net-affecting edit.
- Footprint/CPL rotation at layout (no PCB placed).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
