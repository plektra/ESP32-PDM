# Validation pdm-4ch, 2026-11-14 (T-0272, re-check of T-0271 against 5fba4c29136f)

Scope: `git diff 5fba4c29136f -- hardware lib docs/design-notes.md`. Changed: the PCB (routing only), `scripts/fixed_routes.py`, `STATUS.md`, design-notes §8.21. No schematic, symbol or footprint changed, so no part facts were re-checked.

## Findings

None.

## Checked and OK

- Change size: `fixed_routes.py` touches only the U12-DEN and U13-IN link routes, `DROP_NETS` and new `/DEN` stubs. No power copper, pour outline or part changed. This matches the item (Q-0073 two-way step; the one-way VS-In2 trim was not made, which is correct per §8.21 geometry).
- `kicad-cli pcb drc` on the board: 0 errors, 407 warnings (silk, 1 via_dangling, 2 holes_co_located, 1 lib mismatch), 45 unconnected. This equals the STATUS claim (46 → 45).
- Changed nets: no unconnected item involves Net-(U12-DEN) or Net-(U13-IN). The new routes close cleanly and there is no new dangling copper. The new `/DEN` via (72.50, 17.50) and the In2 run produce no clearance error, including the 0.23/0.24 mm gaps to IO40 and Q3-C. 0.23 mm is above the JLCPCB 0.1 mm minimum.
- The /DEN unconnected items are R202.1 to the ch4 stub and R302.1 to R202.1. The STATUS says these remain open (R302.1 boxed in). The U1.28 to R202.1 link is closed.
- Schematic parity: only "missing footprint FL30" (a DNP ferrite, not part of this change). Not a regression of the routing, but STATUS says "parity 0"; cosmetic.
- `python3 tools/heat_budget.py` runs; the 4 A row shows Tj 101 °C, which matches the STATUS claim. No power copper changed.
- Signal impact: /DEN and the U12/U13 IN links are low-speed 0.2 mm signal tracks. The route length change does not matter and the net identity is unchanged (DRC connectivity).

## Not checked

- Pour island counts and VS-In2 area and via count (taken from the fixer report; no power copper was edited).
- Gerber against the JLCPCB footprint; ERC and netlist (no schematic change).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
