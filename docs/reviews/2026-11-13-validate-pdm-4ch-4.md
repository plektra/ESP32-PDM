# Validation pdm-4ch, re-check 4 (T-0261)

Date: 2026-11-13. Scope: `git diff 2a3ae19655ad -- hardware lib docs/design-notes.md` for pdm-4ch. Change under test: T-0259
(maze_route merge fix, scripted move of R101/R102/R103/R107/R401/R402/R403/R407, two maze passes, 48 → 46 unconnected).
The diff touches only the PCB, STATUS.md, four scripts and design-notes; no schematic, no `lib/` file, no BOM part changed.

## Findings

### MINOR

**M1 – DEN via sits inside the pad R402.1 (ch4 DEN resistor, 0402).** Location: via (37.55, 24.25) `/DEN`, 0.6/0.3 mm,
pad R402.1 at (37.66, 24.53), 0.54 × 0.64 mm. Evidence: pad scan with KiCad Python on the board file. The via covers
most of the pad; the 0.3 mm drill is open (not plugged). Failure mechanism: solder wicks into the hole in reflow; a
starved 0402 joint or tombstone opens ch4's DEN link, so ch4 loses current sense and fault diagnosis. The output switching
is not affected. The fixer already noted this in STATUS.md and left it for "when DEN is touched again"; the board is the
frozen order state, so it should be fixed now. Cheapest fix: move this one via (and its two-segment stub) ≥ 0.5 mm off the
pad; no new part. Two-way door.

No CRITICAL or MAJOR findings.

## Checked and OK

- Scope of the diff: `git diff --stat` shows only the .kicad_pcb, STATUS.md, build_routing.sh, fixed_routes.py, maze_route.py,
  routing_build.py and design-notes. No schematic or library change, so pinouts, footprints, ratings and circuit math are
  untouched (nothing to re-verify).
- Footprint diff (KiCad Python, old vs new board): exactly 8 parts changed, R101/R102/R103/R107/R401/R402/R403/R407, all on
  F.Cu, same footprints; rotations 180° (0402) and 270° (1206), position shifts only R101 −0.2, R102 −0.07, R401 −0.2,
  R402 −0.07 mm in y. Matches design-notes and STATUS. No other part moved; no zone outline changed.
- Pad nets after the move: R101.2/R102.2 = U11 IN/DEN, R101.1 = SW_IN1, R102.1 = DEN, R103/R107 pad 1 = U11 IS, pad 2 = GND
  (same for ch4 with U14). IS shunt R103 ∥ R107 still to GND, so the current-sense scale is unchanged.
- `kicad-cli pcb drc --schematic-parity --severity-all` on the new board: 0 errors except 46 unconnected items (STATUS: 46);
  parity: 1 warning (FL30 DNP, no footprint, existing). No clearance, short, track_width or courtyard violations; the old
  board's track_width item (CANL_XCVR) is gone. Other warnings (silk, holes_co_located ×2, via_dangling /IO13 ×1,
  lib_footprint_mismatch U1) are identical in number to the old board.
- Unconnected, per net, old → new: DEN 4 → 3, MOD_ID 1 → 0; every other net unchanged (the GND-zone items at (100.95, 50.95)
  are the same three as before). No connection was lost.
- Track diff old/new on power nets: no VS, OUT or 16 A copper changed; GND: 5 tracks + 1 via removed, 4 tracks + 2 vias added,
  all on the R103/R107/R403/R407 IS-return links (0.4 mm, signal-level current); +3V3: 2 short 0.3 mm segments added.
  Heat: `python3 tools/heat_budget.py` (4 × BTT6050-1ERA, 40 °C): 4.0 A/ch → Tj 101 °C, as STATUS states.
- VS zones (KiCad Python): VS-In2 1 island, 1156.4 mm² (STATUS 1156.4, floor 1012.1); VS-F-drain, VS-B-spine, VS-B-front
  unchanged; VS-B-rear 153.8 → 152.7 mm² (−0.7 %, 1 island, within decision 178's 95 %). Old VS-In2 1165.0, so the −8.6 mm²
  claim is right.
- Decision 178 (In2 corridor): the only new In2 tracks inside VS-In2 are the DEN slot (35.9, 17.9)–(36.1, 20.9): 9.4 mm from the
  pour outline (≥ 1.5), 12.9 mm from the nearest VS via (≥ 1 mm beyond the thermal-via field). The other new In2 tracks (MOD_ID,
  IO0, IO7) lie outside VS-In2 (≥ 8 mm from it).
- Scripts: `move_parts()` is idempotent and removes only the six DROP_NETS nets and five listed GND segments; the removed
  items are exactly the old GND/IN/DEN/IS pieces on the 8 moved parts (track diff above). `build_routing.sh` `OK=${OK:--1}`
  makes a crashed build count as not kept. `maze_route.py` changes (own copper joined as source, re-seed on failure, node
  limit 6 M, one-net-per-line list) match the description; the 3 µm NTC clearance build was not kept, as written.
- Scope is no bigger than the item: nothing outside the ch1/ch4 pocket and the maze nets moved.
- design-notes T-0259 entry and STATUS agree with the board on every number I could measure (positions, 46 unconnected,
  1156.4 mm², Tj 101 °C).
- ERC (`sch_query erc`): only the existing lib_symbol_mismatch warnings; schematic unchanged.

## Not checked

- The "remaining wall" claim (SW_IN1/4, IO2, IO5, DEN cannot reach U1 without a VS-In2 or spine outline change): not
  re-derived. The fixer already routed it as a one-way door; not repeated here.
- Signal integrity/EMC of the 56-segment MOD_ID and 24-segment DEN maze copper (not a failure mechanism at DC/ADC rates).
- Gerber/JLCPCB footprint comparison (no footprint changed).

<!-- findings:begin -->
```json
[
  {
    "id": "M1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "PCB: DEN via (37.55, 24.25) inside pad R402.1",
    "summary": "Open 0.3 mm via sits inside the 0402 pad R402.1; solder wicks away, risking an open joint and loss of ch4 DEN/diagnosis",
    "fix": "Move that via and its stub at least 0.5 mm off the pad (copper-only change)",
    "door": "two-way",
    "reason": "copper-only move on a signal net before ordering; policy: layout copper changes are two-way",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
