# Validation pdm-hc2, re-check since 1d30964d (T-0123) – 2026-11-03

Scope: `git diff 1d30964d8974 -- hardware lib docs/design-notes.md`. Items: T-0118 (F1–F4 → C70113, R54–R56 0.2 Ω C7420022) and T-0119 (C18 → C9196). `lib/` unchanged.

## Findings

None. CRITICAL 0, MAJOR 0, MINOR 0.

## Checked and OK

- T-0118 parts: C70113 facts (docs/part-facts/C70113.md, mSMD Series datasheet p. 1/3): 60 V, I_max 100 A, I_hold 0.50 A, Ri min 0.150 Ω, R1max 1.0 Ω, 1812. Matches the schematic values and the notes.
- T-0118 resistor: C7420022 facts (FJ-JS-3001-V1.0 p. 2, 5, 6): 0.2 Ω, 2 W at 70 °C, 2512, 5 s × 5 P overload; no ms pulse rating, and the owner accepted that in decision 81 (confirmed).
- Netlist (`sch_query ref`): F1.2 → R54 → D1.2/D2.2; F3.1 → R55 → D10.2/FB2.2 (F3.2 → J4.2); F4.2 → R56 → D55.2. F-pad nets F1-Pad2, F3-Pad1, F4-Pad2 carry only the PTC and its resistor, so each resistor sits between PTC and load as decision 81 says. F2 has no resistor, as ruled.
- Hard-short arithmetic: 30 V / (0.150 + 0.20) Ω = 86 A < 100 A. Normal-use drop 1.0 + 0.2 = 1.2 Ω, as in the notes.
- Notes §8.3 checks (a)–(c) recomputed: F4 path 1.2 Ω × 60 mA = 72 mV; L78M05 headroom ≈ 8.48 V against 7 V; buck input drop 0.22 V at 0.18 A. All pass. The R54–R56 losses are mW, so not rerunning `heat_budget.py` is acceptable (no output change).
- F2 moved to `Fuse_1812_4532Metric` and C70113, which is needed to remove C269104 from the BOM (unique extended parts ±0). The USB-only table in §8.3 states openly that the 4 V minimum is not met with either part at the 0.40 A peak, and that the result is the same in every corner. The change costs about 60 mV.
- T-0119: C18 = C9196 1 nF/2 kV 1206, footprint unchanged. The RC corner is 1/(2π × 1 MΩ × 1 nF) ≈ 159 Hz, as stated. Matches decision 83. No C107198 left in the schematics.
- ERC pdm-hc2: 0 errors, 5 warnings (`lib_symbol_mismatch` Q3–Q6, J3), unchanged.
- Leftover old part numbers appear only in historic STATUS entries (T-0104, marked as superseded by T-0118) and in part-facts and OWNER-INBOX history. No live reference.
- The safety text (failure mode: resistor fails open, F4 supplies the panel switches; competent-person review; mandatory 30 V hard-short test) is in design-notes, STATUS and the prototype test list.
- Size of change: three resistors and four PTC swaps, nothing beyond what decision 81 and decision 83 require.

## Not checked

- KiCad pads of `Fuse_1812_4532Metric` (pitch 4.275 mm, pads 1.125 mm) and `R_2512_6332Metric` against the datasheet land patterns (C70113: 1.78 × 3.2 mm pads, 3.2 mm gap; C7420022: a 4.0 / b 2.1 / L 4.1 mm, letters unmapped) and against the JLCPCB footprints. Both are already listed as pre-order checks in STATUS, so this is not a new finding.
- Pulse capability of C7420022 at ms scale (UNVERIFIED in the datasheet; accepted by the owner, prototype test mandatory).
- The pdm-4ch copies of the same sheets (out of scope).
- Cost figures and stock (taken from the notes).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
