# pdm-4ch status

Updated: 2026-11-21 (footprint check against JLCPCB: `docs/reviews/2026-11-21-footprints-pdm-4ch.md`; decision 238: RIS → Vishay CRCW-HP C844867, decision 235 done; decisions 230–236: firmware rulings, RIS hardware cover, ARCHITECTURE sync; decision 226: test pads; decision 225: validator V1 fixed, no via on SMD pads; decision 224: silkscreen done; decision 223: EMC E22/E23 fixed, E25 report in the build; decision
222: U30 → LM74502H-Q1; decision 221: PWM rating, confirmed by 234)

**2026-11-22 (`/board pdm-4ch pcb`, decision 220 licence, owner: "add it"):** title blocks on all five schematic
sheets (`tools/ksch.py` `set_title_block`, by `scripts/title_block.py`) and on the PCB (pcbnew): "ESP32-PDM pdm-4ch",
rev A, 2026-11, comments "Hardware licence: CERN-OHL-S v2" and "Source: github.com/plektra/ESP32-PDM". The source
location was missing on the board: `scripts/silk.py` now prints it as a third bottom line under the licence (1.0 mm).
Checks: ERC unchanged (5 library notices), netlist nets identical (167); PCB diff = title block + the new text (silk
texts redrawn), DRC 0 errors / 0 unconnected / 0 parity; package rebuilt, only the Gerber zip changed.

**2026-11-22 (`/board pdm-4ch pcb`, owner: "apply corrections"):** the CPL corrections of the footprint check are in
`tools/jlc_package.py` (`CPL_FIX`, per LCSC part, applied only on the footprint it was measured on; the report flags
any other). Package rebuilt: DRC gate 0 errors / 0 unconnected / 0 parity, 24 CPL rows changed, BOM and copper
unchanged. Cross-check: JLCPCB's EasyEDA pads placed by the new CPL land within 0.4 mm of our pads on all 142 checked
parts (the switch's 3.7 mm is pad numbering only; Q30 leads 0.00 mm). D7/D8 stay at KiCad's rotation.

**2026-11-21 (`/board pdm-4ch pcb`, footprint check, owner asked for the scripted comparison):** 37 LCSC parts compared
with their JLCPCB/EasyEDA footprints by `tools/fp_check/` (report `docs/reviews/2026-11-21-footprints-pdm-4ch.md`). No
design file changed. Every fitted land passes (D30/D31 SMC and the SOD-123FL diodes are smaller than the maker's
suggestion, accepted; Q30 land checked against the AGM601LL p. 5 drawing; PESD2CAN pin 3 = common confirmed). Found:
(1) the CPL carries KiCad's raw rotation and origin, so **U3, U5, U11–U14, U30 and the SOT-23 parts need a rotation
correction and U1, J3, U6, Q30 an origin correction** (table in the report; D7/D8 need none, polarity right at 0°);
(2) **FL1 (DNP) cannot be fitted as drawn**: EasyEDA/cjiang put each winding end to end along the long side, our
footprint pairs pads 1–2 on the short side, so a fitted FL1 would join CANH_XCVR to CANL_XCVR. No effect on this order.
Stock: all fitted parts in stock; SMAJ30CA back to 23897.

**2026-11-21 (`/board pdm-4ch pcb`, decision 238, owner):** decision 235 done. The eight RIS parts R103/R107 … R403/R407 are now **Vishay CRCW12061K00FKEAHP C844867** (1206, 0.75 W at 70 °C; 0.40 W each at the 40 mA fault maximum = 53 % at 65 °C). Same footprint, no layout change: `channel.kicad_sch` by `tools/ksch.py` (netlist identical, 167 nets; ERC unchanged, 5 library notices), PCB footprint fields synced (LCSC, Description, MPN), JLCPCB package rebuilt (DRC gate 0 errors / 0 unconnected / 0 parity; BOM 54 unique parts, one more extended: 15 fees). Facts file `docs/part-facts/C844867.md`, design-notes §6.1 and the failure-mode note updated.

**2026-11-21 (`/system firmware`, decisions 230–236, owner):** firmware rulings: stack confirmed, SensESP v3 after a build trial (230); fault behaviour confirmed, bus outputs off after a reset (231); NMEA 2000 messages confirmed plus bus alerts (232); version 1 = Active + OTA (233); PWM rating 221 confirmed and PWM added to the draft (234). **Decision 235: RIS gets a hardware cover for the 40 mA fault before the first order** (see Next). The "For /system" items are done: layout rules and mechanics are in ARCHITECTURE (236); the firmware items (IO13, spare pulls, IO12, RIS 500 Ω, DEN) are in the draft (`hal.cpp`, `pdm_config.h`).

**2026-11-18 (decisions 227–229, confirmed by 230–232, firmware draft, no hardware change):** `firmware/` holds a first pdm-4ch firmware (Active mode, NMEA 2000 switch bank, DEN-pulsed current sense, soft fuse, panel LEDs, USB console). It builds for the ESP32-S3 and its logic passes 15 host tests; it has not run on a board. For bring-up it can replace MicroPython once the unverified values in `firmware/README.md` are settled (DEN settling time, IO33 state at reset); its TWAI driver covers the CAN test of bring-up.md §8.

**2026-11-18 (decision 226, owner – interactive): copper-only test pads.** The debug-access check found USB-Serial/JTAG, BOOT/RESET and J6 enough for firmware, but no test points for bring-up scoping (EMC review 2026-11-03 item 9). Added five bare 1.0 mm pads, top side, not in BOM/CPL: TP1 GND (17.6, 59.4) 3 mm from the buck SW node, TP30 VS (56.1, 42.7), TP70 CANH_BUS (83.6, 53.3), TP71 CANL_BUS (85.3, 54.6), TP72 GND_CAN (89.4, 57.3). No new track or via (pads join their pours or sit on the fixed CAN routes). Buck SW and +3V3 are probed on L1's pads. `silk.py` prints the net name beside each pad. Probe table with scope-ground points: `bring-up.md`. Schematic: TP1/TP30 on the root, TP70–TP72 in the shared `can` sheet (pdm-hc2 too); ERC unchanged, netlist only the five nodes added. Build (`LAND_BEST=1`): 0 DRC errors, 4 warnings (known), 0 unconnected, parity 0, pours whole, tracks/vias unchanged, VS-In2 2 pieces 966.9 mm², GND_CAN-F −0.9 mm². **Note:** the build no longer adds the 43 `sliver-*` fill keep-outs that the committed board carried; a build of the untouched HEAD gives the same (0 slivers, identical GND islands), so this is the build's own current output, not the pads. Fab package rebuilt: it was stale (CPL still had the pre-decision-223 C50/D24/D50/R19 positions); BOM unchanged, CPL 199 rows.

**2026-11-18 (decision 225, owner): layout validated, V1 fixed.** `/validate pdm-4ch` on the layout
(`docs/reviews/2026-11-18-validate-pdm-4ch.md`): 0 CRITICAL, 0 MAJOR, 1 MINOR. V1: GND vias inside SMD pads (rule 9),
mostly placed by the build's own stitching (a GND fill contains its GND pads). Fixed in the build: stitching and tie
vias never touch an SMD pad, and `finish()` fails a build that has a via on an SMD pad below 10 mm² (the U6 tab via
stays). Pads that lost their only tie got their own off-pad via (C101.2, C402.2, D101.1, R106.2) or a router tie
(**a new reroute needs `pf_route.py --iters 300 --ties-extra C301.2,U1.63`**, see `build_routing.sh`). Result:
0 DRC errors, 0 unconnected, parity 0, pours whole; VS-In2 2 pieces, 966.9 mm² (81 %; was 1 piece 1003.4 mm²; gate
75 %, every piece via-tied), 40/40 thermal vias, Tj 101 °C; a second build gives the same. Silkscreen unchanged.
Not covered by the review: the fab package, the JLCPCB footprint/rotation checks and stock (pre-order list), the
hot-plug surge path with the new U30.
Updated: 2026-11-18 (RoHS/REACH check, no design change; decision 224: silkscreen done; decision 223: EMC E22/E23 fixed, E25 report in the build; decision
222: U30 → LM74502H-Q1; decision 221: PWM rating, confirmed by 234)

**2026-11-18 (owner – interactive): RoHS and REACH check** of the 54 BOM parts and 7 THT connector parts,
`docs/reviews/2026-11-18-rohs-reach-pdm-4ch.md` + `.csv`. RoHS: no non-compliant part (19 by exemption 7(a)/7(c)-I).
REACH: Q30 AGM601LL declares lead above 0.1 % (SGS); U6 likely too (unverified); 22 parts have no maker statement,
mainly the THT connectors. Nothing blocks the prototype order; the declarations to collect before any sale are in the
pre-order checklist.
Follow-up the same day (no browser in the session): U6 declaration still unread (st.com timed out); LCSC pages of
14 of the 15 listing-only parts read, no maker certificate found; DigiKey lists only U6, U1 and L1 and its web pages
gave no RoHS/REACH values without a browser; declaration requests for 16
makers drafted, not sent, in `docs/reviews/2026-11-18-rohs-reach-requests-pdm-4ch.md`.
Browser follow-up (Chrome): ST's declaration for U6 returns 404 (also from ST's product page), so U6 stays
unverified; the DPAK sister part L78M05CDT-TR declares lead 4566 ppm under 7(a). LCSC documents read: Kefa brass
C3604 holds 3.5 % lead under 6(c) (SGS, raw material); hongjiacheng (= "R+O" at LCSC) mixed diode sample holds
2.6 % lead under 7(a) (SGS), so D4–D6 now count as "by exemption"; MMBT5551 and the XKB switch now have maker
RoHS evidence. Listing-only parts 15 → 12. DigiKey: U6 "ROHS3 Compliant" / "REACH Unaffected", U1 "REACH
Unaffected", L1 no values. C96963 is not listed at LCSC. Request drafts corrected and one for ST added (not sent).
2026-11-20: the owner found ST's 2014 material declaration, which names L78M05ABDT-TR: lead 2984 ppm of the part
under 7(a). U6 now counts as a second part with lead above 0.1 % (REACH: no maker statement 22 → 21 parts). The
current version of that declaration is still unread (ST's link is dead); the owner closed R2 without it, the
request to ST is optional.

**2026-11-18 (decision 224, owner – interactive): silkscreen done.** `scripts/silk.py` (KiCad python, rewrites the
board; the same result on every run) draws all silkscreen. Re-run it after any part move or reroute.
- References shown only for the 38 parts looked for at bring-up and service (list in decision 224); all others hidden
  and kept on F.Fab for `fab/ESP32-PDM-4CH-assembly.pdf` (assembly drawing, 2:1, every reference).
- Top: OUT1–OUT4 (0.8 mm, one column level with the J11 pins; OUT1/OUT3 sit between the pads of the DNP TVS
  footprints D103/D303 and would be hidden under a fitted diode), BATTERY, + / − at J10, PANEL and CAN between J5 and
  J4. The old labels were off: OUT1/OUT3 sat beside the wrong pins, the "1" was at J4 pin 3, PANEL under J5's body.
- Bottom (no parts there): pin legends of J5 (SW1–SW4, SW SUPPLY, LED1–LED4, GND), J4 (NET-C GND, NET-S, CAN-H,
  CAN-L), J11 (OUT1–OUT4), J10 (BAT + / BAT −), J6 (GND, TXD0, RXD0, IO35–IO37, IO42, +3V3); board name, revision,
  licence.
- DRC: 0 errors, 0 unconnected, parity 0; warnings 413 → 4: three U1 module silk lines clipped at the antenna edge
  (JLCPCB clips silk at the outline) and the U1 library-version note. No copper change.

**2026-11-17/18 (decision 223, owner – interactive): EMC layout findings E22 and E23 fixed, E25 added.** One reroute
(`pf_route.py --iters 300`, converged at round 259, 0 open); `build_routing.sh`: 0 DRC errors, 0 unconnected,
parity 0, every power pour whole; VS-In2 1 island, 1003.4 mm² (84 %, was 1026.2), 40/40 thermal vias; Tj 101 °C at
40 °C, 4 × 4 A (unchanged); DRC warnings 413 (unchanged, silkscreen).
- **E22:** D50 (LED_K1 TVS) moved to (87.6, 27.05) into the J5 TVS column beside D51/D53/D54, 1.6 mm of copper
  from J5.6 (was 10.3 mm); R19 (83.0, 27.05, 180°) and C50 (79.6, 27.05, 180°) take its old place, so LED1 now
  has the LED2–LED4 order TVS → R → C. Copper path C50 → R19.2 **0.8 mm** (was 22.8 mm); C50.2 GND via 0.9 mm away.
  D24 (SW_SENSE clamp, 3.3 V zener) moved to (86.8, 20.25) to make room; it may sit anywhere on SW_SENSE.
- **E23:** the CANH hand route (`fixed_routes.py`) now enters J4.3 → B.Cu → via (88.6, 52.4) → D9.1 → via
  (86.0, 53.45) → R71/FL1: R71 is tapped behind the clamp. TVS stub **0.0 mm** (was 6.4 mm), like CANL.
- **E25:** `scripts/emc_report.py` runs after each DRC in `build_routing.sh`, report only: filter cap to resistor
  path (≤ 5 mm), TVS stub on every J3/J4/J5 line (≤ 1 mm), GND via within 2.5 mm of every connector-line TVS and
  filter-cap GND pad, FB–SW gap (≥ 2 mm). Current result: 2 CHECK lines, both known – FB–SW 0.70 mm (E24, waits for
  the T-0161 scan) and SW_SUPPLY (below).
- **Found on the way, fixed:** (a) some GND pads had no via of their own and lived on F.Cu fill or on grid
  stitching vias that the build only places where all four layers are GND; a reroute can cut them off. Fixed GND
  ties now in `fixed_routes.py`: C70.2 (via at x 67.1, logic side of the barrier), D52.1, C14.2, C15.2, R1.2.
  (b) `pf_land.py` now keeps the GND drop lists of earlier runs (the export no longer sees that copper, so a second
  reroute put the harvest GND copper back on turned pads: 59 DRC errors) and drops an old router GND stub only when
  the new run ties the same pad again (two vias 0.05 mm apart otherwise).
- **Noted, not changed:** on SW_SUPPLY, R49 (10 k, SW_SENSE divider) is tapped at J5.5, 3.7 mm ahead of D54. A surge
  into that branch meets 10 kΩ, then C21 470 nF and D24, so the stub carries microamps; the report keeps showing it.
  Move R49's tap behind D54 if a later layout pass touches that corner.
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

**2026-11-17: PWM rating and showcase.** Decision 221 (confirmed by 234): a PWM-dimmed channel is
rated 4 A on 12 V and 3.5 A on 24 V at 100 Hz (3 A at 200 Hz), from the datasheet switching energy and slew added to
the heat budget (design-notes §4 "PWM dimming"); bring-up.md §9.4 measures it. The README carries a preview render
(`docs/images/pdm-4ch-preview.jpg`, KiCad raytrace). A showcase page with a rotatable 3D model of the board (for the
Signal K community) lives outside the repo as a claude.ai artifact; it is rebuilt from a KiCad GLB export
(`kicad-cli pcb export glb --no-dnp --subst-models --include-tracks --include-pads --include-zones --include-silkscreen
--include-soldermask`), so a layout change needs a fresh export to show there.

## Next

1. **Do not run *Update Symbols from Library*, and do not save the schematics from KiCad 10 by hand** (2026-11-08):
   a KiCad 10 save with a symbol update reset every Value/Footprint/LCSC field, merged GND_CAN into GND and renamed
   SW_BOOT1/SW_RESET1, FL30, JP30. That copy is kept on the local branch `backup/kicad10-resave-2026-11-08`, never
   merged. Schematic changes go through `tools/ksch.py` (agents), checked by ERC and the netlist compare; a KiCad 10
   format upgrade, if wanted, is a scripted package of its own with a netlist-identical check.
2. Silkscreen: done (decision 224). After any part move or reroute run `scripts/silk.py` again and check the DRC.
3. Decision 235 (RIS hardware cover): **done** (decision 238, C844867; land checked 2026-11-21).
4. `/validate pdm-4ch` on the PCB: done 2026-11-18, V1 fixed (decision 225). Footprints, CPL and licence done
   (2026-11-21/22). **Next step: quote and order** (fixture-fee check, connector sets and their stock, decision 127).
   No PCB fix is open before the order; open only on condition: E24 (below) and FL1 (before it is ever fitted).
   Earlier notes for this step: Points to check first:
   decision 217 (CAN barrier keep-out at the rule minimum), decision 218 (VS-In2 gate), the 0.2 mm VBUS and
   Net-(D3-A) necks at J3 (decision 219), the fill keep-outs that removed GND slivers on F.Cu/B.Cu/In2.
   `/emc pdm-4ch` on the layout is done (2026-11-17, `docs/reviews/2026-11-17-emc-pdm-4ch.md`): 0 CRITICAL,
   0 MAJOR, 3 MINOR, all layout-only, two-way, no part change. E22 and E23 are fixed and E25 is in the build
   (decision 223, entry at the top). Left:
   - **E24:** R10 pad 1 (FB) is 0.7 mm from the SW pad of DNP R44, and a 6 mm dead-end SW spur to R44/C20 runs
     1.6 mm from the FB track. No change now; added to the T-0161 scan below. Move R9/R10 or R44/C20 only if the
     scan shows jitter.
   - Not a finding, noted: the VBAT_FL track at x = 40.25 (U30 pin 5 to the pour) is 0.3 mm from GND fill for
     about 4 mm, beyond rule 4's 0.6 mm pad zone. The BTT6050 slew is now read from the datasheet (0.3/0.8/1.4 V/µs),
     which closes the "slew UNVERIFIED" item for pdm-4ch.
5. CPL rotation and origin are now corrected by `CPL_FIX` in `tools/jlc_package.py` (2026-11-22, 24 parts: U3, U5,
   U11–U14, U30, Q3–Q6, Q30, D9, D12–D15, D102–D402, U1, J3, U6); the package report lists what JLCPCB's placement
   preview should show. A part swap or a new footprint needs a `tools/fp_check` run and a `CPL_FIX` entry. The JLCPCB package (Gerber zip, BOM, CPL) is built by
   `python3 tools/jlc_package.py pdm-4ch` into `fab/` behind a DRC gate; see `fab/README.md` for the quote settings.
   The 2026-11-17 package is for quoting only and predates decisions 223–225 (D50, R19, C50, D24 moved; copper and
   silkscreen changed): rebuild it before quoting again.
6. Before fitting D103–D403 read the demagnetisation note in design-notes §8.2. (`CP_Elec_8x10`, `C_1206` and
   PESD2CAN pin 3: checked 2026-11-21.)
7. Layout rules: `docs/ARCHITECTURE.md`, "PCB layout rules". Layout work is interactive (decision 216); a new
   signal routing is `pf_export.py` → `pf_route.py` → `pf_land.py` → `build_routing.sh` in `scripts/`.

History of the schematic fix rounds and of the layout up to 2026-11-16: `STATUS-history.md` beside this file.

## Prototype test list

The full bring-up and validation plan, in order, with pass criteria and a record sheet, is `bring-up.md` beside this
file (2026-11-17). It includes every test below. Open owner choice in it: cutting JP1 on one board to get the
"3.3 V rail down" case of T-0042 (section 7.3).

- **Decision 127 – connector fit (moved from decision 98):** on the first assembled boards check that the J11, J5 and J4 plugs cannot go in reversed; whether the J4 plug enters the J5 socket (labels are on the silkscreen either way); the height across the rail (part height + pin length + 1 mm; J10 expected 34.8 mm; recorded, not a pass/fail limit); the J10 wire-entry side and M4 screw access at 36 mm pitch; reach of mated plugs and cable bend past the edge. Findings go into the next revision.
- **T-0118 / decision 81 – PTC hard short (mandatory before installation):** from a 30 V battery-like supply (low source
  impedance), short J5.5 to GND (behind F4/R56), then behind F1 (D1/D2 node) and behind F3 (D10/FB2 node). Scope the
  current; afterwards inspect R54–R56 and F1/F3/F4 (cracks, discoloration, resistance). Pass before installation
  (design-notes §8.3).
  T-0161: make the short behind F1 with **JP1 fitted** (a short at C1 also puts JP1 in the path) and, if L2 is ever fitted, repeat it.
- **T-0161 / decision 28 – buck input filter (pre-compliance scan):** conducted emission on the battery input with JP1 fitted. If the buck's 1.1 MHz or PFM components need it: cut JP1, fit L2 (start 8.2 µH C96963) **together with** C22 2.2 µF + R73 10 Ω (3.3–4.7 Ω 1206 if the ring at 33–57 kHz is not damped enough). Then scope U3 VIN at light load (PFM) and during a 28.8 V hot-plug; the peak must stay ≤ 65 V (design-notes §8.3). EMC E24 (2026-11-17): also scope U3 FB and +3V3 at light load for jitter or pulse bunching.
- **T-0042 / Q-0034 – switch-path margin:** measure IN − device GND (U11–U14 pin IN vs the channel's ground network) at
  SWIN = 10.5 V with the channel on, once with the 3.3 V rail removed and once with it present. Repeat at a 10.5 V battery
  with D55's drop (SWIN ≈ 9.8–10.1 V). Pass: ≥ 2.0 V (VIN(H) min). If short, the planned fix is **RIN R101/R201/R301/R401 →
  4.7 kΩ**. The divider on the shared sheet stays an owner decision. Calculation in design-notes §3.
- T-0129 / Q-0067 - negative pulse on J10 with VS charged and the source short-circuit current within 31 A: scope Q30 VDS and VS (also VBAT_IN); expect VDS about 60 V or less and VS no lower than about -4 V; inspect C31 afterwards.
- T-0012: check the hardware switch path with a bouncing contact (no output chatter, τ ≈ 1.5 ms). Measure the ON/OFF
  switch voltage (≈ 8 V at the switch, ≈ 8.5 V at the battery).

## Pre-order checklist (T-0065)

**2026-11-21: the footprint, polarity, CPL-rotation and stock items below were checked by script**
(`docs/reviews/2026-11-21-footprints-pdm-4ch.md`): all fitted lands pass; T-0118, T-0121, T-0143, T-0160, the
decision 238 land, `CP_Elec_8x10`/`C_1206`, `D_SOD-882`/`TO-252-2`/`L_0805`, U5 and PESD2CAN pin 3 are closed. CPL
corrections applied 2026-11-22 (`CPL_FIX` in `tools/jlc_package.py`, package rebuilt, DRC gate pass; EasyEDA pads
placed by the new CPL land within 0.4 mm of our pads on all 142 checked parts, Q30 leads 0.00 mm). Open from it: FL1
footprint before FL1 is ever fitted (T-0067).

- Decision 150: the cost reviews still price pdm-4ch as 2 layers; the next `/cost` prices 4 layers (owner's quote €43.95 for 5 boards, 100 × 75 mm).
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
- T-0107/T-0120: C30 and C104–C404 use C170101 2.2 µF instead of C13832 1 µF. pdm-4ch no longer carries C13832, so its loading fee is gone; this pays on short runs only. Revisit the choice if runs grow past about 12 boards (owner ruling Q-0063). RIS is now 2 × C844867 per channel (decision 238; was 2 × C4410).
- T-0121: check the KiCad footprints `Infineon_PG-HSOF-8-1` (Q30, pads 1 G / 2 S / 3 D) and `ESP32-PDM:TI_DDF0008A` (U30, since 2026-11-09; was `TSOT-23-8`; TI DDF land
  1.05 × 0.45 mm pads, 2.6 mm column pitch) against the JLCPCB footprints of C5464765 and C5219203 (U30 is the LM74502H-Q1 since decision 222). Recheck stock
  (C5464765 2016 on 2026-11-07, C5219203 1995 on 2026-11-17).
- T-0143: check KiCad `D_SMC` (D31; pads 2.5 × 3.3 mm, gap 4.3 mm) against the JLCPCB footprint of C42371557 (`SMC_L7.2-W5.8-LS8.1-BI`, pads 3 × 3.8 mm, gap 4.6 mm; hongjiacheng suggested land: pads 3.03 × 3.82 mm, gap at most 3.84 mm) and recheck its stock (10271 on 2026-11-04).
- Stock 2026-11-17 (`fab/README.md`): U30 LM74500-Q1 C5219210 was out of stock everywhere; **U30 is now LM74502H-Q1
  C5219203** (1995 in stock, decision 222: pin 7 OV → GND, pin 8 SRC → VBAT_FL; pad 5 got its own VBAT_FL via and pad 7 a
  GND via on the PCB; DRC 0 errors / 0 unconnected / parity 0). SMAJ30CA C19077548 has 172 pcs (20 needed). First order (5 PCBs, 2 assembled, Standard PCBA, 4 layers): 205.46 USD at JLCPCB, 210.46 USD with connector sets, 226.88 USD with the fixture fee (cost review 2026-11-21).
- Decision 238: check the KiCad `R_1206_3216Metric` land (G 1.80, Z 4.05, X 1.75 mm) against the JLCPCB footprint of
  C844867 (Vishay land G 1.50, Z 3.60, X 1.80 mm, accepted on the datasheet) and recheck its stock (138848 on 2026-11-21).
- T-0021: BOM lines without `LCSC` are now only H1–H4 and the DNP positions.
- T-0160: check the CPL rotation of D7/D8 (C2286; JLCPCB footprint pad 1 = anode, KiCad pad 1 = cathode, cathode on the same side) and the KiCad `LED_0603_1608Metric` pads against `LED-SMD_L1.6-W0.8-R-RD`.
- Decision 220 (licence): **done 2026-11-22**: "CERN-OHL-S v2" and `github.com/plektra/ESP32-PDM` on the bottom
  silkscreen and in the title blocks of the five sheets and the PCB.
- RoHS/REACH (`docs/reviews/2026-11-18-rohs-reach-pdm-4ch.md`): hand-solder J4/J5/J10/J11 with lead-free solder.
  Before any sale (not for the prototypes): maker declarations
  for the connectors and the small makers (R3–R5), REACH Art. 33 note + SCIP entry for lead in Q30 AGM601LL (R1) and U6 (R2) and,
  if the makers confirm it, in the Kefa connectors and the hongjiacheng diodes. Re-run the check after a BOM change.
  Requests are drafted in `docs/reviews/2026-11-18-rohs-reach-requests-pdm-4ch.md` for the owner to send through LCSC (the one to ST is optional, R2 is closed).

## For /system

- Mounting decided (decision 123). After layout: the printed DIN mount and enclosure as OpenSCAD files (`/system mechanical`), with the cable entry of decision 237 (bottom-face glands and clamp comb, M12 5-pin CAN panel connector to J4, cable-tie anchors on the DIN mount). Open there: the M12 part (plastic body or isolated metal, shield pin open) and J4's four poles mapped to its pins. Candidate (2026-11-21): the owner's own Chinese M12 panel connectors, 5-pin A-coded, male pins (the usual NMEA 2000 device side); still to check: continuity of every pin, pin 1 included, to the metal body (owner measuring; pin 1 left unwired if tied to the body, decision 28), mounting thread and front/back mount (sets the wall hole), lead type and colours (map by continuity, not colour).
