# Validation – pdm-4ch – re-check since e5ea51408e53 (T-0144)

2026-11-04. Scope: `git diff e5ea51408e53 -- hardware lib docs/design-notes.md`. The only change is T-0143: D31 SMDJ40CA (C42371557) across Q30, with design-notes §8.6 and STATUS updated. `lib/` is unchanged.

## Findings

None (0 CRITICAL, 0 MAJOR, 0 MINOR).

## Checked and OK

- D31 in the schematic: `sch_query ref D31` shows pin 1 on `/VBAT_FL` (Q30.2, U30.1/.5, C32.2, JP30.1, FL30.1) and pin 2 on `VS` (Q30.3 drain, C31, F1, F4, R60, U11–U14). It is across Q30 as intended. The netlist change is D31 only: it adds D31.1 to `/VBAT_FL` and D31.2 to `VS`.
- ERC: 0 errors, 5 warnings (the same lib_symbol_mismatch notices as before).
- Part facts: `docs/part-facts/C42371557.md` (hongjiacheng SMDJ series rev. 2.2, p. 3) gives bidirectional, VRWM 40 V, VBR 44.4–49.1 V, VC 64.5 V at 46.5 A, IR 2 µA. The numbers match what the design-notes use. This is the cached file; I did not open the PDF myself.
- The part is bidirectional, so pin order does not matter. Absolute maximum: D31 sees at most about 60 V across Q30 plus leakage-level steady voltages, which is inside its 3 kW pulse rating. The pulse margin is recorded in §8.6.
- Circuit math rechecked from the facts file:
  - VDS at 31 A: 49.1 + 0.331 × 31 = 59.4 V.
  - VS floor: 44.4 − 36.8 − 0.374 × 31 = −4.0 V.
  - Current at VS = 0: 7.6 / 0.374 = 20.3 A.
  - Leakage into the R60 divider: 2 µA × 242 kΩ = 0.48 V.
  - Steady reversal: D30 clamps VBAT_IN at ≤ 36.8 V, below D31's VBR min of 44.4 V, so D31 does not conduct.
  - VS charged at the moment of reversal: VBR − 28 V gives +16 to +21 V, and VDS is about 57 V at most.
- Residual risk: C31 has no reverse rating. This is stated, accepted by the owner (decision 96, Q-0067) and put on the prototype test list. The other VS branches at −4 V are tabulated and agree with the netlist: D2/D55 block, D1 is bidirectional, U11–U14 −VS(REV) is 28 V, R60 is current-limited.
- Heat: `heat_budget.py --r-path 0.00505` gives 4 × 4 A Tj 102 °C at 45.5 °C inside, as stated. D31 dissipates nothing in steady state.
- Change size: one part (+0.22 USD, preferred, no loading fee, +1 unique). It uses the same footprint as D30. The docs changes are limited to D31, its failure modes and the layout rule.
- Decisions: decision 96 is confirmed, and the owner's ruling covers the change. Invariants 1–4 are untouched: the OUT → VS → Q30 → D30 surge path stays and nothing sits from VS to GND.
- Footprint: the pad difference between `D_SMC` and the maker's land is already on the pre-order checklist in STATUS. It is the same footprint as D30 and was reported in T-0143, so I do not repeat it as a finding.

## Not checked

- The SMDJ40CA PDF itself (cached facts only).
- Fig. 1 and Fig. 2 readings for the pulse margin.
- The real bus transient environment (T-0130, open).
- KiCad `D_SMC` against the JLCPCB footprint (pre-order checklist).
- ARCHITECTURE root row naming D31. STATUS already lists it under "For /system", so it is not a finding.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
