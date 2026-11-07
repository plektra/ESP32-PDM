# Validation re-check pdm-hc2 (T-0182), 2026-11-07

Scope: `git diff 1b667a36fb2f -- hardware lib docs/design-notes.md`. Changed files: `docs/design-notes.md` (one sentence in §4a.3), `hardware/pdm-hc2/STATUS.md`, `hardware/pdm-4ch/STATUS.md`. No schematic, footprint, symbol, BOM or `lib/` change, so no netlist/ERC/heat-budget rerun is needed.

## Findings

None.

## Checked and OK

- T-0180 turn-off edge text (design-notes §4a.3, STATUS scan item): "about 10.5 nF" and R(PD) 0.69–1.34 Ω give τ = 7–14 ns, which makes ~500 V/µs a fair order-of-magnitude estimate. The text says it is an estimate, not simulated. The "230 ns at 22 Ω" is 22 Ω × 10.5 nF = 231 ns. Not verified against the datasheet figures here (those were not changed).
- T-0180 scope: documents only; R116/R216 stay 0 Ω C17168. The text says keeping a trial value amends decision 25 and goes to the owner, which is the right door.
- T-0180 layout note ("R116/R216 close to U11/U12 pin 14, with pads a hand-swap can reach") adds no part and is no bigger than the item needed.
- T-0179/T-0177 plug warning, checked in the netlist (`sch_query pdm-hc2 ref J11`): J11 has two pins, OUT1 and OUT2, and no GND pin. A battery plug there puts battery − on one output, so that channel's MOSFET (Q22 for OUT2) turning on shorts the battery. The STATUS statement is consistent. `pdm-4ch` J10 pin 1 is VBAT_IN, pin 2 is GND, and both boards use C577772. Silkscreen rule 2 exists in `docs/reviews/2026-11-07-emc-system-2.md`, line 88.
- The buying rule (C577772 from any seller, marking KF2EDGSRM-7.62, no C577767/C7422678, the order waits) is the same in both STATUS files and says "no design change". The 4-ch sync-sweep note was closed.

## Not checked

- The reasons the substitute sockets failed (no flange, no latch) rest on `docs/part-facts/C577767.md` and `C7422678.md`, which I did not re-read. They are unchanged since the earlier report.
- Seller marking of C577772 outside LCSC cannot be verified from here.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
