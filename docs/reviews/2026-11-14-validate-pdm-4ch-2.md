# Validation pdm-4ch, re-check since e85bc36a6273 (T-0277), 2026-11-14

Scope: `git diff e85bc36a6273 -- hardware lib docs/design-notes.md`. Changed: `ESP32-PDM-4CH.kicad_pcb`, `scripts/fixed_routes.py`,
`maze_route.py`, `routing_build.py`, `STATUS.md`, design-notes §8.22 (T-0276). No schematic, symbol, footprint or part changed.

## Findings

None.

## Checked and OK

- Change size: the diff adds the marked In2 exit (window x 55–57, y 6.45–20, only for five named nets), a 0.9 × 1.6 mm notch in VS-In2, the /DEN column and ch3 link swap, and a /SW4 join. No 16 A path, no other pour outline. It matches Q-0075/Q-0073 as written in §8.22.
- `kicad-cli pcb drc`: 0 violations, schematic parity 0, 42 unconnected. This equals the STATUS claim (45 → 42).
- Unconnected items: no /DEN item remains (DEN 2 → 0). The 3 GND items are at (100.95, 50.95), a spot outside the changed area. The earlier GND-3 count in STATUS is the same.
- Moved C301.2 GND via (56.78, 25.30): `DROP_GND_VIAS` removes the old via and no GND connectivity error appears, so the new via is connected.
- New copper (R302.1 → via (57.45, 25.95) → B x 56.36 → column via (56.45, 15.70)) passes DRC clearance at the stated 0.24–0.27 mm gaps. These are signal copper (DEN) next to 24 V nets; 0.24 mm is well above the JLCPCB minimum and the board's 0.2 mm rule.
- `maze_route.py` via-mask change is stricter (zone clearance + via radius + margin), not a relaxation. The exit window is limited to `EXIT_NETS`; other nets keep the 1.5 mm band.
- `routing_build.py` notch function is idempotent and asserts the outline stays in one piece.
- Heat budget: no power copper changed; heat_budget.py output unchanged (Tj 101 °C at 4 × 4 A, 40 °C).

## Not checked

- VS-In2 area (1133.4 mm²), island counts and 40/40 thermal vias: taken from the fixer report and STATUS; the DRC shows no connectivity loss on VS.
- Comment in `fixed_routes.py` describes a notch of y 14.9–18.5 for three vias; the constant is y 14.9–16.5 for the one via placed. Comment only, no board effect, not a finding.
- Gerber against the JLCPCB footprint; ERC and netlist (no schematic change).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
