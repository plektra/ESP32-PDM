# EMC re-check, scope system (T-0165), 2026-11-07

Scope: `git diff 619a24338297 -- hardware lib docs/design-notes.md`. Changes since then: T-0158 (pdm-4ch J10 socket and Q30
part), T-0159 (BOM merge C2/C12/R9/R10), T-0160 (D7/D8 LEDs, J6 header, U1 labels), T-0161 (buck input filter position: JP1,
L2, C22, R73). `lib` unchanged. Netlists read with `sch_query.py`; no PCB exists. Question: do the changed filters,
protection parts and connectors keep invariant 4 and the layout rules of the last report, and do they add switching edges or coupling paths?

## Findings

None (0 CRITICAL, 0 MAJOR, 0 MINOR).

- **T-0158, J10 and Q30 (pdm-4ch).** The socket changes from 10.16 mm to 7.62 mm pitch, as HC2 J11 already has. Protection at the
  connector (D30, C30, FL30, JP30) is untouched, and pin 1 = VBAT_IN, pin 2 = GND stays. Q30 is AGM601LL in the same TOLL land and
  the same wiring. The path OUT → VS → Q30 → D30 is intact (invariant 4), D31 stays across Q30, and Q30 is still a static switch with
  no new edge. Its Ciss and gate drive sit behind U30 and C32 as before. The VS copper rule shrinks from 6 to ≥ 2 cm²; that is
  thermal, and the EMC rule that D31 sits on the VS loop is unchanged. The layout rule to keep J10 pole spacing and creepage on the
  battery side still applies: 7.62 mm pitch is larger than the pad-to-pad spacing the rules ask for.
- **T-0159, BOM merge.** Values and nets are unchanged (netlist compared by the fixer). C12 (CA-IS3050G VCC2 decoupling) goes from 0402 to 0603, with
  more capacitance at 5 V after DC bias (0.70 µF against 0.60 µF), which does not hurt the isolated CAN's emissions. C2 (buck boot) goes to
  0402 at 97 nF, within the TI requirement. R9/R10 are feedback dividers on a quiet node. No filter corner on an external line
  changed.
- **T-0160, LEDs and J6.** D7 (IO13) and D8 (+3V3) are 0.7 mA static loads behind 2.2 k, on-board, and add no switching edge. J6 is a DNP
  1×8 header carrying TXD0, RXD0, IO35–37 and IO42 unfiltered, which would be an antenna and ESD entry **only if fitted and cabled**; it is DNP, not in
  the BOM, and the STATUS layout rule puts it inside the board near the EMC test points, not at an edge connector. That keeps
  invariant 4 (it is not an external line) and I raise no finding. The rule is repeated below.
- **T-0161, buck input filter position.** In the default state JP1 (copper bridge, 0.2 mΩ) bypasses L2, so nothing changes electrically. The
  changed net split keeps C1/C19/U3 as the tight hot loop, and D3 (USB) stays on the U3 side. With L2 + C22/R73 fitted (DNP), this is a
  conducted-emission filter of 49–58 dB at f_sw and adds no new edge. L2 is a new magnetic part, and its stray field is a possible coupling
  path (layout rule below). The 64 V ring-up of the undamped case is already documented by the fixer as a MINOR note, covered by the
  rule "fit L2 only with C22/R73" and the scan; not repeated as a finding.

## Layout rules

The earlier rules hold. Additions and sharpenings:

1. **L2 (if fitted):** keep it away from the buck switch node and L1, and do not route the SW node or the CAN pair under or beside it. Orient it with its pads toward D2 on one side
   and C1/U3 on the other, so the input loop C1/C19/U3 VIN/GND stays the smallest loop and the L2 → C1 trace is short.
2. **JP1:** on the D2 → L2 → C1 path in series, not a stub. No via or branch between JP1/L2 and the C1 node other than C22.
3. **C22/R73:** next to C1, with the ground return to the same GND pour as C1/U3, not through a long trace.
4. **J6:** inside the board, away from the edge connectors and the CAN barrier; no routing of TXD0/RXD0/IO35–37 beside the CAN pair
   or the switch inputs. The pins stay unpopulated in a sold unit.
5. **J10 (pdm-4ch):** D30, C30, FL30 stay at the connector; the 7.62 mm pitch keeps at least the creepage of the rail spacing on the battery side. VS copper ≥ 2 cm² for Q30 is a floor; D31 stays on the VS loop.

## Installation guidance

No change from the last report. Do not fit J6 in an installed unit with a long cable.

## Not checked

- Layout (no PCB).
- The JLCPCB land of C96963 (L2) and of C577772 (J10) against the KiCad footprint (the fixers list both as open).
- L2's real EMI figure and the C22/R73 values, which depend on the pre-compliance scan (decision 28).
- Thermal and part-ratings of Q30 (validator and heat budget, not EMC).

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
