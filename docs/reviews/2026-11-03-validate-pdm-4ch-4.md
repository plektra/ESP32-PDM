# Validation pdm-4ch, re-check since 1d30964d (T-0122) – 2026-11-03

Scope: `git diff 1d30964d8974 -- hardware lib docs/design-notes.md`, pdm-4ch only. Items on this board: T-0118 (F1–F4, R54–R56; shared, already re-checked in `2026-11-03-validate-pdm-hc2-4.md`, not repeated), T-0119 (C18, same), T-0120 (C104–C404 → C170101), T-0121 (reverse-battery blocker Q30/U30/C32, new symbols in `lib/`).

## Findings

None. CRITICAL 0, MAJOR 0, MINOR 0.

## Checked and OK

- Netlist old (1d30964) vs new, `kicad-cli sch export netlist` on the pdm-4ch root: the only component differences are Q30/U30/C32 (new), R54–R56 (new), F1–F4, C18, C104–C404 (values). Pin differences besides those: FL30.1/JP30.1 move from VS to `VBAT_FL`, and the F1/F3/F4 pad nets that now carry R54–R56. Nothing else changed.
- U30 pinout in the symbol (EN 1, GND 2, N.C 3, VCAP 4, SOURCE 5, GATE 6, N.C 7/8) and the TSOT-23-8 footprint order match LM74500-Q1 SNOSDB7 p. 3 (via `docs/part-facts/C5219210.md`).
- U30 wiring: SOURCE and EN both on VBAT_FL (always on, datasheet p. 3/11), GATE → Q30.1 direct (as in all TI circuits, Fig. 9-4 p. 16), VCAP → C32 → VBAT_FL, GND → GND. Orientation matches Fig. 9-4: SOURCE on the battery side, Q30 source to the battery, drain to the load (VS).
- U30 ratings against 30/48 V: SOURCE abs max ±65 V (recommended ±60 V) vs 48.4 V D30 clamp; GATE–SOURCE 15 V abs max, charge pump regulates to 13.9 V max, Q30 VGS ±20 V (IPT007N06N Rev 2.1 p. 4) – no zener needed. EN abs max follows SOURCE.
- Q30 pins: symbol G 1 / S 2 / D 3 against the Infineon datasheet pin 1 gate, 2–8 source, tab drain (p. 2, 11); stock KiCad `Infineon_PG-HSOF-8-1` has pads 1 (G), 2 (S, merged), 3 (tab D); pad edges lie outside the package outline H 11.48–11.88. VDS 60 V ≥ 48.4 V clamp; 0.75 mΩ max at 10 V.
- Reverse-battery behaviour: Q30 body diode (anode source) is reverse-biased with VBAT_FL negative; VS floats up to about GND via the loads' output body diodes, so C31 sees no reverse voltage and Q30 blocks ≤ about 48 V. Forward direction: Q30 is on in both directions, so OUT → VS → Q30 → D30 (invariant 4) stays, and U30 keeps itself powered from the VS side while a surge is present.
- Nothing but J10, D30, C30, FL30/JP30 sits on VBAT_IN; everything else is behind Q30.
- C32 C15849: 1 µF/50 V X5R 0603, basic (`jlc_get_part`), ≥ 10 × Ciss max 21.3 nF = 213 nF even with a heavy DC-bias loss at 12–14 V.
- Heat: `tools/heat_budget.py --r-path 0.00505` reproduces 4 × 4 A Tj 101 °C (≈ +1 K with Q30 in the path as stated; 4.5 A still marginal). Q30 at 40 A: 1600 A² × 1.1 mΩ ≈ 1.8 W; × 40 K/W + 51 °C air ≈ 122 °C, matches §8.6. The ≥ 6 cm² 2 oz rule on the VS tab is recorded in STATUS and as decision 90.
- Turn-on: body diode carries the inrush and any load current for 22–40 ms until the gate is on (75 µs + 1 µF × 6.5 V / 300 µA); the diode IS 300 A / ISM 1200 A makes this harmless, as written in §8.6.
- T-0120: C104–C404 now C170101 2.2 µF/100 V 1206, same footprint, matches the amended decision 26; no C13832 remains in the netlist.
- ERC pdm-4ch: 0 errors, 5 warnings (`lib_symbol_mismatch` Q3–Q6, J3), unchanged.
- Size of change: three parts (+2 unique extended), nothing beyond the ruling Q-0054; failure modes and the competent-person review are in §8.6 and STATUS.

## Not checked

- Land patterns of `Infineon_PG-HSOF-8-1` and `TSOT-23-8` against the JLCPCB footprints of C122552/C5219210 (Infineon datasheet has no land pattern; already a pre-order item in STATUS).
- U30 reverse SOURCE current, body-diode drop at load current during the 22–40 ms turn-on, C32 DC-bias curve (UVERIFIED in the facts files; consequences small).
- Shared T-0118/T-0119 changes (covered by the pdm-hc2 re-check of the identical sheets).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
