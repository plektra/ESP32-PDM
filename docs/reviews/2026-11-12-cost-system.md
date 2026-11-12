# Cost re-check, scope system – 2026-11-12 (T-0238)

## Figures
Base 557048cfff29, `git diff -- hardware lib docs/design-notes.md`: pdm-4ch PCB (copper and one placement move),
`scripts/fixed_routes.py` (six In2 tracks for the J6 service bundle), STATUS.md and design-notes §8.18 (T-0236).
No schematic, no lib change. pdm-hc2 untouched.
- PCB part set compared before/after: 226 footprints, identical sorted Reference/Value/LCSC property set (md5 equal).
  No part added, removed or swapped. R60 only moved to (58.3, 41.4).
- Unique extended parts per board and loading fees: unchanged from the earlier reports (pdm-4ch and pdm-hc2 both
  unchanged). Parts cost, setup, stencil and extended fees: unchanged.
- PCB price: the T-0236 copper changes add no layer, via class or copper weight (0.2 mm tracks and the existing via
  sizes, per the fixed-route entries), so no bare-board price change is expected. Estimate, not re-quoted.

## Levers
None from this change set.

## Rule findings
None. Change is correct and no bigger than its item needed from a cost view: routing only, no BOM effect.

## Questions for the owner
None.

## Not checked
Everything untouched since 557048cfff29, as instructed. Routing correctness (DRC, 74 unconnected still open) is for the
validator. Quote-side fee items stay with the owner.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
