# Validator report – pdm-4ch re-check (T-0138)

Date 2026-11-04. Scope: changes since commit e367037082bd (`git diff e367037082bd -- hardware lib docs/design-notes.md`).

## What changed

Only `hardware/pdm-4ch/STATUS.md` (T-0137: header date, one paragraph, the "Waiting for the owner" line). No schematic, symbol, footprint or design-notes change. T-0137 states it fitted no TVS across Q30 (blocked for the owner, stop iii). The commit also added seven `docs/part-facts/` files and a fix report; those are outside the diff scope but were used as evidence.

## Findings

None. CRITICAL 0, MAJOR 0, MINOR 0.

## Checked and OK

- Diff contains no `.kicad_sch`, `lib/` or design-notes change: `git diff e367037082bd --stat -- hardware lib docs/design-notes.md` shows STATUS.md only. So "no schematic change" in STATUS is true, and the change is no bigger than the item needed.
- STATUS numbers against the fix report (`2026-11-04-fix-pdm-4ch-T-0137.md`): SMDJ40CA VDS 59.4 V at 31 A, VS +3.1 V at 12 A, −4.0 V at 31 A; SMCJ30CA −15.1 V at 31 A and −8.0 V at 12 A. Recomputed: chord r = (64.5 − 49.1)/46.5 = 0.331 Ω, 49.1 + 0.331·31 = 59.4 V ✓; VS = VBR min − D30 clamp: 44.4 − 48.4 = −4.0 ✓; 33.3 − 48.4 = −15.1 ✓; 44.4 − 41.3 (D30 at 12 A, 36.8 + 0.374·12) = +3.1 ✓.
- SMDJ40CA facts (C42371557): VBR 44.4/49.1 V, VC 64.5 V at 46.5 A, p. 3 table of the datasheet (rev. 2.2, via pcbparts.dev copy) – read the row myself ✓.
- D30 on the schematic is SMCJ30CA C19077607 (`sch_query ref D30`), so the "already on the BOM" statement is right.
- STATUS blocked-state statement is consistent with the "Waiting for the owner" line and with decision 82 reference (C31 reverse rating). Design-notes §8.6 (b)/(c) unchanged, as STATUS says.

## Not checked

- Untouched circuits (per scope); the avalanche claim for Q30 (T-0129/T-0132) was already reported on earlier.
- Chord model for TVS clamp voltage at currents below Ipp is an extrapolation (the fix report says so; no maker gives VC at lower current). Not independently measurable here.
- SMCJ30CA/other TVS datasheets other than SMDJ40CA not re-read; no board change depends on them.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
