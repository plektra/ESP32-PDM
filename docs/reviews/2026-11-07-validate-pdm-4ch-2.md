# Validation re-check pdm-4ch (T-0172) – 2026-11-07

Scope: changes since 2dfb50ad6655 (`git diff 2dfb50ad6655 -- hardware lib docs/design-notes.md`). The diff holds one file: `hardware/pdm-4ch/STATUS.md` (T-0171, J10 stock fallback). No schematic, PCB, library or design-notes change.

## Findings

None (0 CRITICAL, 0 MAJOR, 0 MINOR).

## Checked and OK

- No design file changed: `git diff` limited to hardware, lib and design-notes shows only STATUS.md text. Nothing to re-run for ERC, netlist or heat budget.
- Stock claim "C577772 stock 0, minimum order 18": confirmed live with jlc_get_part (stock 0, min_order 18, extended, 0.6461 USD at 1 piece).
- Rejected substitutes C577767 and C7422678: `docs/part-facts/C577767.md` and `C7422678.md` cite the maker drawings (KF2EDGSR rev. A 2023-05-12; DB3ERC rev. T0-1) as showing no flange or flange holes on the header. The C577772 facts show it has Ø3.2 flange holes. So the conclusion "no flange, ear screws unusable" follows from the sources. The pad grid (7.62 × 7.62) and hole (Ø1.5) are consistent in all three.
- The fallback "same part from another seller, check marking KF2EDGSRM" adds no part and no footprint, and it is no bigger than the item needed.
- Decision 119 (auto) matches STATUS; swapping to another socket is sent to the owner because it would amend decisions 98/104 (one-way door by policy item 2).
- J10 is owner-bought and hand-soldered (decision 85), so the statement that JLCPCB assembly does not wait for it holds.
- The sync-sweep note (pdm-hc2 J11 uses the same C577772, decision 102) matches decisions 98/102.

## Not checked

- Datasheet pages of the two rejected parts were not re-read; I relied on the cached facts files, which cite page 1 of each drawing. Because the outcome is "reject", an error would not harm the board.
- Whether the C577752 plug actually latches onto C577772 is UNVERIFIED in the facts files (C577772.md "Locking: UNVERIFIED"); this is already in the decision-98 sample check before layout, so I did not repeat it.
- Untouched circuits (by instruction).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
