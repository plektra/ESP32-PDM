# Cost re-check, scope system, 2026-11-04 (T-0145)

Basis: `git diff e5ea51408e53 -- hardware lib docs/design-notes.md`. Only the change since that commit is priced. Untouched circuits and earlier findings are not repeated.

## What changed
One part on pdm-4ch only (T-0143, owner ruling Q-0067): **D31 SMDJ40CA, LCSC C42371557**, VS to VBAT_FL across Q30. Nothing on pdm-hc2 or in `lib/`. The rest of the diff is text in design-notes §8.6 and STATUS.md.

Correct and complete: `sch_query.py pdm-4ch ref D31` shows pin 1 on VBAT_FL (Q30.2, U30.1/5, JP30, FL30, C32) and pin 2 on VS (Q30.3, C31, F1, F4 …). The symbol carries LCSC, footprint `D_SMC` (as D30) and a description. It is the only schematic edit, and no other part was added, removed or swapped. No bigger than the item needed.

## Figures
| Item | Value | Source, date |
|---|---|---|
| D31 C42371557, hongjiacheng SMDJ40CA, SMC | **preferred**, economic assembly, stock 10271 | `jlc_get_part`, 2026-11-04 |
| Unit price | 0.2231 USD @1, 0.1751 @50, 0.1545 @150, 0.129 @500, 0.1175 @3000 | same |
| Loading fee | **0** (preferred) | same |
| Unique parts pdm-4ch | 61 → 62 (+1, preferred) | STATUS.md T-0143 |
| Unique **extended** parts pdm-4ch | unchanged (D31 is preferred) | `jlc_search no_fee` |
| pdm-hc2 | unchanged | no diff |

Cost of the change (parts only, tier @1+ since each order is under 50 boards; placement fee per SMD part not looked up):
| Boards per order | D31 per board | D31 per order | Extended fee change |
|---|---|---|---|
| 5 | 0.22 | 1.12 | 0 |
| 10 | 0.22 | 2.23 | 0 |
| 30 | 0.22 | 6.69 | 0 |

Change since last report: +0.22 USD per pdm-4ch board and nothing else. Q30 + U30 + C32 remain about 5.4 USD plus two extended fees, as before. Full per-board totals are not repriced here (scope of this re-check).

## Levers
None found. D31 is the only TVS in the 40 V class and the only no_fee SMDJ40CA at SMC (`jlc_search`, library_type no_fee: 1 result). A cheaper like-for-like part was not found. SMCJ30CA (C19077607, 0.14 USD, D30) cannot take its place: its 30 V stand-off would conduct in normal use. Reusing the D30 part number to save a unique line is therefore not possible. A preferred part carries no loading fee, so the extra unique line costs only its price and one more placement.

## Rule findings
- Extended where basic/preferred fits: no. D31 is preferred.
- Non-standard value: SMDJ40CA is a standard TVS voltage.
- Stock: 10271, well above 500.
- Single source: one maker's SMDJ40CA is the no_fee option. This is acceptable for a standard TVS and does not repeat earlier reports.
- Footprint: KiCad `D_SMC` (pads 2.5 × 3.3 mm) differs from the JLCPCB land (3 × 3.8 mm). It is already on the STATUS pre-order checklist.

## Questions for the owner
None.

## Not checked
JLCPCB per-placement fee for D31, PCB cost, setup and stencil (unchanged by this change), the full BOM total and the electrical correctness of the circuit (validator's job, owner-accepted risk in Q-0067).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
