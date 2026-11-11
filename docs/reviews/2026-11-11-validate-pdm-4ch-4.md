# Validation re-check pdm-4ch (T-0232), 2026-11-11

Scope: changes since 16a7b88575e8 in `hardware`, `lib`, `docs/design-notes.md`.

## Findings
None.

## Checked and OK
- `git diff 16a7b88575e8 -- hardware lib docs/design-notes.md` touches only two build scripts (`hardware/pdm-4ch/scripts/fixed_routes.py`, `routing_build.py`). No schematic, PCB, symbol or footprint changed, so part facts, circuit math, heat budget and netlist are unchanged. The placement stage in decision 172 was not implemented (T-0231 moved nothing, so no heat-budget recheck is due).
- `POUR_LOSS_MAX` 0.02 -> 0.05 (`fixed_routes.py:30`) matches decision 172 ("every power pour keeps >= 95 % of its baseline area"). The island test (`routing_build.py:301`, no more islands than baseline) is unchanged, which covers "one island".
- `VIA_OK_POURS = {'VS-In2'}` (`routing_build.py:43,191`) clears `DoNotAllowVias` only on the `pour-VS-In2` keep-out; tracks stay barred. Every other pour keeps its track+via keep-out (decision 164). That matches decision 172 and is no wider than needed. The T-0231 note reports 1 wire_keepout against 248 full keep-outs in the DSN (not re-run).
- Decision 172 is confirmed and cites Q-0070 (owner ruling in `docs/OWNER-INBOX.md:173`).

## Not checked
- Untouched circuits (out of scope).
- The routed board result: T-0231 produced no board change (0 fixed), so no new DRC run was needed.
- `STATUS.md:59` still says "<= 2 % area change". That is correct for the current board and becomes stale only after a board is built with the 5 % gate. Not a finding.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
