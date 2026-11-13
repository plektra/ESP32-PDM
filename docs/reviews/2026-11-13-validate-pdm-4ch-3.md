# Validation pdm-4ch, re-check since 478ce84e52d5 (T-0254), 2026-11-13

Scope: `git diff 478ce84e52d5 -- hardware lib docs/design-notes.md`. Changes: T-0253 (T-0250 dangling-copper clean-up,
T-0251 +3V3 class width) in `ESP32-PDM-4CH.kicad_pcb`, `scripts/{maze_route,routing_build,fixed_routes,geom_export}.py`,
STATUS.md, design-notes. No schematic, symbol, footprint or part change, so no part facts to re-check.

## Findings

### MINOR
- **M1 design-notes §8 T-0253 / STATUS.md, wording of the +3V3 neck claim.** The text says the +3V3 path through the two 0.2 mm
  necks "feeds clamp diodes and pull-ups only". The +3V3 net also has L1.2 (buck output), C3/C8/C10, U5.1 (CA-IS3050G VCC1)
  and, once T-0218 connects it, U1.3 (ESP32 3V3). Which of these sit behind the necks was not traced (UNVERIFIED).
  No failure mechanism: 0.6 mm total of 0.2 mm copper is about 3 squares, a few mOhm, so even 0.5 A drops ~1–2 mV. Only
  the statement is imprecise. Fix: reword to "carries well under 0.5 A; 3 squares of 0.2 mm copper" (documentation).

No CRITICAL or MAJOR findings.

## Checked and OK
- Board DRC (`kicad-cli pcb drc --schematic-parity`, also with `--refill-zones` on a scratch copy): 417 violations (old 437),
  unconnected 48 (old 52), 0 footprint errors, no clearance/short/parity/hole/zone-island entries. Remaining non-silk
  items are the same as before: 1 track_width (CANL_XCVR 0.15 mm, existing), 2 holes_co_located, lib_footprint items.
- Per-net unconnected counts: none rose against old; the four fewer are R3.2, Q6.1, U14.IS/R403.1 and the IO2/IO5/SW2_IO/DEN pad
  stubs now ending in their pads (diff of DRC unconnected lists).
- track_dangling 5 → 0; via_dangling 16 → 1 (the /IO13 junction via at 164.1, 66.75, explained in the T-0253 fix report; it
  carries the connection and is a warning override).
- Track diff old/new (KiCad Python): 32 items removed, 6 added, 67 locked +3V3 tracks widened 0.2 → 0.3 mm, nothing narrowed.
  Removed items are on signal nets only (SW*_IO, IO*, DEN, MOD_ID, VBAT_SENSE) plus 2 +3V3 pieces replaced by the 2 added
  split segments; no VS, GND or other power copper removed. This matches STATUS ("32 items").
- +3V3 widths on board: 95 segments 0.3 mm, 4 at 0.2 mm (the two documented necks, 0.6 mm total, GND vias nearby); matches
  `fixed_routes.py` and STATUS. With the clearance DRC clean at 0.3 mm the widening is also sound.
- Six finishing segments added in `fixed_routes.py` (J6.8 ×2, R403.1, Q6.1, R3.2, R4.2) each end in the named pad
  (unconnected list confirms R3.2, Q6.1, R403.1 now connected); each is ≤ 1 mm.
- `prune()` guards: skips POWER_NETS/GND_NETS and net 0; via removed only if ≤ 1 item touches it; loops to stability;
  uses BOARD::Delete. `add_fixed` widens only same-net identical tracks and never narrows. `erode()` falls back to raw cells
  for thin copper. Scope is no bigger than the two items need. Heat/Tj statement (101 °C) not rerun: no power copper changed
  (VS/GND track set identical per the diff above).
- `git status`: no tracked file changed by my runs (scratch copies only).

## Not checked
- Re-routing quality / EMC of the maze copper; the remaining 48 unconnected items (T-0218).
- `tools/heat_budget.py` not rerun (no power or heat-relevant change); board power-copper identity inferred from the track diff.
- Which +3V3 consumers lie behind the two necks (see M1).

<!-- findings:begin -->
```json
[
  {
    "id": "M1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "docs/design-notes.md T-0253 +3V3 width note; STATUS.md",
    "summary": "Text says the +3V3 necks feed only clamp diodes and pull-ups, but +3V3 also feeds U5 VCC1, L1 output caps and later U1.3; topology behind the necks not traced",
    "fix": "Reword the note to state the actual bound (3 squares of 0.2 mm copper, mOhm range, negligible drop even at 0.5 A)",
    "door": "two-way",
    "reason": "documentation only; policy: documentation is a two-way door",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
