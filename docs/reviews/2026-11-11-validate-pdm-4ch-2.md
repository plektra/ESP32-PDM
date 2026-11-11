# Validate pdm-4ch, re-check since 95b6c7b (T-0222), 2026-11-11

Scope: `git diff 95b6c7b337f0 -- hardware lib docs/design-notes.md`. Changed files: `hardware/pdm-4ch/STATUS.md`,
`scripts/build_routing.sh`, `scripts/fixed_routes.py`. No board, schematic, lib or design-notes change.

## Findings
None.

## Checked and OK
- `fixed_routes.py` is only the T-0210 CAN/USB/CC1 copper written as data (34 track entries = 85 segments, 16 vias). I
  parsed the board file independently and compared them at the board origin (99.95, 49.95; edge box incl. line width):
  all 85 segments and 16 vias exist, locked, with the same net, layer, width and via size/drill. So the script adds
  nothing the board does not already have, and `git diff --stat` shows the .kicad_pcb unchanged.
- The 0.15 mm neck on CANL_XCVR (85.8, 56.6–57.6) is the one non-0.2 width; it is on the board with that width and is
  commented with its reason.
- `build_routing.sh`: `LAND_BEST=1` adds one OR condition to the replace test; default behaviour unchanged;
  documented in the header; no bigger than the item needed.
- STATUS.md text matches the diff (34 entries, 16 vias, 0 added by `add_fixed`; "held back" closed).
- `sch_query erc`: only lib_symbol_mismatch warnings (BC817, USB4145 copy), no schematic change since the last report.

## Not checked
- A full `build_routing.sh` run with `LAND_BEST=1` (not needed for a script-only change).
- Untouched circuits (earlier reports).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
