# Validator re-check pdm-4ch, 2026-11-04 (T-0133)

Scope: `git diff 916e5cda788e -- hardware lib docs/design-notes.md`. Changed: `docs/design-notes.md` (new paragraph in §8.6, "Cheaper Q30 checked and dropped") and `hardware/pdm-4ch/STATUS.md` (T-0132 entry). No schematic, symbol, footprint or BOM change (`git diff` shows no `.kicad_*` or `lib/` file), so ERC and netlist are unchanged by construction.

## Findings

None.

## Checked and OK

- No design file changed: the diff contains only the two Markdown files; the AGM601LL was not fitted and `grep` finds no C5464765 in `hardware/` or `lib/`. The change is no bigger than its item needed.
- AGM601LL facts (60 V, VGS ±20 V, EAS 1225 mJ, Tj 175 °C, RDS(on) 1.25 typ / 1.6 max at 10 V 30 A, RthJA 50 with no copper area stated, pinout 1 G / 2–8 S / tab D): match `docs/part-facts/C5464765.md` (datasheet VER2.65, pp. 1–3). The cached file is a pointer written by an agent; I did not re-read the PDF because the decision (drop the part) does not depend on a figure that could flip it: even the typical value at 25 °C gives about 132 °C at 40 A.
- Table in §8.6 recomputed by hand: AGM601LL at 16 A: 1.6 mΩ × 1.25 (Fig. 6 at 66 °C) gives 0.51 W, ×40 K/W + 45.7 °C = 66 °C; at 24 A: 1.6 × 1.48 = 2.37 mΩ, 1.36 W, +46.6 → 101 °C; 50 K/W column 72 °C at 16 A; 40 A: 5 W+ at 175 °C against 40 K/W is runaway. IPT007N06N at 40 A: ≈1.12 mΩ hot (`docs/part-facts/C122552.md`, Diagram 9) → 1.8 W × 40 + 52.5 = 124 °C. All agree with the stated values.
- `tools/heat_budget.py` (4 × BTT6050, 40 °C): 4 A per channel Tj 102 °C, 4.5 A OVER – matches the note's "4 × 4 A 102 °C (4.5 A now OVER)".
- STATUS.md figure 122 °C (T-0121, `--r-path 0.00505`) versus 124 °C in the new table (`--r-path 0.0069`, the AGM path used as a common method check): consistent, difference is the path resistance only.
- STATUS.md points to `docs/reviews/2026-11-03-fix-pdm-4ch-T-0132.md`, which exists.

## Not checked

- AGM601LL datasheet PDF not re-read (see above); Fig. 6 values are the agent's read-off from a plot (±0.03).
- T-0129 avalanche claim (Q30 at 60–63 V, 80–115 mJ, ≈1–2× margin on Diagram 13) is recorded as blocked for the owner and is a documentation statement only; design-notes §8.6 (b) is deliberately unchanged, so the known "VDS ≤ 48.4 V" text still stands until the owner rules. Not repeated here.
- Untouched circuits (per scope).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
