# Validation pdm-4ch, re-check since 0c3b88089578 (T-0215)

Date 2026-11-11. Scope: `git diff 0c3b88089578 -- hardware lib docs/design-notes.md`.

## Changed since the last review
Only `hardware/pdm-4ch/STATUS.md`, `scripts/build_routing.sh` and `scripts/fixed_routes.py` (T-0214). No schematic,
board, lib or design-notes change, so part facts, circuit math, heat budget and netlist are unchanged.

## Findings
None.

## Checked and OK
- `fixed_routes.py`: 34 `T()` and 16 `V()` entries, as STATUS.md says. Net names and layers match the T-0210 routes.
- Claim "board already matches the script": `routing_build.py prep` run on a scratch copy of the board gives
  "locked copper kept, fixed routes added 0". Every script item is already locked copper. The board file is unchanged.
- `build_routing.sh`: `LAND_BEST=1` adds one condition to the replace test. Without it, behaviour is as before. It is
  documented in the header and no bigger than the item needed.
- STATUS.md update is consistent with the diff; "held back" is closed.

## Not checked
- A full `build_routing.sh` run (not needed for a script-only change; fix report also did not run it).
- Untouched circuits (earlier reports).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
