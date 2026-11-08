# Validate pdm-hc2 – re-check since a58f6c897a96 (T-0193)

Date: 2026-11-08 · Unattended · Scope: `git diff a58f6c897a96 -- hardware lib docs/design-notes.md`

Changes in scope: T-0190 (C3 on `power-usb`, C377773 → C170101) and T-0191 (R105/R205 on `hc_channel`, C26083 → C17927). No `lib/` change.

## Findings

None. CRITICAL 0, MAJOR 0, MINOR 0.

## Checked and OK

- Diff is limited to: C3 Value/Footprint/LCSC (`power-usb`), R105/R205 Footprint/LCSC (`hc_channel`), STATUS.md, design-notes §4a row and new §8.8. No net, symbol or other part edit.
- C3 = C170101 (`sch_query pdm-hc2 ref C3`): 2.2uF/100V, `C_1206_3216Metric`, nets +3V3/GND as before. Cached facts `docs/part-facts/C170101.md` (Samsung MLCC catalog Nov 2015, p. 45 row 48, p. 4 codes): 2.2 µF ±10 %, 100 V, X7R, 1206. Rating well above 3.3 V.
- C3 in U3 (LMR51610) output: C8 22 µF remains the main output capacitor; cited TI SLUSEY1B §8.2.2.5 gives no C_OUT maximum or ESR limit (`docs/part-facts/C22427220.md`, not re-read by me). Nominal value unchanged, so the swap is no larger than needed.
- R105/R205 = C17927 (`sch_query ref R105`): 1M, `R_1206_3216Metric`, pin 1 on VS, pin 2 on `/HC channel 1/EN` (same nets as before). Facts `docs/part-facts/C17927.md` (Uniroyal series sheet V.3): ±1 % (same as the 0402), 1/4 W, 200 V working voltage; at 24 V (48 V transient) VS the rating is above the old 0402. Value unchanged, so the UVLO ≈ 9.7 V / OV ≈ 34.5 V divider math and the 1 nF filter are unchanged.
- R13 on the board is already C17927 1M 1206, so the BOM unique count −1 for R105/R205 holds; likewise C170101 is already used for C1/C22/C30.
- Stale references: grep for C377773 / C26083 outside `docs/reviews`, `queue.json`, STATUS history and the §8.8 change note finds none in schematics or BOM-relevant text.
- STATUS.md, decisions 124/125 and design-notes agree with the schematic. The layout note ("1206 land needed", PCB not yet placed) is recorded.
- No output changed, so no heat-budget run is needed.

## Not checked

- ERC and netlist were not rerun by me; I relied on the fix reports (ERC 0 errors/5 warnings, only Footprint/LCSC differ) and on the diff, which touches no net.
- C170101 DC-bias capacitance at 3.3 V (no curve read); effect is nil for a secondary 2.2 µF beside C8.
- Samsung soft-termination suffix S vs base part CL31B225KCHNNN: electrical identity inferred (stated in the cached facts).
- C17927 1206 pad dimensions and power derating curve (not extracted in the facts file); R105/R205 dissipate far below 1 mW.
- Footprint/CPL checks at layout (no PCB placed).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
