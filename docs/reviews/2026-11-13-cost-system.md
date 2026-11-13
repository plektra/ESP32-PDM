# Cost re-check, system – 2026-11-13 (T-0262)

Scope: `git diff 2a3ae19655ad -- hardware lib docs/design-notes.md`. Price the change only.

## Figures
- Changed files: `pdm-4ch` PCB, routing scripts (`fixed_routes.py`, `maze_route.py`, `routing_build.py`,
  `build_routing.sh`), `STATUS.md`, `design-notes.md` (T-0259: merge fix, ch1/ch4 signal-part move, 48 → 46
  unconnected). No schematic, no `lib/` change, nothing for `pdm-hc2`.
- Part set compared before/after (PCB footprints, 226 each, sorted References): identical. No part added, removed
  or swapped. R101/R102/R401/R402 turned 180°, R103/R107/R403/R407 turned 270°, a few moved by ≤ 0.3 mm.
- Unique extended parts per board: unchanged on both boards (before = after), so the loading fee per order is
  unchanged. Parts cost, JLCPCB setup and stencil: unchanged.
- PCB price: via classes are unchanged (0.6/0.3 mm 209 → 219, 0.8/0.4 mm 185 → 185), the smallest track is
  unchanged (0.15 mm, one segment; 0.2 mm 947 → 1014), and there is no new layer or copper weight. No bare-board
  price change is expected (estimate, not re-quoted). Only the pdm-4ch 0.3 mm drill count rose by 10.
- No part is swapped, so there is no cheaper equivalent to look for.

## Levers
None from this change set.

## Rule findings
None. The change is correct for cost purposes and no bigger than its item needed: routing and placement only,
no BOM effect.

## Questions for the owner
None.

## Not checked
Routing correctness (DRC, 46 unconnected, the one-way VS-In2 outline wall) is for the validator. Quote-side fee
items stay with the owner. Everything untouched since 2a3ae19655ad, as instructed.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
