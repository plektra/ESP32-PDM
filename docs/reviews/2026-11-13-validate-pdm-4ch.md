# Validate pdm-4ch – re-check since 4de2c33 (T-0242), 2026-11-13

Scope: `git diff 4de2c33967a9 -- hardware lib docs/design-notes.md`. Change set: `STATUS.md`, design-notes §8.19, new
`scripts/T-0241-next-build.patch`, `scripts/geom_export.py`, `scripts/maze_route.py`. No `.kicad_sch`, `.kicad_pcb`,
`lib/` or footprint file changed (item T-0241 kept the board: 74 unconnected).

## Findings
None (0 CRITICAL, 0 MAJOR, 0 MINOR).

## Checked and OK
- No design file changed: `git diff --name-only` for hardware/lib lists only STATUS.md and scripts/ – so no part, pinout, footprint, net, or ERC change to re-verify.
- Patch `T-0241-next-build.patch` applies cleanly to main (`git apply --check`), so `routing_build.py`/`fixed_routes.py` on main still reproduce the board as STATUS says.
- `geom_export.py` and `maze_route.py` compile; they are not imported by the build (design-notes §8.19 claim holds).
- Constants in the patch match the notes: KEEPOUT_HOLE 0.25 = 0.2 mm smallest class clearance + 0.05; VS-In2 floor 85 % of 1190.7 = 1012.1 mm²; pin-pin 190 µm; corridor band 1.5 mm.
- Scope fits the item: only router-side (DSN copy) rules changed; no KiCad rule, zone, or F/B VS copper touched (one-way doors untouched).
- Heat: `tools/heat_budget.py` 4 A row gives Tj 101 °C at 40 °C, matching STATUS.

## Not checked
- Router quality claims (723→0 violations, 5 build results) – would need rerunning Freerouting builds.
- Untouched circuits and earlier findings (not repeated per brief).

## Finding block
<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
