# Validation pdm-hc2, re-check of changes since d6cef248342f (T-0110, 2026-11-03)

Scope: `git diff d6cef248342f -- hardware lib docs/design-notes.md` for pdm-hc2. Changes found: T-0105 (switch loads
R3/R4/R7/R8 → 2 × 2 k), T-0106 (gate slew on `hc_channel` ×2), T-0107 (C30, C102, C202 → C170101). `lib/` unchanged.
Netlist of HEAD against d6cef24 (kicad-cli, scratch): only the refs those three items declare changed (R3/R4/R7/R8,
R45–R48, R104/R204, R115/R215, R116/R216, C114/C214, C30, C102, C202; U11/U12 pin 14 moved from GATE to PD).

## Findings

None. CRITICAL 0, MAJOR 0, MINOR 0.

## Checked and OK

- T-0106 pins: U11/U12 pin 15 PU → R104/R204, pin 14 PD → R116/R216 → GATE; matches the pin table in TPS4811-Q1 SLUSEE5E (part facts C17556513, PU 15, PD 14).
- T-0106 topology: PU → R1 (10 k) → gate, PD direct to the gate node (through 0 Ω), 10 Ω + 1 nF from gate to GND: as TPS4811-Q1 §8.3.2.1 / Fig. 8-6 (facts file, p. 19–20). Ramp from Eq. 3: 0.63 × 12 V / (10 k × 1 nF) = 0.76 V/µs, 40–57 µs for 30 V, as the notes say.
- T-0106 C114/C214: 1 nF/2 kV 1206 sees gate-to-GND ≤ VS + 12 V ≈ 60 V at the 48 V clamp, far below 2 kV. Charge for CBST (Eq. 4) 162 nC ≪ 1 µF. The overcurrent timer (CTMR 10 µF, tOC ≈ 146 ms) is far longer than the ≈ 50 µs inrush pulse, so only the fast ISCP trip matters; the notes check it (53 A against ≥ 71 A).
- T-0106 numbers are not recomputed (SOA re-digitising, bounding model); the notes state the open corner (turn-on into a short right after 15 A) openly, in STATUS and the failure-mode text. Heat budget unchanged (no conduction-loss change).
- T-0107: TPS4811-Q1 Table 9-3, PDF p. 39 (fetched from ti.com, read myself): "RVS, CVS … 100 Ω, 0.1–10 µF". 2.2 µF is inside the range; τ = 0.22 ms. Decision 26 allows 1–2.2 µF at J10 for C30. C170101 is 2.2 µF/100 V X7R 1206 (Samsung catalog p. 45, facts file); the same part as C1, so +0 parts and −1 unique on pdm-hc2 (no C13832 left in the HC2 schematics).
- T-0105: R3/R4/R7/R8 + R45–R48 are C17944 2 k 1206 (basic). Netlist: SWIN → R3 → mid-point → R45 → GND, while the 10 k series path still tees off SWIN, not the mid-point, so thresholds are unchanged. Power at 30 V: 30²/4 k = 0.225 W, 0.11 W per part (1206 0.25 W); in a 48 V clamp 0.29 W per part for a short time. Decision 74 matches.
- ERC pdm-hc2: 0 errors, 5 warnings (`lib_symbol_mismatch` Q3–Q6, J3), unchanged. Worktree has no other modified files.
- Docs: STATUS and design-notes §4a.1, §4a.3, §5, §8.1 agree with the schematic values (R104 10 k, R115 10 Ω, R116 0 Ω, C114 1 nF, C30/C102 2.2 µF).

## Not checked

- Anything not in the diff; footprints (no new footprints); SOA digitisation and the Zth cross-check in §4a.3 (a `/validate pdm-hc2 deep` item already listed in STATUS).
- Whether C1 returns to GND rather than SRC: the facts file marks the text as silent (figure shows a ground symbol); the notes argue it from the ramp physics. Prototype ramp measurement is already planned in STATUS.
- Stale ARCHITECTURE root row ("C30 1 µF/100 V") is already listed by the agent under "For /system".

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
