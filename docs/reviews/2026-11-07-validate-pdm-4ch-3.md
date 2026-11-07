# Validation re-check pdm-4ch (T-0181) – 2026-11-07

Scope: changes since 1b667a36fb2f (`git diff 1b667a36fb2f -- hardware lib docs/design-notes.md`). Files changed: `hardware/pdm-4ch/STATUS.md` and `hardware/pdm-hc2/STATUS.md` (T-0179, documents only). No schematic, PCB, library or design-notes change, so ERC, netlist and heat budget were not re-run (nothing they read changed).

## Findings

None (0 CRITICAL, 0 MAJOR, 0 MINOR).

## Checked and OK

- No design file in the diff (git diff stat: two STATUS.md files only). The "no schematic, footprint or BOM change" claim holds.
- Buying rule (any seller, marking KF2EDGSRM-7.62, no C577767/C7422678, order waits) matches the owner rulings Q-0068/Q-0069 (`docs/OWNER-INBOX.md` lines 175-176) and decision 120 (confirmed). The change is no bigger than the ruling.
- Plug-mismatch warning matches the EMC report E21 (`docs/reviews/2026-11-07-emc-system-2.md`): battery plug in an HC2 J11 shorts the battery when channel 2 turns on; an HC2 load plug in J10 leaves the unit dead. The mechanism follows from the shared 7.62 mm set (decisions 102/104).
- Layout rule 2 reference (silkscreen "BATTERY"/polarity at J10, "OUT1 OUT2" at HC2 J11) exists in that report. README text (lines 65-68) agrees with the STATUS wording.
- The T-0171 sync-sweep note is replaced by "done in T-0179"; the pdm-hc2 STATUS carries the same rule.
- Old C577772 stock numbers (40/63 on 2026-11-05, 0/63 on 2026-11-07, MOQ 18) are unchanged and were confirmed live in the previous re-check.

## Not checked

- Live C577772 stock today; not part of this change.
- Untouched circuits (by instruction); pdm-hc2 STATUS wording beyond the sync-note it mirrors.
- Whether C577752 latches onto C577772 stays UNVERIFIED in the part facts; already assigned to the decision 98 sample check.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
