# Validation re-check pdm-4ch (T-0237), 2026-11-12

Scope: changes since 557048cfff29 in `hardware`, `lib`, `docs/design-notes.md` (T-0236 routing stage).

## Findings
None.

## Checked and OK
- Diff content: only `ESP32-PDM-4CH.kicad_pcb`, `STATUS.md`, `scripts/fixed_routes.py` and `docs/design-notes.md` §8.18 changed. No schematic, symbol or footprint changed (`git diff --stat` on `*.kicad_sch` and `lib` is empty), so part facts, circuit math and netlist are unchanged.
- PCB DRC (`kicad-cli pcb drc`, errors): 0 violations, schematic parity 0, 74 unconnected (old board 78 by the same command). Matches the T-0236 report and STATUS.
- R60 (220k, VS -> VBAT_SENSE) moved to (58.3, 41.4): schematic nets unchanged (`sch_query ref R60`: pin 1 VS, pin 2 VBAT_SENSE). The VS pad now lies in VS-F-drain; DRC clean. Failure mode (R60 short puts VS on the ADC divider) is the same as before the move; no new exposure. VBAT_SENSE stays one of the open ratsnest items (open in the old board too, 4 items before and after), so not a regression.
- J6 bundle (TXD0/RXD0/IO35-37/IO42, DNP service pads) rerouted as nested L shapes on In2 over the In1 GND plane: 3.3 V signals only, 0 DRC errors, no pour split reported. Change is limited to those six nets and the 12 old segments they replace.
- `fixed_routes.py` adds only the J6 loop (9 lines); builds 3 and 4 (VBUS, bundle v2) were not kept, and the scripts match the kept board.
- Heat budget: the T-0236 note states Tj 101 C at 40 C, 4 x 4 A; no output, thermal via or power outline changed, VS-In2 loss 0.4 % against a 5 % limit (decision 172). Not rerun (inputs unchanged).
- Segment count rose 881 -> 940, consistent with a fresh route build; no power-zone outline change stated and DRC clean.

## Not checked
- Untouched circuits (out of scope), ERC/netlist (no schematic change).
- Whether the board is routable to completion: 74 nets still open, work in progress (T-0218 blocked, two-way).
- Pour area numbers (VS-In2 1185 / 1190.7 mm2) taken from the T-0236 report, not recomputed.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
