# pdm-4ch status

Updated: 2026-11-17 (decisions 215, 217–219: routing review, one-pass reroute – **fully routed, 0 unconnected**)

**2026-11-16/17 (decisions 215, 217–219, owner – interactive): the board is fully routed.** `build_routing.sh`:
0 DRC errors, **0 unconnected** (was 29), parity 0, every power pour whole; a second build from the new board gives
the same. VS-In2: 1 island, 1026.2 mm², 40/40 thermal vias. Tj 101 °C at 40 °C, 4 × 4 A (unchanged).
- **Review finding (decision 215).** The board was not out of room: 17 nets run from U1 to the switch/CAN block and
  11 cross the VS block, with B.Cu and In2 mostly empty. It was stuck on pad access (parts pad to pad, many of them
  facing away from their connections) and on a method that locked every earlier route.
- **Method.** All signal copper except the CAN and USB pairs is removed and routed again together:
  `scripts/pf_export.py` (base board + geometry) → `scripts/pf_route.py` + `pf_core.c` (0.05 mm grid, every net
  negotiates with the others, then rip-up) → `scripts/pf_land.py` writes `scripts/pf_routes.json`, which
  `fixed_routes.py` loads → `build_routing.sh` with all its gates. A full reroute takes about 10 minutes. KiCad's DRC
  agrees with the router's rules (the check: its output placed on the board gives 0 errors).
- **What unlocked it,** in order of effect: (1) the CAN barrier keep-out drawn to the rule 9 minimum (decision 217):
  the one passage to the switch-input block went from 6.8 to 10.9 mm; (2) In2 runs may cross the VS-In2 east edge
  anywhere (decision 218); (3) 27 small parts turned 180° so their pads face their connections, e.g. the six
  resistors beside U12/U13; (4) R30–R33 moved out of the switch-input pocket to their source by C14–C17; (5) D24 and
  D23 moved out of the pocket; (6) at J3 the CC1 via moved, D4 and FB1 turned, VBUS and D3-A 0.2 mm (decision 219).
- **Not moved:** J6, the connectors, U1, the PROFETs, the power path, all power pour outlines, SW_BOOT1/SW_RESET1.
  No schematic change.
- **Found on the way:** no pad was ever walled in by fixed copper; the earlier "sealed" findings came from the old
  router's model (a hole rule that fenced in every through-hole pad's own net).
- **Open:** silkscreen (stage 6); the EMC layout review and the validator review of the PCB, including decision 217
  (barrier keep-out) and the 0.2 mm VBUS/D3-A necks at J3; the old router scripts and the superseded decision rows
  are still to be cleaned up. A competent person reviews the board before installation.

**2026-11-17: 3D models complete.** Every placed part now has a 3D model. The nine that had none or pointed to a
file missing in KiCad 10 (PROFETs, KF135T, KF2EDGRC, both WJ15EDGRC, USB-C, TS-1187A, 1812 fuses, ESP32 module) use
LCSC/EasyEDA STEP models in `lib/ESP32-PDM.3dshapes/` (see its README). Placement checked in renders. No copper,
footprint pad or schematic change; DRC unchanged.

## Next

1. **Do not run *Update Symbols from Library*, and do not save the schematics from KiCad 10 by hand** (2026-11-08):
   a KiCad 10 save with a symbol update reset every Value/Footprint/LCSC field, merged GND_CAN into GND and renamed
   SW_BOOT1/SW_RESET1, FL30, JP30. That copy is kept on the local branch `backup/kicad10-resave-2026-11-08`, never
   merged. Schematic changes go through `tools/ksch.py` (agents), checked by ERC and the netlist compare; a KiCad 10
   format upgrade, if wanted, is a scripted package of its own with a netlist-identical check.
2. Silkscreen (layout stage 6): connector and pin-1 marks, "BATTERY + −", OUT1–OUT4, "PANEL", "CAN"; clear the
   398 silkscreen warnings of the DRC.
3. `/emc pdm-4ch` on the layout and `/validate pdm-4ch` on the PCB, then fix the findings. Points to check first:
   decision 217 (CAN barrier keep-out at the rule minimum), decision 218 (VS-In2 gate), the 0.2 mm VBUS and
   Net-(D3-A) necks at J3 (decision 219), the fill keep-outs that removed GND slivers on F.Cu/B.Cu/In2.
4. At the first order, check the CPL rotation of U11–U14 and U3 (EasyEDA draws both packages rotated 90°), and
   the footprints listed in the pre-order checklist below.
5. Before ordering: check the `CP_Elec_8x10` and `C_1206` footprints against the JLCPCB footprints of C487384 and
   C170101; before fitting D103–D403 read the demagnetisation note in design-notes §8.2. Remaining part check from
   the BOM audit: PESD2CAN pin 3 = common.
6. Layout rules: `docs/ARCHITECTURE.md`, "PCB layout rules". Layout work is interactive (decision 216); a new
   signal routing is `pf_export.py` → `pf_route.py` → `pf_land.py` → `build_routing.sh` in `scripts/`.

History of the schematic fix rounds and of the layout up to 2026-11-16: `STATUS-history.md` beside this file.

## Prototype test list

- **Decision 127 – connector fit (moved from decision 98):** on the first assembled boards check that the J11, J5 and J4 plugs cannot go in reversed; whether the J4 plug enters the J5 socket (labels are on the silkscreen either way); the height across the rail (part height + pin length + 1 mm; J10 expected 34.8 mm; recorded, not a pass/fail limit); the J10 wire-entry side and M4 screw access at 36 mm pitch; reach of mated plugs and cable bend past the edge. Findings go into the next revision.
- **T-0118 / decision 81 – PTC hard short (mandatory before installation):** from a 30 V battery-like supply (low source
  impedance), short J5.5 to GND (behind F4/R56), then behind F1 (D1/D2 node) and behind F3 (D10/FB2 node). Scope the
  current; afterwards inspect R54–R56 and F1/F3/F4 (cracks, discoloration, resistance). Pass before installation
  (design-notes §8.3).
  T-0161: make the short behind F1 with **JP1 fitted** (a short at C1 also puts JP1 in the path) and, if L2 is ever fitted, repeat it.
- **T-0161 / decision 28 – buck input filter (pre-compliance scan):** conducted emission on the battery input with JP1 fitted. If the buck's 1.1 MHz or PFM components need it: cut JP1, fit L2 (start 8.2 µH C96963) **together with** C22 2.2 µF + R73 10 Ω (3.3–4.7 Ω 1206 if the ring at 33–57 kHz is not damped enough). Then scope U3 VIN at light load (PFM) and during a 28.8 V hot-plug; the peak must stay ≤ 65 V (design-notes §8.3).
- **T-0042 / Q-0034 – switch-path margin:** measure IN − device GND (U11–U14 pin IN vs the channel's ground network) at
  SWIN = 10.5 V with the channel on, once with the 3.3 V rail removed and once with it present. Repeat at a 10.5 V battery
  with D55's drop (SWIN ≈ 9.8–10.1 V). Pass: ≥ 2.0 V (VIN(H) min). If short, the planned fix is **RIN R101/R201/R301/R401 →
  4.7 kΩ**. The divider on the shared sheet stays an owner decision. Calculation in design-notes §3.
- T-0129 / Q-0067 - negative pulse on J10 with VS charged and the source short-circuit current within 31 A: scope Q30 VDS and VS (also VBAT_IN); expect VDS about 60 V or less and VS no lower than about -4 V; inspect C31 afterwards.
- T-0012: check the hardware switch path with a bouncing contact (no output chatter, τ ≈ 1.5 ms). Measure the ON/OFF
  switch voltage (≈ 8 V at the switch, ≈ 8.5 V at the battery).

## Pre-order checklist (T-0065)

- Decision 127: no connector samples before the order; buy the connector sets with the board order and re-check their stock, plug sets included. Footprints of J10, J11, J5, J4 checked against the maker drawings and the EasyEDA footprints: pass (2026-11-08, see the log above). Hand-solder J10 with a powerful iron; check the joints.
- J10 marking (T-0177, layout rule 2 of `docs/reviews/2026-11-07-emc-system-2.md`): silkscreen "BATTERY" and the polarity at J10. The cross-board mis-plug of T-0177 (battery plug into a pdm-hc2 J11) no longer applies: J10 is a fixed screw terminal with no plug (decision 121).
- Recheck JLCPCB stock of the thin parts: TPS48110A (HC2), L1 SWPA6045S8R2MT (1231 on 2026-11-02), BTT6050 (4-ch),
  LMR51610YF (only if the scan asks for FPWM), plus the new C170101.
- L1 approved alternates (datasheet-checked, same 8.2 µH / 0.056 Ω max / I_sat 3.9 A / I_rms 2.6 A / 6045 land):
  **Sunltech SLW6045S8R2MST C47018494** (no EasyEDA footprint at JLCPCB – map it to the SWPA land) and
  **cjiang FNR6045S8R2MT C168074**.
- H5VL10B has no published TLP curve (8/20 µs clamp only); accepted on that data (design-notes §8.3).
- Check the KiCad footprints `D_SOD-882`, `TO-252-2`, `L_0805_2012Metric` against the JLCPCB footprints of C7420372,
  C58069, C1017.
- T-0118: check the KiCad `Fuse_1812_4532Metric` pads (1.125 × 3.4 mm, pitch 4.275 mm) of F1–F4 against the JLCPCB
  footprint of C70113 (datasheet pads 1.78 × 3.2 mm, gap 3.2 mm), and `R_2512_6332Metric` (R54–R56) against the JLCPCB
  footprint of C7420022. C70113 is up to 1.8 mm high. Recheck stock of C70113 and C7420022.
- T-0067: check the KiCad footprints `SOIC-8_7.5x5.85mm_P1.27mm` (U5) and `L_CommonModeChoke_Coilank_ACM4532`
  (FL1) against the JLCPCB footprints of C528763 and C20624726. The FL1 pad numbering must match windings 1→2 / 4→3
  before FL1 is ever fitted (design-notes §8.5).
- T-0051 (production / flashing): never burn eFuse `EFUSE_STRAP_JTAG_SEL` – IO3 is held low by the IS2 network
  (design-notes §2).
- T-0107/T-0120: C30 and C104–C404 use C170101 2.2 µF instead of C13832 1 µF. pdm-4ch no longer carries C13832, so its loading fee is gone; this pays on short runs only. Revisit the choice if runs grow past about 12 boards (owner ruling Q-0063). RIS is now 2 × C4410 per channel.
- T-0121: check the KiCad footprints `Infineon_PG-HSOF-8-1` (Q30, pads 1 G / 2 S / 3 D) and `ESP32-PDM:TI_DDF0008A` (U30, since 2026-11-09; was `TSOT-23-8`; TI DDF land
  1.05 × 0.45 mm pads, 2.6 mm column pitch) against the JLCPCB footprints of C5464765 and C5219210. Recheck stock (C5464765
  2016 on 2026-11-07, C5219210 2923 on 2026-11-03).
- T-0143: check KiCad `D_SMC` (D31; pads 2.5 × 3.3 mm, gap 4.3 mm) against the JLCPCB footprint of C42371557 (`SMC_L7.2-W5.8-LS8.1-BI`, pads 3 × 3.8 mm, gap 4.6 mm; hongjiacheng suggested land: pads 3.03 × 3.82 mm, gap at most 3.84 mm) and recheck its stock (10271 on 2026-11-04).
- T-0021: BOM lines without `LCSC` are now only H1–H4 and the DNP positions.
- T-0160: check the CPL rotation of D7/D8 (C2286; JLCPCB footprint pad 1 = anode, KiCad pad 1 = cathode, cathode on the same side) and the KiCad `LED_0603_1608Metric` pads against `LED-SMD_L1.6-W0.8-R-RD`.

## For /system

- Decision 150: cost reviews still price pdm-4ch as 2 layers; the owner's quote is €43.95 for 5 boards (4 layers, 100 × 75 mm). ARCHITECTURE Mechanics/Budgets: note 4 layers.
- T-0160 (`/system firmware`): IO13 drives the status LED (high = on, ≈ 0.7 mA); keep its internal pull-up off; hold it low in Sleep. Leave spare inputs on J6 (IO35–IO37, IO42) with a pull enabled while unused.
- Decision 93 (`/system firmware`): read IO12 (high = SW_SUPPLY present); alert only while VBAT_SENSE shows a healthy battery.
- T-0107 (`/system firmware`): the IS scale constant is now **RIS = 500 Ω** (2 × 1 kΩ). IL = VIS / 500 Ω × kILIS, ≈ 0.33 V/A for the BTT6050 and ≈ 0.128 V/A for the BTT6010 (design-notes §6.1). A sense current of about 5.8 mA reads full scale (2.9 V), below the minimum IIS(FAULT) of 6 mA, so DEN rule 2 still sees every fault.
- T-0069 (`/system firmware`): firmware requirements for DEN (design-notes §6.1).
- RIS at the 40 mA maximum fault current: 0.8 W in two 0.25 W parts since T-0107, covered only by firmware; hardware
  cover needs a resistor of at least the fault power – owner decision if wanted.

- Decision 127 (`/system mechanical`): the rail pitch is a soft goal, not a constraint. ARCHITECTURE Mechanics and decisions 97/123 still say "about 36 mm"; reword it as a target. Decision 123's arms-instead-of-plate choice for the long DIN mount was made for the 36 mm and may be revisited.
- Decision 138: ARCHITECTURE Mechanics and decision 123's two mount depths (65/75 mm) – both boards are now 100 × 75 mm, one long DIN mount. Sync in `/system`.
- Decision 128: ARCHITECTURE Mechanics still says "length up to 100 mm, set at layout"; now 100 mm on both boards, H1–H4 4 mm from both edges, rail-side hole spacing 92 mm. Sync in `/system`.
- Mounting decided (decision 123). After layout: the printed DIN mount and enclosure as OpenSCAD files (`/system mechanical`).
