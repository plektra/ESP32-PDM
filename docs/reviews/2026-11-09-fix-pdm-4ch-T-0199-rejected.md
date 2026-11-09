# pdm-4ch layout stage 3: logic half (T-0199, 2026-11-09, pcb-fixer, unattended)

The stage placed 112 parked parts and moved 14 channel-2 parts. **18 parts stay parked, because the 100 × 65 mm single-sided
board has no room left for them**: the CAN block, J6, J4 (owner question from T-0197) and U30 (footprint, from T-0198).
That is a one-way question for the owner. Layout reasoning is in design-notes §8.11.

## What was placed

Coordinates in mm from the top-left board corner. y = 0 is the front edge, x = 100 the signal edge.

- **U1 ESP32-S3-MINI-1** at 69.25/9.75, rot 0. The antenna points at the front edge in the front signal-end corner
  (decision 128).
  - With the module on the board edge, its footprint keep-out (no copper or parts on either layer) covers only the
    strip x 46.5–92, y 0–4.5 on the board. That strip is clear.
  - x 69.25 is the right-most position whose keep-out stays out of H2's Ø 8 mm keep-out. A first try at 69.75 was
    flagged by `hole_keepout`.
- **Channel 2 moved** to make room for the antenna strip and the module. Each part's position relative to U12 is
  unchanged.
  - U12, C201–C204, R201, R202, R205 and R206 moved 2.6 mm toward the rail.
  - D202/R204/R203/R207 now form one column, with R203 and R207 upright, and D201 sits below U12.
  - Allowed: the antenna keep-out requires it.
- **Front signal corner:**
  - D8/R67 and D7/R59 in a row 4.6 mm from the front edge, visible in the carrier.
  - SW_RESET1, SW_BOOT1, C6/C9/R15 (EN), C7/R16 (IO0), R29/R42 (MOD_ID).
- **Module lower-left corner:** C8/C10 (3V3 decoupling), R60/R61/C60 (VBAT_SENSE), R62/C61 (NTC), R70 (TXD pull-up).
  U1's left pins face channel 2 with no room, so C8/C10 need a short B.Cu feed to pin 3.
- **LED sinks:** Q3–Q6, R17–R28, R50–R53 and C50–C53 between U1 and D50–D53 (J5 pins 6–9). Spill-over in the gaps of
  the J5 TVS column.
- **USB:** J3 at the front edge in the power-end corner (15.2/4.2, rot 180, receptacle outward), with F2, R13/C18/R14,
  D4–D6, R11/R12, C4, FB1, C5 and D3 around it.
- **Buck (rail-side strip, signal end):**
  - Input chain: F1 → R54 → D1/D2 → JP1 (76.2/55.9) ‖ L2 DNP (76.2/61.15, 6.8 mm body room).
  - Then C1 → C19 → U3: all three rot 90, VIN/SW on top, GND at the bottom, input loop about 3 mm.
  - Output: L1 (SW pad toward U3) → C3.
  - C22/R73 above C1, outside the loop. R44/C20, R9/R10 and C2/R43 between C31 and the buck.
- **Switch inputs:**
  - D12–D15, R1/R2/R5/R6 and R30–R33 in the corridor between the switch rows.
  - R3/R45 … R8/R48, D20–D24, R38–R41, R49/R57/R58/C21 along the rail-side strip x 8–53.

## Checks

- `kpcb.py pdm-4ch drc`: **0 errors on the board**, 404 warnings (silkscreen overlap/edge, for the silkscreen stage),
  469 unconnected (routing stage), parity 0.
  - The 6 U30 clearance errors listed belong to the parked U30 (T-0198 item).
  - Bottom SMT: none. Parts in hole keep-outs: none.
- Antenna strip, J10 clear zone (x 20–35, y 33–56) and U30's reserved spot (42.5/39.3) are free of parts.
- `fix_check.py --scope pdm-4ch`: **NOT READY** – "18 parts still off the board". All other gates pass: ERC/netlist
  unchanged, outline and hole keep-outs unchanged.
- The render was checked: groups sit together and connectors face their edges. The board is packed to about
  0.1–0.15 mm courtyard gaps.

## Blocked

- **FINDING (HIGH) – the board is full (one-way, owner).**
  - The parts still parked need about 560 mm² of courtyard: the CAN block about 330, J4 about 145, J6 about 80, U30
    about 15.
  - The free board left is about 1560 mm², but only as slivers under 4 mm wide between placed parts.
  - A packing trial confirmed this:
    - U5 (13 × 6.5 mm) and U6 (DPAK, 11 × 7 mm) fit nowhere.
    - The other CAN parts fit only as scattered fill across the board, which would break PCB rule 9 (one barrier block
      at J4).
  - So the CAN block was kept together and left parked.
  - Ways out:
    - (a) a 75 mm board depth like pdm-hc2 (+1000 mm²; outline, owner);
    - (b) the CAN block on the bottom side (decision 122, +33.77 USD per order);
    - (c) the ESP32 antenna overhanging the front edge by 4.5 mm (Espressif's preferred placement; frees the front
      strip, changes the mechanical envelope);
    - (d) a tighter power half (cuts the switch spacing that the heat spreading relies on).
- **FINDING (HIGH) – J4 versus the antenna.** T-0197's suggested J4 spot (front edge 10–15 mm from the signal corner)
  is now inside the antenna keep-out strip. The J4 ruling and the antenna position have to be decided together.
- **U30** (two-way, board-fixer, from T-0198): the stock TSOT-23-8 footprint has 0.15 mm pad gaps. Still parked, spot
  reserved.

## Gate re-check (after the orchestrator's rejection)

The orchestrator rejected the hand-in for the 18 parked parts. Checked again on 2026-11-09:
- `origin/main` brings no change to `lib/`, the schematics or `docs/decisions.md`: no U30 footprint and no owner
  ruling on J4 or the board size.
- None of the 18 can be placed without a one-way door or a broken gate:
  - J4 elsewhere moves an owner-fixed connector edge (decision 128).
  - U30 adds 6 DRC errors.
  - U5/U6 have no free spot; the rest of the CAN block fits only as scattered fill, against PCB rule 9.
- `fix_check --refs` (all 18): NOT READY, for the parked parts only.
- Each part is listed under a blocked item in the fix block (T-0199-space, T-0197-J4, U30-footprint). No design change
  in this round.
- Second rejection, same 18 parts: main and `docs/OWNER-INBOX.md` unchanged again, so the result is the same. This stage
  cannot pass the "nothing parked" gate until the owner rules on board space and J4 and a board-fixer replaces U30's
  footprint. Repeating the hand-in will not change that.

## Open points for the next stages

- After the owner's ruling: place the CAN block as one barrier block at J4 (PCB rule 9), J6 near the EMC test points,
  and U30 at its reserved spot.
- **Power copper / routing:**
  - Keep the antenna strip x 46.5–92, y 0–4.5 free of copper on both layers.
  - Feed U1 pin 3 from C8/C10 by a short B.Cu path.
  - Size the VS → F1 → R54 copper for the short-circuit pulse (≥ 0.6 mm at 2 oz, §8.3/§8.11).
  - USB_DP/DN run as a pair through the corridor between the switch rows.
  - The switch-input SWIN lines run 20–55 mm along the rail strip.
  - Whether 2 layers can route this density is open until the space question is settled.
- Safety: no battery-path, Q30/U30, D31 or output part moved. F1/R54 feed only the buck. A competent person reviews
  the board before installation.

<!-- fix:begin -->
```json
{
  "done": [],
  "blocked": [
    {"id": "T-0199-space", "door": "one-way", "reason": "Parked: U5, U6, D9, D10, D11, F3, R55, FB2, FL1, R71, R72, C11, C12, C13, C70 (CAN block) and J6. The 100 x 65 mm single-sided board is full after the logic half: about 410 mm2 of these courtyards against only slivers under 4 mm wide. U5 and U6 fit nowhere; a packing trial fits the other CAN parts only as scattered fill, which breaks PCB rule 9 (one barrier block at J4). Rechecked 2026-11-09 after the gate rejection: main unchanged, still no room.", "question": "How does the board get room for the CAN block and J6: (a) 75 mm depth like pdm-hc2, (b) CAN block on the bottom side (decision 122), (c) ESP32 antenna overhanging the front edge by 4.5 mm, or (d) a tighter power half?", "default": "(a) 100 x 75 mm, the same as pdm-hc2, with J4 and the CAN barrier in the added depth at the signal end"},
    {"id": "T-0197-J4", "door": "one-way", "reason": "Parked: J4. Still the open owner question from T-0197: J5 + J4 need 57 mm, but the signal edge has 49 mm between the H2/H4 keep-outs (decision 128). T-0197's suggested front-edge spot is now inside the ESP32 antenna keep-out strip x 46.5-92. Placing J4 on another edge changes an owner-fixed connector position.", "question": "Where does J4 (CAN) go, decided together with the antenna position and the board-space question above?", "default": "In the added depth of a 75 mm board at the signal end, plug outward, CAN barrier beside it"},
    {"id": "U30-footprint", "door": "two-way", "reason": "Parked: U30. Unchanged from T-0198: the stock TSOT-23-8 footprint has 0.15 mm pad gaps (6 DRC clearance errors when placed); needs a lib footprint from TI's DDF land and a schematic footprint change by a board-fixer. Spot 42.5/39.3 rot 180 kept free."}
  ],
  "refs": ["C1", "C10", "C18", "C19", "C2", "C20", "C201", "C202", "C203", "C204", "C21", "C22", "C3", "C4", "C5", "C50", "C51", "C52", "C53", "C6", "C60", "C61", "C7", "C8", "C9", "D1", "D12", "D13", "D14", "D15", "D2", "D20", "D201", "D202", "D21", "D22", "D23", "D24", "D3", "D4", "D5", "D6", "D7", "D8", "F1", "F2", "FB1", "J3", "JP1", "L1", "L2", "Q3", "Q4", "Q5", "Q6", "R1", "R10", "R11", "R12", "R13", "R14", "R15", "R16", "R17", "R18", "R19", "R2", "R20", "R201", "R202", "R203", "R204", "R205", "R206", "R207", "R21", "R22", "R23", "R24", "R25", "R26", "R27", "R28", "R29", "R3", "R30", "R31", "R32", "R33", "R38", "R39", "R4", "R40", "R41", "R42", "R43", "R44", "R45", "R46", "R47", "R48", "R49", "R5", "R50", "R51", "R52", "R53", "R54", "R57", "R58", "R59", "R6", "R60", "R61", "R62", "R67", "R7", "R70", "R73", "R8", "R9", "SW_BOOT1", "SW_RESET1", "U1", "U12", "U3"],
  "decisions": [
    {"area": "pdm-4ch", "text": "U1 at 69.25/9.75 rot 0 with its antenna section on the front edge; the footprint keep-out covers only x 46.5-92, y 0-4.5 on the board and stays clear of H2's keep-out; channel 2 moved 2.6 mm toward the rail and its IS column reshaped to make room"},
    {"area": "pdm-4ch", "text": "USB J3 at the front edge in the power-end corner (15.2/4.2 rot 180), the only free front-edge spot outside the antenna strip"},
    {"area": "pdm-4ch", "text": "Buck in the rail-side strip at the signal end: F1 -> R54 -> D1/D2 -> JP1 || L2 -> C1/C19/U3 (rot 90, input loop about 3 mm) -> L1 -> C3; C22/R73 outside the loop"},
    {"area": "pdm-4ch", "text": "CAN block kept parked as one group rather than scattered: it must form one PCB-rule-9 barrier block at J4, whose position is open"}
  ],
  "checks": {"drc": "0 errors on the board (6 more on the parked U30), 404 warnings, 469 unconnected", "parity": "0", "fix_check": "NOT READY: 18 parts still off the board (all other gates pass)"}
}
```
<!-- fix:end -->


## Rejected by the orchestrator

- 18 parts still off the board: C11, C12, C13, C70, D10, D11, D9, F3, FB2, FL1, J4, J6
