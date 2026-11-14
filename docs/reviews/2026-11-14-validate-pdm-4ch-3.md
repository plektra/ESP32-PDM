# Validation pdm-4ch, re-check after T-0281 (2026-11-14, unattended, T-0282)

Scope: `git diff dfe3e43d8d38 -- hardware lib docs/design-notes.md`. Changed: `ESP32-PDM-4CH.kicad_pcb`, `scripts/fixed_routes.py`,
`scripts/routing_build.py`, new `scripts/gnd_weak_q0076.json`, `STATUS.md`, design-notes §8.23 (T-0281). No schematic, symbol,
footprint, part or connector change (`lib` not in the diff).

## Findings

### MINOR
- **M1 – ch3 /DEN regressed from routed to open.** R302.1 (/DEN, to U1.28 via R102/R202/R402.1) was routed in T-0276 and is open again
  (R302.2 → U13 DEN pin has no link to the shared /DEN net). Cause: the ch3 DEN lane along x 56.36 had to make way for the IO2/IO5
  column vias. Evidence: `python3 tools/kpcb.py pdm-4ch drc` lists 37 unconnected, ch3 DEN among them; fixer report T-0281 step 4. Failure
  mechanism: if the board were built like this, ch3 diagnosis enable would float. The state is disclosed and the board is not
  orderable at 37 open items anyway, so this is a trade-off already named, not a hidden defect. Fix: none beyond the routing work
  already queued (STATUS "next one-way door": move the ch2/ch3 resistor blocks).
  Net effect of the stage is still 42 → 37 unconnected.

## Checked and OK
- DRC (`kpcb.py pdm-4ch drc`): 0 errors, schematic parity 0, 37 unconnected. This matches STATUS and the fix report (42 → 37). Only the pre-existing
  /IO13 `via_dangling` and silk/library warnings remain.
- Co-located +3V3 vias (`holes_co_located` warning): same two spots (141.35, 56.15 / 58.15) in the base and the new board; not introduced by T-0281.
- Via count 408 → 424: consistent with 5 stitching vias, the IO2/IO5 column and lane vias, and the +3V3 maze legs.
- IO2/IO5 copper is signal copper on 3.3 V nets (D201-A is the R205 clamp node). The 0.28 mm and 0.38 mm gaps to neighbouring items pass the 0.2 mm DRC rule; no 24 V net is
  involved at these gaps.
- Notch growth `VS_IN2_NOTCH` (55.6, 14.9, 56.6, 18.3) lies inside the decision 199 exit window (y 5–20) and was grown only to the column vias' extent. VS-In2 stays above
  the 1012.1 mm² gate (1093.8 mm² as stated; taken from the fixer report). Decision 208 records it.
- Heat budget: `heat_budget.py --ambient 40 --currents 4,4,4,4` gives Tj 101 °C, unchanged. No 16 A path or surge copper changed (diff is signal copper, stitching vias and the notch).
- Gate change in `routing_build.py` (`gnd_fragments`, `ref_check`): stricter than before (compares against the pre-build board, requires ≥ 2 ties for new weak GND-F/B islands, fails the
  build otherwise). Matches the Q-0076 / decision 206 wording; the stage-start weak islands are exempt via `gnd_weak_q0076.json`. Not wider than the ruling needed.
- Scope discipline: no part moved, D12–D15 not moved (the fixer gave the reason and the next one-way door), no schematic, outline or connector change.

## Not checked
- Island counts per pour (GND-In1 1, GND-In2 18, VS-In2 1) and 40/40 thermal vias: taken from the fixer report and STATUS; DRC shows no VS connectivity error.
- Whether the 5 new GND-F/B fragments each hold 2 ties: reported by the build gate, not recomputed.
- ERC, netlist and part facts: no schematic or part change since dfe3e43d8d38.
- Gerber against the JLCPCB footprints.

<!-- findings:begin -->
```json
[
  {
    "id": "V1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "ESP32-PDM-4CH.kicad_pcb: ch3 R302.1 /DEN",
    "summary": "ch3 /DEN link (routed in T-0276) is open again after the IO2/IO5 column took its lane; ch3 DEN pin would float if built as is",
    "fix": "route R302.1 in a later stage (e.g. after the ch2/ch3 resistor block move already named in STATUS); no extra action now",
    "door": "two-way",
    "reason": "signal copper only, rerouting is allowed under decision 206; board is not ordered",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
