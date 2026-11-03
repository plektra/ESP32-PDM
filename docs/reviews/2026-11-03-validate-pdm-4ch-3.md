# Validation pdm-4ch, re-check 3 (T-0109)

Scope: `git diff d6cef248342f -- hardware lib docs/design-notes.md`, pdm-4ch parts: T-0105 (R3/R4/R7/R8 -> 2 k + 2 k, new R45–R48), T-0107 (RIS -> 2 × 1 kΩ: R107/R207/R307/R407; C30 -> C170101). T-0104 and T-0108 changed documents only; the hc2 changes are out of scope.

## Findings

None.

## Checked and OK

- RIS: `sch_query ref R103/R107/R407`: both 1 kΩ C4410 (1206) have pin 1 on the same IS net (Net-(Un-IS), with C101 and R104) and pin 2 on GND. Parallel = 500 Ω. The new wire in channel.kicad_sch is only the pin-2 stub; nets match the claim.
- C4410 facts (UNI-ROYAL series datasheet SMD-SP-001 V.9, p. 4–5): 1206, 0.25 W, 1 %, 200 V. Basic part.
- Full-load IS: BTT6050 4.5 A at kILIS min 1380 gives 3.26 mA, 1.63 V; BTT6010 1.27 V. Both are below the 2.9 V ADC range and the 3.3 V clamp. I recomputed these from the design-notes figures; I did not open the BTT datasheets. The kILIS values come from the cited facts files.
- Fault cover: full scale at 5.8 mA (2.9 V) is under IIS(FAULT) min 6 mA, so DEN rule 2 still sees every fault. A 40 mA fault dissipates 0.4 W per resistor, against 1.1 W in one part before, so it improves. It is still firmware-covered, which the notes state.
- Switch loads: `sch_query ref R3/R45…R8/R48`: each pair is in series from SWINn to GND, so the load is 4.0 k. 30 V gives 7.5 mA and 0.11 W per part (44 % of 0.25 W). RCWV √(0.25 × 2000) = 22 V; 15 V per part at 30 V is fine. The 48 V clamp gives 0.29 W per part for µs–ms, inside the 5 s overload rating (2.5 × RCWV, 400 V limit). C17944 is a basic part, cited in its facts file.
- Divider thresholds: the load current rises by 0.4 mA, which the notes say stays within the 10.5 V margin (≤ 2 mV at IN). I did not recompute this because the change is small.
- Heat: `heat_budget.py --p-other 2.3` gives 4 A: Tj 101 °C, air 45.4 °C, as stated; 4.5 A is marginal. The 4 A rating stands.
- C30: C170101 2.2 µF/100 V X7R 1206 (Samsung catalog Nov 2015, PDF p. 45); it is the same part as C1, and decision 26 allows 1–2.2 µF at J10. Value, MPN, LCSC and Description in the schematic all agree.
- ERC: 0 errors, 5 warnings (BC817 ×4, J3), unchanged. The diff changes no other symbols: only the 4 values and LCSC codes plus 4 new resistors in analog_sw, and 4 values and codes plus 1 new resistor (instanced ×4) in channel.
- STATUS.md and the design-notes figures agree with the schematic. The owner questions (C104–C404 vs decision 26, C18 vs decision 31) are correctly left alone.

## Not checked

- BTT6050/BTT6010 kILIS from the maker datasheets (taken from the cached facts files).
- A fresh netlist diff against d6cef248342f (the nets were read through `sch_query`).
- The pdm-hc2 changes and the PTC question (T-0104), which is with the owner.

Note (not a finding): `heat_budget.py` default `--p-other` is still 2.2 W. STATUS lists the sync to 2.3 as a /system item, and the result does not change.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
