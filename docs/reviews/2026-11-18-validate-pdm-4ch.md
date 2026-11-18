# Validation pdm-4ch, PCB after decisions 215-224 (2026-11-18)

Scope: `hardware/pdm-4ch` at commit 1e8f0b0 (fully routed, EMC E22/E23 fix, silkscreen). Schematic unchanged since the last
validation except U30 (decision 222). Work files in a scratch folder; no design file edited (`*.kicad_prl` untouched).

## Findings

### CRITICAL
None.

### MAJOR
None.

### MINOR

- **V1 – Seven vias sit inside SMD pads, against layout rule 9 ("No via on an SMD pad"), and the build does not stop it.**
  Location (board coordinates, GND vias, drill 0.3 mm, dia 0.6 mm; offset = via centre from pad centre):
  C101.2 (0402 100 pF, pad 0.56 x 0.62, offset 0.10/0.25), C301.2 (0402 100 pF, offset 0.10/0.10), C402.2 (0402 10 nF,
  offset -0.04/-0.20), D7.1 (0603 status LED, pad 0.88 x 0.95, offset -0.36/0.06), D52.1 (SMAJ30CA, pad 2.5 x 1.8,
  offset 0.16/-0.78), U6 tab pad (DPAK, two vias). D52.1 is one of the "fixed GND ties" of decision 223; the others come
  from the router. Failure mechanism: an open 0.3 mm hole under a 0.56 mm 0402 pad draws the solder away on reflow, which
  gives an open or weak joint or a tilted part; JLCPCB does not plug or fill vias by default (design-notes line 1868 says
  the same for Q30's drain pad). C101/C301 are the 100 pF caps on the ch1/ch3 IS sense nets, C402 the 10 nF cap on OUT4, D7 is the status LED;
  a bad joint shows at bring-up and is repaired by hand, so this is a yield problem, not a safety one.
  Evidence: pcbnew scan of all SMD pads against all via centres (7 hits); `docs/ARCHITECTURE.md` rule 9 and its header
  sentence "the build enforces rules 2-12"; KiCad DRC reports no violation (no rule for it).
  Fix (cheapest): move each of the five small-part vias 0.5-0.8 mm off the pad along a short stub (the pours around them
  are GND, so the tie stays), or add a rule 9 check to `routing_build.py` and let the reroute handle it; for D52.1 and the
  U6 tab either accept (large pads, state it in rule 9) or the same stub. No part change.

## Checked and OK

- **U30 LM74502H-Q1 pinout** (decision 222): TI SNOSDE0A (Feb 2022, rev. May 2022) p. 4 Table 6-1 and Fig. 6-1: 1 EN/UVLO,
  2 GND, 3 NC, 4 VCAP, 5 VS, 6 GATE, 7 OV, 8 SRC. Exported netlist: pins 1, 5, 8 = VBAT_FL, 2 and 7 = GND, 4 = Net-(U30-VCAP)
  (C32 1 uF to VBAT_FL), 6 = Q30 gate, 3 NC. Matches, including "OV to GND if unused" (p. 4) and "EN/UVLO to VS for always on".
- **U30 absolute maximum** (p. 5 §7.1): VS -65...65 V, EN/UVLO and OV -0.3...65 V, SRC to GND -(70-VS)...VS, GATE-SRC 0...15 V,
  VCAP-VS -0.3...15 V. Against 30 V continuous and the D30 SMCJ30CA clamp (about 48 V): inside, 60 V recommended maximum also
  inside. C32 1 uF/50 V sees at most 13.9 V (p. 6 charge-pump turn-off); C30 on the same node covers the 22 nF VS capacitor
  (p. 5), 14 mm of 2 oz copper away.
- **Footprint `ESP32-PDM:TI_DDF0008A`** against TI drawing 4222047/E p. 31 (land example): pads 1.05 x 0.45, pitch 0.65, column
  pitch 2.6 mm; pad positions (+-1.3, +-0.325/0.975) and pin order 1-4 down the left, 5-8 up the right match Fig. 6-1.
- **BTT6050-1ERA heat inputs** (Infineon Rev. 1.00 2019-03-09, p. 15 Table 6): RDS(ON) at 150 C 70 / 95 / 100 mOhm
  (min/typ/max, 4 A), 50 mOhm typ at 25 C. `tools/heat_budget.py` uses 60 / 105 mOhm, so it is conservative.
  `python3 tools/heat_budget.py --ambient 40 --currents 4,4,4,4`: 1.40 W per channel, 8.92 W total, Tj 101 C. Matches STATUS.
- **Decision 221 PWM numbers**: slew 0.3 / 0.8 / 1.4 V/us (p. 15, P_5.5.11/12) and EON 0.6 mJ / EOFF 0.7 mJ at 36 V, 12 Ohm
  (p. 16, P_5.5.19/20) as cited. E per edge = V^2 I / (6 slew) is the correct linear-ramp integral for a resistive load.
  Recomputed 24 V row: 28.8 V, 4 A, 0.8 V/us gives 0.69 mJ per edge, 0.14 W at 100 Hz; 0.3 V/us gives 0.37 W; with
  about 42 K/W per watt this lowers the current to about 3.8 A / 3.5 A as in the table. The PWM claims stay "proposed".
- **ERC** (`kicad-cli sch erc`, all severities): 0 errors, 5 warnings, all `lib_symbol_mismatch` (4 x BC817 in Transistor_BJT,
  J3 USB4145 in ESP32-PDM); no unconnected pin, no power-pin error. Netlist: 227 components, no duplicate or unannotated
  reference, no single-pin net except explicit `unconnected-` pins; only FL30 (DNP ferrite, bridged by JP30 copper) has no
  footprint.
- **DRC** (`kicad-cli pcb drc --schematic-parity --all-track-errors`): 0 errors, 0 unconnected pads, 4 warnings (3 U1 silk lines
  clipped at the antenna edge, U1 library-version note). One "parity" line is `missing_footprint FL30`, the intended
  bridge; the STATUS statement "parity 0" counts it as none.
- **CAN isolation** (rule 6, decision 217), pcbnew minimum distance between GND_CAN-side copper (GND_CAN, VCC2, XCVR, BUS,
  NET-S, D11/F3/D10 nodes) and every other net, per layer: F.Cu, In1, In2, B.Cu items >= 4.18 mm apart apart from C70 (the
  allowed crossing: 1.82 mm pad to pad) and the U5 pins; pour to pour 4.02 mm on all four layers. Nothing but C70 crosses.
- **VS-In2** (rule 5, decision 218): 1 island, 1003.4 mm2 (84 % of 1190.7, floor 75 %), all 44 VS vias lie in the In2 fill
  (40 thermal + 4 others). VS and VBAT_IN pours: F.Cu 1 island each, B.Cu 1 island each.
- **Rule 4** (1.0 mm from VS/VBAT_IN to other nets on F/B): only pad-to-pad pairs inside the PROFET package (0.48 mm, package
  geometry), R60 pads 0.48 mm, one GND via 0.45 mm from the U13 tab (via of a GND pad next to it). Nothing below 0.45 mm; at
  about 36 V peak that is not an electrical problem.
- **Silkscreen legends** (decision 224) against the exported netlist and pad coordinates: J5 pins 1-10 = SW1-SW4, SW SUPPLY,
  LED1-LED4, GND; J4 = GND_CAN, NET-S, CANH, CANL; J11 pins 1-4 = OUT1-OUT4 at the pad rows; J10 pin 1 = VBAT_IN ("+" at y 89.5
  = pad 1), pin 2 = GND ("-" at y 99.9); J6 pins 1-8 = GND, TXD0, RXD0, IO35-IO37, IO42, +3V3. Bottom legends are mirrored.
- **Divider/threshold spot checks:** VBAT_SENSE 220 k / 22 k gives 2.62 V at 28.8 V; SW_SENSE R49 10 k / R57 4.7 k with
  D24 3.3 V clamp reads high above about 7.7 V (IO12 VIH 0.75 x 3.3 V), clamp current 2.7 mA at 30 V. Unchanged from earlier
  validations.

## Not checked

- Gerber, BOM and CPL package in `fab/` (STATUS says it predates decisions 223/224 and must be rebuilt before quoting).
- JLCPCB footprints against KiCad land patterns (pre-order checklist), CPL rotations, stock.
- The fully re-derived power-path surge behaviour with the new U30 (hot-plug body-diode current, T-0129) and the T-0118/T-0161
  bench tests; unchanged by decision 222 and not recomputed.
- E22/E23/E25 track lengths from `emc_report.py` (taken from STATUS; DRC and connectivity of those routes confirmed).
- Part facts of parts untouched since the earlier validations (PROFET pinout from the cached file only; BTT6050 slew and RDS(on)
  figures were checked on the PDF).
- Firmware-side items, EMC beyond the layout rules.

<!-- findings:begin -->
```json
[
  {
    "id": "V1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "ESP32-PDM-4CH.kicad_pcb: GND vias in pads C101.2, C301.2, C402.2, D7.1, D52.1, U6 tab",
    "summary": "7 vias sit inside SMD pads (rule 9 forbids it); open 0.3 mm holes under 0402 pads can wick solder away and leave an open joint",
    "fix": "move the five small-part vias off their pads on a short GND stub (or add a rule 9 check to routing_build.py); accept D52.1 and the U6 tab if stated in rule 9",
    "door": "two-way",
    "reason": "layout-only copper change, no part or schematic change, board not ordered (git revert undoes it)",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
