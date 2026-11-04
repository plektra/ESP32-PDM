# EMC re-check, scope system (T-0146), 2026-11-04

Scope: `git diff e5ea51408e53 -- hardware lib docs/design-notes.md`. Only change in the schematic: **D31 SMDJ40CA
(C42371557)** across Q30 on the `pdm-4ch` root sheet (T-0143, owner ruling Q-0067). `lib` unchanged; STATUS and
design-notes §8.6 changed as text. `pdm-hc2` unchanged.

## Findings

None (0 CRITICAL, 0 MAJOR, 0 MINOR).

What was checked:
- **Correct:** netlist (`sch_query.py pdm-4ch ref D31`) shows D31 pin 1 on VBAT_FL (Q30 source, U30 pins 1/5, C32, JP30, FL30)
  and pin 2 on VS (Q30 drain, C31, C103–C404, U11–U14, F1, F4, R60). That is across Q30 as described. Bidirectional part, so the
  polarity of the symbol does not matter.
- **Invariant 4:** the surge path OUT → PROFET body diode → VS → Q30 → VBAT_IN → D30 is unchanged. D31 is not a TVS to GND and adds
  no path to the chassis or the battery negative other than through Q30's own loop. The invariant wording stays valid.
- **Immunity / RF:** at the VS node D31 conducts only above about 44 V across Q30, so it is no rectifier at VHF levels; in normal
  operation VDS is about 0 V. Its junction capacitance sits across a 1 mΩ switch and changes no filter corner.
- **Emissions:** no new switching edge, no clocked part. D31 conducts only in a fault, once.
- **Reverse battery:** D30 VBR max about 36.8 V is below D31's VBR min 44.4 V, so D31 stays off for a steady reversal, as design-notes §8.6 says.
- **Size of change:** one part, preferred, no loading fee, +0.22 USD. Nothing bigger than the item needed. The cheaper alternative
  (SMCJ30CA already on the BOM) was ruled out in T-0137 on the VS-negative figure.
- **Accepted residual risk (owner, Q-0067):** VS to about −4 V at 31 A, C31 without reverse rating. Not repeated; the prototype
  test is in STATUS.

## Layout rules

Last EMC report's rules still hold. One addition is already written (design-notes §8.6, STATUS): D31 directly across the Q30 drain
tab and source pins, short and wide, 8 × 8 mm copper per terminal. It must stay inside the VS loop of the switches → VS → Q30 → D30,
not on a stub. No other change.

## Installation guidance

No change from the last report.

## Not checked

- D31 KiCad footprint against JLCPCB footprint (STATUS lists it as open item T-0143).
- Whether negative transients on a real bus reach 31 A (UNVERIFIED, T-0130).
- Layout (no PCB).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
