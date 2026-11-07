# pdm-4ch status

Updated: 2026-11-07 (decision 121 J10 fixed terminal)

**2026-11-07 (decision 121, /system, `pdm-4ch` root sheet only):** J10 is now the fixed screw terminal **KF135T-10.16-2P C475108** (65 A UL / 57 A IEC, 10 mm², M4) for the prototype, because every flange-locking socket that fits is out of stock or thin at LCSC (C577772 0, C6394053 4). New footprint `ESP32-PDM:Kefa_KF135T-10.16-2P` from the Kefa drawing (`docs/part-facts/C475108.md`, design-notes connectors section). J10 fields only: Value, Footprint, Description, LCSC; `LCSC_Plug` removed. ERC 0 errors, 5 warnings (unchanged); netlist: 169 nets identical, 227 parts, only J10 fields differ; unique parts unchanged (C577772 out, C475108 in). No output changed, so the heat budget was not rerun. The T-0158 cross-board mis-plug question closes (no pdm-4ch battery plug). **A competent person reviews the battery path (J10, Q30/U30, D31) before installation.**

**2026-11-07 (decision 120, /system, documents only):** the owner's Q-0068/Q-0069 ruling is recorded as a decision: J10 stays C577772 + C577752, bought from any seller (header must read KF2EDGSRM-7.62), and the decision 98 sample, layout and order wait if none is available. No substitute socket. Live stock 2026-11-07: socket 0, plug 63. ARCHITECTURE Mechanics now has a separate pdm-4ch J10 row. No schematic change.
**2026-11-07 (T-0185: "For /system" sweep, unattended, documents only; its J10 row superseded by decision 121):** ARCHITECTURE now names Q30 AGM601LL C5464765, D7/R59, D8/R67 and J6 in the root row, the BTT6010 option as not on this version (Boards row, budget row, decision 103), a pdm-4ch J10 row C577772 + C577752 (decision 104) and the Q30 figures with the 16 A input limit in the supply-path row. The T-0158/T-0171 done-notes left this list. No schematic change. Report: `docs/reviews/2026-11-07-fix-sync-T-0185.md`.

**2026-11-07 (T-0179: T-0166, T-0168, T-0177, owner rulings Q-0068/Q-0069, unattended, documents only; J10 part and plug marking superseded by decision 121):** C577772 + C577752 stay (no design change); buy C577772 from any seller, marking KF2EDGSRM-7.62 (flange header); no C577767, C7422678 or other socket; the order waits if none can be bought. The J10 battery plug fits the pdm-hc2 J11 output socket: mark the battery plug and check it before power-up (pre-order checklist, README). No schematic, footprint or BOM change. Report: `docs/reviews/2026-11-07-fix-shared-T-0179.md`.

**2026-11-07 (T-0171: T-0166, T-0167, T-0169, unattended, documents only):** C577772 (J10 socket) has stock 0, minimum order 18. No design change. Two possible substitutes were checked: C577767 (Kefa KF2EDGSR-7.62-2P) and C7422678 (DORABO DB3ERC-7.62-2P-GN). Both match the J10 pad grid and hole size and are rated 30 A UL / 32 A IEC. Neither has the flange header that the C577752 plug's ear screws need, and neither drawing shows that the plug locks, so both fail. The only fallback is C577772 from another seller (pre-order checklist). Changing to another socket would amend decisions 98/104, so that question goes to the owner. T-0167 (the T-0158 saving, about 4.8 $ per board at 5) is confirmed and needs no action. No schematic, footprint or BOM change. Report: `docs/reviews/2026-11-07-fix-pdm-4ch-T-0171.md`.

**2026-11-07 (T-0161: T-0153, owner ruling 2026-11-06, unattended, shared – `power-usb`, same on both boards):** buck input filter position. Net-(D2-K) is split: D2.K → **JP1** (copper bridge, bridged solder-jumper footprint, no part) ‖ **L2** (DNP, SWPA6045S8R2MT C96963 footprint, example 8.2 µH) → C1/C19/U3. D3 (USB) stays on the U3 side, so USB-only input is unchanged (3.74 V at 0.40 A, decision 87). Damping option **C22 2.2 µF C170101 + R73 10 Ω C17903 across C1, both DNP**. A 0 Ω chip part was not used: neither C17168 nor C21189 publishes pulse data for the ≈ 86 A / ≤ 9.6 A²s F1 trip. The 0.6 mm copper bar carries 87 A²s at 2 oz (Onderdonk). With JP1 fitted, the buck input changes only by ≈ 0.2 mΩ. L2 must be fitted only together with C22/R73: undamped, the filter peak (≤ 21 Ω) is only 1.4× below the buck's 29 Ω negative input impedance at a cranking dip, and a surge step can push U3 VIN to ≈ 64 V (65 V recommended). F1, R54 and their ratings are unchanged. ERC 0 errors, 5 warnings (unchanged); +4 DNP parts, unique +0. Design-notes §8.3. **A competent person reviews F1 and R54 before installation.** Report: `docs/reviews/2026-11-07-fix-shared-T-0161.md`.

**2026-11-07 (T-0160: T-0150, T-0151, T-0152, owner rulings 2026-11-06, unattended, shared – controller part of the root sheet, same on both boards except J6 pins 4–6):** sign-of-life LEDs and service pads. **D8 + R67** power LED +3V3 → GND; **D7 + R59** status LED IO13 → GND (high = on, off while IO13 is undriven). LEDs KT-0603R red 0603 C2286 (basic, the one new line), resistors 2.2 k C25879 (on the BOM): ≈ 0.7 mA each. D8 draws continuously, also in Eco/Sleep (decision 13), ≈ 2.3 mW from 3.3 V. **J6** unfitted `PinHeader_1x08_P2.54mm_Vertical`, DNP, no BOM line: 1 GND, 2 TXD0, 3 RXD0, 4 IO35, 5 IO36, 6 IO37, 7 IO42, 8 +3V3. Pin checks: none strapping, none used in the N8 module. CAN TX/RX LEDs left out (an LED to GND on TXD sits at the 2 V VIH limit with R70; the active-low version would light too briefly to see). Pin map (IO13, IO34–IO37, IO42, TXD0/RXD0) and the controller power row updated in ARCHITECTURE. ERC 0 errors, 5 warnings (unchanged); netlist differs only in U1 pins 17, 31–33, 38–40 and the new parts. 223 parts (+5, J6 DNP), 60 unique (+1). Design-notes §8.7. Report: `docs/reviews/2026-11-07-fix-shared-T-0160.md`.

**2026-11-07 (T-0159: T-0149, owner ruling, decisions 99 and 105, unattended, shared – same on both boards):** near-duplicate BOM lines merged; values and nets unchanged. C2 → C307331 0402, C12 → C15849 0603, R9 → C36871 0402, R10 → C25768 0402. **C13 stays on C28323:** C15849 keeps only 0.10 µF at 29 V and 0.31 µF at 12 V (Samsung's simulation), below the L78M05's 0.33 µF, while C28323 keeps 0.42 µF worst case at 29 V. C14663, C52923, C31850, C23231 are gone; C36871 is new on this board because R9 is on the shared sheet, so net 3 lines fewer: 59 unique (−3), 4.59 USD per order. **Layout:** C2, R9, R10 are 0402, C12 is 0603 (was 0402), C13 stays 0805. ERC 0 errors, 5 warnings (unchanged). 3.3 V setpoint tolerance unchanged (±1 %, ±100 ppm/°C). Design-notes §8.3. Report: `docs/reviews/2026-11-07-fix-shared-T-0159.md`.

**2026-11-06 (cost session, no schematic change):** `pdm-4ch` is the whole first order and the MVP: 5 bare PCBs, 2 assembled, 2 oz, Standard PCBA, about 218 $ with connector sets (decisions 99, 101, 102; `docs/reviews/2026-11-05-cost-system.md`). First version is 16 A only, all BTT6050 (decision 103). T-0148 is done (T-0158, below). **Queued, not done:** T-0149 part merges; T-0150 status LEDs; T-0151 spare GPIO pads; T-0152 serial pads; T-0153 buck filter position.

**2026-11-07 (T-0158: T-0148, owner ruling, decisions 103 and 104, unattended, `pdm-4ch` root sheet only; J10 part superseded by decision 121):** the board input is now 16 A. **J10** is KF2EDGSRM-7.62-2P C577772 + plug C577752 (30 A UL / 32 A IEC), footprint `ESP32-PDM:Kefa_KF2EDGSRM-7.62-2P`, pin 1 VBAT_IN, pin 2 GND; the footprint passes against the drawing and is unchanged (design-notes §7). **Q30** is AGM601LL C5464765 (60 V, VGS ±20 V, 1.6 mΩ max, TOLL, same pins, footprint unchanged, 0.85 USD instead of about 3.55 USD); the symbol stays `ESP32-PDM:IPT007N06N`. C32, U30, D31, D30, C30, FL30 and JP30 are unchanged. **Heat at 40 °C:** 4 × 4 A inside 45.8 °C, Tj 102 °C (`--r-path 0.0069`); 4.5 A OVER. Q30 at 16 A: Tj 66 °C at 40 K/W, 80 °C at 62 K/W; AGM's 50 K/W has no stated copper area, so it is not relied on. **Copper rule:** ≥ 2 cm² of 2 oz VS copper on the drain tab replaces the 6 cm² of decisions 90 and 95. Decision 96's limits and invariant 4 hold: VDS 59.4 V and VS −4.0 V at 31 A do not depend on the FET. ERC 0 errors, 5 warnings (unchanged); netlist differs only in J10 and Q30 fields; 218 parts (+0), 62 unique (+0). **C577772 stock is 0 today (minimum order 18), so the set cannot be bought until restocked.** BTT6010 stays out of this version: four at 8 A would take Q30 to about 179 °C. **A competent person reviews the battery path (J10, Q30/U30, D31) before installation.** Older entries that give 32 A or IPT007N06N are history. Details and failure modes: design-notes §7, §8.6. Report: `docs/reviews/2026-11-07-fix-pdm-4ch-T-0158.md`.

**Where it stands:** schematic complete (scripted edits), ERC: 5 `lib_symbol_mismatch` notices only (since T-0066). Netlist checked
after every edit. No PCB. Decisions 1–7, 9–14, 17, 18 apply. Panel connector J5 and the pin map changed on
2026-10-30 (decisions 17, 18): SW_SUPPLY on J5.5, MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9,
channel-4 drive moved to IO11.

**2026-11-04 (T-0147: "For /system" sweep, unattended, documents only):** ARCHITECTURE root row names D31 SMDJ40CA C42371557 across Q30 (VS to `VBAT_FL`, decisions 92, 96). The T-0064 and T-0065 cost entries left this list: C13832 and C107198 are on neither board, C1 is C170101, and the record stays in design-notes §8.1 and §8.3. No schematic change. Report: `docs/reviews/2026-11-04-fix-sync-T-0147.md`.

**2026-11-05 (decision 98, /system mechanical, same on both boards except J11):** all four connectors are keyed plugs on right-angle sockets: J10 C6394053 + C6394029, J11 C441238 + C440882, J5 C26895 + C26865, J4 C7245 + C7244. Five new footprints in `lib/ESP32-PDM.pretty` drawn from the maker drawings. Fields only: no net changed; pads match pins; ERC 0 errors, 5 warnings (unchanged). **For the PCB:** mating faces at the board edge; board depth about 65 mm; J10 reaches 34 mm in from the edge; TVSs at the socket pins (invariant 4); keep the J10/J11 rows on one edge, J5/J4 on the other.

**2026-11-05 (decision 97, /system mechanical, root sheet, same on both boards):** the board mounts on a plastic DIN carrier (edge-on, about 36 mm per unit, enclosure by the installer) or in a printed enclosure. H1/H2 had no footprint: H1–H4 are now four `MountingHole_3.2mm_M3` non-plated holes. ERC 0 errors, 5 warnings (unchanged); netlist adds H3/H4 and footprints only. **For the PCB:** holes at the corners with copper keep-out, no copper reachable by carrier or screws (invariant 6), and J10 height sets the pitch.

**2026-11-04 (T-0143: T-0129, owner ruling Q-0067, unattended, `pdm-4ch` root sheet only):** **D31 SMDJ40CA C42371557** (preferred, 0.22 USD, no loading fee; `Diode_SMD:D_SMC`, bidirectional, as D30) fitted across Q30, VS to VBAT_FL, so a negative transient with VS charged no longer avalanches Q30. **Residual risk accepted by the owner:** VDS 59.4 V at 31 A (25 °C, source short-circuit current ≤ 31 A; about 60.4 V with the TVS at 47 °C); VS ≥ 0 V up to about 20.3 A, down to about −4.0 V at 31 A, so C31, which has no reverse rating, is briefly reverse-biased. Unverified whether such spikes occur (T-0130); prototype check added below. Steady reversal ≤ 28 V: D31 does not conduct. ERC 0 errors, 5 warnings (unchanged); netlist differs only in D31. 216 parts (+1), 62 unique (+1). Heat unchanged at 40 °C. Details and failure modes: design-notes §8.6. **A competent person reviews this circuit before installation** (F4 feeds navigation lights and bilge forced run). Needs the KiCad tidy of D31. Report: `docs/reviews/2026-11-04-fix-pdm-4ch-T-0143.md`.

**2026-11-04 (decision 95, /system, no schematic change):** board input limits are 32 A (`pdm-4ch`) and 36 A (`pdm-hc2`) instead of ≈ 40 / 50 A; they set J10, its GND pole and the supply copper in `/system mechanical`. Q30 is about 86 °C at 32 A with the 6 cm² copper rule kept; the cheaper AGM601LL still fails at about 179 °C. Older entries that say 40 A are history.

**2026-11-04 (decision 93, /system, shared `analog_sw` + root sheet, same on both boards):** SW_SUPPLY sense added: R49 10 k 1206 → SW_SENSE, R57 4.7 k, D24 BZT52C3V3, C21 470 nF, R58 10 k (root sheet) → IO12 as a digital input. It replaces the decision 21 divider, which could not work on IO12 (design-notes §5). +5 parts, +0 unique. ERC 0 errors, 5 warnings (unchanged); netlist differs only in those parts and U1 pad 16. Needs the KiCad tidy of the new parts' labels.

**2026-11-04 (T-0141: "For /system" sweep, unattended, documents only):** ARCHITECTURE root row (C30 2.2 µF C170101, blocker Q30/U30/C32 on pdm-4ch only) and supply-path budget updated; `tools/heat_budget.py --p-other` default 2.2 → 2.3 W (4 × 4 A Tj ≈ 101 °C, unchanged). No schematic change. Report: `docs/reviews/2026-11-04-fix-sync-T-0141.md`.

**2026-11-04 (T-0137, superseded by T-0143 above: T-0129, owner ruling Q-0066, unattended, no schematic change):** the TVS across Q30 is **not fitted yet; back with the owner**. Stop (iii) of the brief applies: every part that keeps Q30 VDS below 60 V at the 31 A bounding current with an adequate pulse rating also lets VS fall below 0 V at that current. Example: SMDJ40CA C42371557 (preferred, same SMC package), VDS 59.4 V at 31 A, VS +3.1 V at the 12 A textbook pulse but −4.0 V at 31 A. C31 has no reverse rating (decision 82). SMCJ30CA already on the BOM is the worst for this: −15.1 V at 31 A and still −8.0 V at 12 A. §8.6 (b) and (c) stay unchanged until the owner chooses. Numbers per candidate and the question: `docs/reviews/2026-11-04-fix-pdm-4ch-T-0137.md`. Facts added for seven TVS parts in `docs/part-facts/`.

**2026-11-04 (T-0132: T-0126 cost lever L1, T-0129/EMC E18, unattended, documents only):** AGM601LL (C5464765) as a cheaper Q30 **fails** the heat check and was not fitted: its 1.25 mΩ is typical, 1.6 mΩ max (≈ 2.9 mΩ at 150 °C); with RthJA 40–50 K/W Q30 has no stable Tj below 175 °C at 40 A (IPT007N06N: 124 °C by the same method). Q30 stays IPT007N06N C122552; no schematic change, no refs. Details: design-notes §8.6 Cost. T-0129 (the §8.6 (b) "VDS ≤ 48.4 V" correction) is **blocked for the owner**: in a negative transient with VS charged, Q30 avalanches at about 60–63 V and absorbs about 80–115 mJ. EAS 1100 mJ is for Tj(start) 25 °C only. At the 40 A hot case (Tj ≈ 122 °C) the IAS–tAV curve (Diagram 13) leaves only ≈ 1–2× margin, depending on C31 ESR, which is not bounded. §8.6 (b) is unchanged until the owner rules. Report: `docs/reviews/2026-11-03-fix-pdm-4ch-T-0132.md`.

**2026-11-03 (T-0121: T-0088/EMC E16, owner ruling Q-0054, unattended, `pdm-4ch` root sheet only):** reverse-battery blocker on VS in front of the bulk capacitors. New net `VBAT_FL` between FL30/JP30 and **Q30 IPT007N06N** (C122552, 60 V, 0.75 mΩ max, TOLL; source VBAT_FL, drain VS), driven by **U30 TI LM74500-Q1** (C5219210, SOT-23-THIN-8; SOURCE+EN on VBAT_FL = always on without MCU, GATE → Q30) with **C32** 1 µF/50 V (C15849, basic, on the BOM) at VCAP. D30/C30 stay on VBAT_IN at J10; C31, C104–C404, U11–U14, F1, F4, R60 sit behind Q30. The LM74500 does not block reverse current: Q30 is fully on both ways, so OUT → body diode → VS → D30 (invariant 4) is kept, no TVS on VS. Reverse battery up to 30 V: VS stays unpowered, no time limit. Heat at 40 °C (`--r-path 0.00505`): 4 × 4 A Tj 101 → 102 °C, mix 8 A/4 A unchanged (90/102 °C), Q30 itself 1.8 W / Tj 122 °C at 40 A with ≥ 6 cm² 2 oz drain copper. New symbols `ESP32-PDM:IPT007N06N` and `ESP32-PDM:LM74500-Q1` in `lib/`. ERC 0 errors, 5 warnings (unchanged); netlist differs only in Q30/U30/C32 and FL30.1/JP30.1 (now VBAT_FL). 210 parts (+3), 61 unique (+2 extended). README and design-notes §8/§8.1/§8.6 updated, failure-mode note in §8.6: **a competent person reviews the blocker before installation** (panel switches for navigation lights and bilge forced run depend on Q30). Report: `docs/reviews/2026-11-03-fix-pdm-4ch-T-0121.md`.

**2026-11-03 (T-0120: T-0099/T-0115, owner Q-0063/Q-0064, unattended, `channel`):** VS-tab capacitors C104–C404 are now 2.2 µF/100 V X7R 1206 C170101 (Samsung CL31B225KCHSNNE, already on the BOM as C1/C30) instead of 1 µF C13832. Same footprint C_1206_3216Metric. Decision 26 amended by the owner to "≥ 1 µF/100 V (2.2 µF C170101)"; this supersedes auto decision 44. No C13832 is left on pdm-4ch. ERC 0 errors, 5 warnings (unchanged); netlist differs only in C104–C404. 207 parts (+0), 59 unique (−1). Details: design-notes §8.1, `docs/reviews/2026-11-03-fix-pdm-4ch-T-0120.md`.

**2026-11-03 (T-0119: T-0096/T-0090, owner Q-0061/Q-0062, decision 83, unattended, shared – `power-usb`, same on both boards):** USB shield capacitor C18 is now 1 nF/2 kV X7R 1206 C9196 (basic, already on the BOM) instead of 4.7 nF/1 kV C107198 (extended). Footprint, R13 1 MΩ and R14 0 Ω DNP unchanged. Shield RC 1 MΩ ‖ 1 nF, corner ≈ 160 Hz (was 34 Hz). ERC 0 errors, 5 warnings (unchanged); netlist differs only in C18 value/LCSC. 207 parts (+0), 60 unique (−1). Details: design-notes §8.3, `docs/reviews/2026-11-03-fix-shared-T-0119.md`.

**2026-11-03 (T-0118: T-0018, Q-0060/decision 81, unattended, shared – `power-usb`, `can`, `analog_sw`, same on both
boards):** F1–F4 are now TECHFUSE mSMD050-60V C70113 (60 V, I_max 100 A, I_hold 0.50 A, R1max 1.0 Ω, 1812; F2 moved from
`Fuse_0805_2012Metric` to `Fuse_1812_4532Metric`). New 0.2 Ω 2 W alloy 2512 FOJAN FRM252WJR200TK C7420022 in series on the
protected side: R54 (F1 → D1/D2), R55 (F3 → D10/FB2), R56 (F4 → D55); F2 has none. Hard short behind a resistor: 30 V /
0.35 Ω ≈ 86 A < 100 A. Checks: switch path ≈ 2.03 V ≥ 2.0 V at a 10.5 V battery via D55 (F4 + R56 1.2 Ω, less than the
old 1.4 Ω); L78M05 input ≈ 8.5 V at NET-S 9 V; buck input −0.22 V at 0.18 A; USB-only at the 0.40 A peak 3.74 V typ (was
3.80 V; below the 4 V minimum with either part, same result in every corner). ERC 0 errors, 5 warnings (unchanged);
netlist differs only in F1–F4 and R54–R56. +3 parts, +0 unique (+C70113 +C7420022 −C19078719 −C269104). Heat budget: no
output change, losses in mW. Details: design-notes §8.3, `docs/reviews/2026-11-03-fix-shared-T-0118.md`.

**2026-11-03 (T-0107: T-0098, T-0099, unattended, shared – cost levers L7/L8):** RIS is now two 1 kΩ 1206 0.25 W in parallel = 500 Ω per channel: R103 ‖ R107, R203 ‖ R207, R303 ‖ R307, R403 ‖ R407 (C4410, basic). The extended 680 Ω C17975 is no longer used. IS at full load is ≤ 1.63 V (BTT6050 4.5 A, kILIS min) and ≤ 1.27 V (BTT6010 9 A), below the 2.9 V ADC range and the 3.3 V clamp. **Firmware scale constant: RIS 500 Ω (≈ 0.33 V/A for the BTT6050).** C30 (root, battery input J10, same on both boards) is now 2.2 µF/100 V X7R 1206 C170101 (the part already used as C1; decision 26 allows 1–2.2 µF at J10). C104–C404 are unchanged: 1 µF C13832, because confirmed decision 26 names them (that is an owner question). The C18 swap (T-0096) is blocked too: confirmed decision 31 names 4.7 nF, so it goes to the owner. ERC 0 errors, 5 warnings (unchanged). The netlist differs only in the refs above. +4 parts, +0 unique. Extended types 19 → 18 (−C17975). Details: design-notes §6.1 and §8.1, `docs/reviews/2026-11-03-fix-shared-T-0107.md`.


**2026-11-03 (T-0105: T-0046, Q-0048/decision 74, unattended, shared `analog_sw` – same on both boards):** the switch
loads R3/R4/R7/R8 (4.7 k) are now two 2 k 1206 in series each: R3+R45, R4+R46, R7+R47, R8+R48 (C17944, basic, 4.0 k):
0.11 W per part at 30 V (44 %, was 77 %), 0.29 W per part in a 48 V clamp (inside the 5 s overload rating). Thresholds
and the 10.5 V margin unchanged (≤ 2 mV at IN); leakage rejection slightly better; p_other ≈ 2.3 W → Tj ≈ 101 °C at
4 × 4 A, the 4 A rating stands. ERC 0 errors, 5 warnings (unchanged); netlist differs only in those eight resistors and
four new mid-point nets. +4 parts, +0 unique. Details: design-notes §3, §4, §5.

**2026-11-03 (T-0104: T-0018, Q-0047/decision 73, unattended, shared – documents only):** the 100 A PTCs pass the
datasheet check (TECHFUSE mSMD050-60V C70113 and JDT ASMD1812-050-60V C427396: 60 V / I_max 100 A, I_hold 0.50 A, 1812
body as now; C70113 preferred, R1max 1.0 Ω). The series resistor (0.20 Ω → 86 A, ≤ 1.9 J in ≈ 1.3 ms, ≈ 1.5 kW peak) is
**not shown to pass**: no basic or cheap 0.1–0.22 Ω resistor publishes a ms pulse rating (5 s overload tests only).
Following the ruling, nothing was changed (F1/F3/F4 stay 1812L050/60GR, F2 stays SMD0805B050TF) and the question is
back with the owner. Details: design-notes §8.3, `docs/reviews/2026-11-03-fix-shared-T-0104.md`.

**2026-11-03 (T-0085, unattended, scope sync – documents only):** ARCHITECTURE `can` row (CA-IS3050G, L78M05ABDT, LEN)
and root row (C30/C31, FL30/JP30, VBAT_IN) brought in line with the schematic; `tools/heat_budget.py --p-other`
default 0.6 → 2.2 W (design-notes §4). The 32 V full scale is already recorded (decision 38). No schematic change.

**2026-11-03 (T-0078: T-0076, Q-0052, unattended, shared lib + `can` – same on both boards):** U5 CA-IS3050G symbol pin
numbers corrected to the datasheet (v1.10 Table 6-1): pin 2 RXD, pin 3 TXD (they were swapped, the CA-IS3052G order).
Renumbered only – no wire moved: /IO17 (U1.21, R70) → U5.3 TXD, /IO18 (U1.22) → U5.2 RXD. Pin map unchanged. ERC
unchanged (5 `lib_symbol_mismatch`, none on U5); the netlist differs only in those two U5 pins. Details: design-notes §8.5.

**2026-11-03 (T-0073: T-0021/T-0031/T-0033/T-0043/T-0051/T-0060, unattended, shared – same on both boards):** `LCSC` fields added (cost report C1, each checked against value, package and net voltage): C2 C14663, C4/C6 C15849, C5 C19666, C7/C9 C28233, C8 C45783, C10/C11 C307331, C12 C52923, D12–D15 BAT54C C22466350 (preferred; pinout 1/2 anodes, 3 common cathode), R1/R2/R5/R6 C25879, R11/R12 C25905, R15–R17/R21/R24/R27 C25744 – all basic except the BAT54C, no new unique extended part. C13 and FB1/FB2 already had codes from T-0065. R1/R2 and the NTC TH1 (C52155402) stay (Q-0025, Q-0024). VBAT full scale ≈ 32 V and the IO3 strap rule are in design-notes §2.

**2026-11-02 (T-0068, Q-0006/Q-0040/Q-0034, unattended, shared `analog_sw` – same on both boards):** C14–C17 → 470 nF
0402 (C47339, preferred; debounce τ ≈ 1.5 ms). New D55 DSK16 (C22466351, already on the BOM) in series after F4 in the
SW_SUPPLY feed: protects the panel LEDs against reverse battery and costs 0.3–0.7 V of switch supply. D54/C54 stay on
J5.5. Margin at SWIN 10.5 V corrected (design-notes §3), p_other ≈ 2.2 W documented (§4, Tj 101 °C at 4 A, the rating
stands), reverse-battery limits qualified (§8, README). README: dry contacts and 12 V cranking note. ERC 0 errors,
5 warnings (unchanged). +1 part, +1 unique part. T-0046 (R3/R4/R7/R8 split) was done later in T-0105 (2 k + 2 k).

**2026-11-02 (T-0069, Q-0032/Q-0033/Q-0041, unattended):** RIS R103/R203/R303/R403 now 680 Ω **1206** (C17975, extended – no
basic exists; value unchanged). New DNP OUT pull-downs R106/R206/R306/R406 47 kΩ 0603 (C25819) per channel. DEN policy
and firmware requirements: design-notes §6.1. ERC 0 errors, 5 warnings (unchanged). Heat budget unchanged.
The 40 mA fault-current case (≈ 1.1 W in RIS) relies on the firmware DEN rule, not hardware.

**Population and ordering rule (Q-0032, T-0040/T-0032):** standard build = **all four BTT6050-1ERA** (≈ 4 A per channel at
40 °C); heavy loads go on pdm-hc2. Fit BTT6010-1ERA only on a channel with a load > 4 A. A mixed build adds one extended
loading fee (≈ 3.07 $) per order and each BTT6010 costs ≈ 1.57 $ more at 10 pcs (2+2 mix ≈ +3.71 $/board), so order mixed
builds together in one order so the fee is paid once.

**2026-11-01 (T-0064, decisions 26/27, unattended):** battery input J10 now has D30 + C30 (1 µF/100 V) on the
terminal net `VBAT_IN`, a DNP ferrite position FL30 bridged by the copper net tie JP30 to `VS`, and C31 100 µF/63 V
bulk on VS (same controller part as HC2). Each channel has C104 1 µF/100 V at the BTT6050 VS tab and a DNP SMAJ30CA
D103 from OUT to GND (refs x04/x03 per channel). Invariant 4 now states the PROFET output rule. ERC unchanged
(6 `lib_symbol_mismatch`), netlist checked. Details and failure-mode notes: design-notes §8.1/§8.2.

**2026-11-02 (T-0065, decisions 30–32, unattended, shared sheets – same on both boards):** FB1/FB2 → GZ2012D601TF
(C1017, basic); D4–D6 → H5VL10B (C7420372, preferred, SOD-882); U6 TPS7B91 → L78M05ABDT (C58069, basic, DPAK) with C13
1 µF/50 V input capacitor; buck: C19 100 nF/100 V at VIN, R43 0 Ω boot resistor, R44/C20 SW snubber **DNP**; C1 →
2.2 µF/100 V 1206 (C170101); C50–C53 → 1 nF/2 kV 1206 (C9196, basic); J3 shield on the new net `USB_SHIELD` with R13
1 MΩ ‖ C18 4.7 nF/1 kV to GND, R14 0 Ω hard-tie **DNP**. README USB service rule added. ERC unchanged
(6 `lib_symbol_mismatch`), netlist checked. Details: design-notes §8.3.

**2026-11-02 (T-0066, Q-0036/Q-0037, unattended, shared lib + `power-usb`, same on both boards):** PG-TDSO-14
footprint paste moved between the thermal vias: 4 × 2.55 × 0.6 + 2 × 2.55 × 0.5 mm windows, 51 % of the exposed pad, all ≥ 0.15 mm
from the via drills. Pads rechecked against Infineon Fig. 53 and the JLCPCB footprint of C534868; they agree. U3 LMR51610 now
uses `Package_TO_SOT_SMD:SOT-23-6` (checked against TI DBV0006A and the JLCPCB footprint, pin numbering identical);
custom `LMR51610.kicad_mod` removed. ERC 0 errors, warnings 6 → 5 (U3 mismatch cleared); netlist: only U3's
footprint changed. Details: design-notes §8.4.

**2026-11-02 (T-0067, Q-0023/Q-0039/Q-0004, rulings Q-0012/Q-0031, unattended, shared `can`, same on both boards):**
U5 ISO1044 → **Chipanalog CA-IS3050G** (C528763, SOIC-8-WB `Package_SO:SOIC-8_7.5x5.85mm_P1.27mm`, new symbol
`ESP32-PDM:CA-IS3050G`; not pin-compatible, pins 5/6/7 = GND2/CANL/CANH). The datasheet check passed: supplies, ±58 V bus,
210 ns loop, 2–8 ms timeout, 5 kV_RMS; LEN 1 still holds at 49.3 mA worst case. −0.71 USD/board. R70 10 k TXD pull-up
to +3V3. DNP CMC FL1 (FACT4532-510-2P-T) in series with CANH/CANL, bridged by fitted 0 Ω R71/R72 (new nets
CANH/CANL_BUS and _XCVR). DNP Y-cap C70 1 nF/2 kV 1206 GND_CAN–GND (capacitor only). The bus side stays on NET-S (Q-0031);
J4 stays 4-pole with the shield open (Q-0012). ERC unchanged (5 `lib_symbol_mismatch`), netlist checked. Details: design-notes §8.5.

**PTC interrupt rating: settled (T-0118, decision 81).** F1–F4 C70113 (I_max 100 A), 0.2 Ω C7420022 R54/R55/R56 in series
with F1/F3/F4 (≈ 86 A for a 30 V hard short). The resistor is accepted on its 5 s / 50 J overload rating; the 30 V
hard-short prototype test below is mandatory before installation. An overstressed resistor fails open (for F4: panel
supply permanently off, bus control keeps working). F4 feeds the panel switches (bilge forced run, navigation lights):
a competent person reviews F1–F4 and R54–R56 before installation.

## Next

1. Open in KiCad: tidy what the scripts placed (labels, part positions; the new parts in `analog_sw` and the
   VBAT/NTC block at the bottom of the root sheet), run *Update Symbols from Library* (USB-C; keep Q3–Q6
   on the BC817 symbol with value MMBT5551 – same pinout; keep Q30 on the IPT007N06N symbol with value AGM601LL – same pins), then ERC.
2. After `/emc pdm-4ch` and `/validate pdm-4ch deep`: fix findings.
3. ~~Verify `Infineon_PG-TDSO-14_ThermalVias` against the JLCPCB footprint~~ done (T-0066). At the first order, check the
   CPL rotation of U11–U14 and U3 (EasyEDA draws both packages rotated 90°).
4. Remaining part checks from the BOM audit: PESD2CAN
   pin 3 = common; Molex 39301080 = 5569-08A2 (if still used).
5. PCB layout after the connector sample check (decision 98): 2 oz, VS copper on both
   layers around the cooling tabs, switches spread out and away from the ESP32; TH1 next to the hottest switch;
   J5 TVSs at the connector.
6. PCB rules from T-0064 (design-notes §8.1/§8.2):
   - **VS copper from the four switches to D30 wide** (both layers, 2 oz): it is the output surge path
     (OUT → PROFET body diode → VS → D30), decision 27.
   - JP30 is the VBAT_IN–VS link: draw it as a copper bridge as wide as the VS copper (the placeholder footprint
     `NetTie-2_SMD_Pad2.0mm` is far too small for 16 A). FL30 has no footprint yet; decide at pre-compliance.
   - D30 and C30 directly at the J10 socket pins; C31 close to J10; C104–C404 at each VS tab.
   - MLCCs on VS/VBAT_IN (C30, C104–C404): away from the J10 flange screws and board edges and not across a bending
     line (a cracked MLCC shorts the battery input).
   - D103–D403 (DNP) next to J11, GND return straight to J10.2.
   - T-0121, T-0158 (design-notes §8.6): Q30 in the 16 A path between JP30 and VS. VBAT_FL and VS copper as wide as the VS
     copper, both layers. **≥ 2 cm² 2 oz copper joined to Q30's drain tab (VS)**: Tj ≈ 66–80 °C at 16 A (40–62 K/W, Infineon's TOLL
     figures as an analogue; AGM gives no copper area). U30 next to Q30 with short SOURCE/GATE traces. C32 at U30, away from Q30's tab. The surge loop
     switches → VS → Q30 → D30 short and wide.
   - T-0143 (design-notes §8.6): D31 directly across the Q30 drain tab and source pins, short and wide.
   - T-0160 (design-notes §8.7): **J6** (unfitted service pads) inside the board near the EMC test points (VS, 3V3, GND, buck SW, CANH/CANL; `docs/reviews/2026-11-03-emc-system.md` item 9), not at an edge connector, short traces from U1, outside the antenna keep-out, pin 1 (GND) marked. On-board use only: no cable leaves the board (invariant 9 for 3V3; invariant 4, the lines are unprotected). **D7/D8** where they are visible with the board in its carrier.
   T-0161 (design-notes §8.3): the buck input loop C1/C19/U3 stays tight and unchanged; the filter position JP1 ‖ L2 sits **before** C1 (D2.K → JP1/L2 → C1), with room for L2's 6 × 6 mm body. JP1 traces at least as wide as its 0.6 mm bar; JP1 on an outer layer where it can be cut. C22/R73 (DNP) next to C1, outside the C1/C19/U3 loop. D3.K joins on the C1 side.
   T-0065 layout rules (design-notes §8.3): C19 (100 nF) right at U3 VIN/GND; R44/C20 footprints tight at the SW
   node; R13/C18/R14 at J3 next to the shield tabs; U6 DPAK with copper under the tab (≈ 0.5 W); C1 1206 away from
   board edges and screws.
7. Before ordering: check the `CP_Elec_8x10` and `C_1206` footprints against the JLCPCB footprints of C487384
   and C170101; before fitting D103–D403 read the demagnetisation note in design-notes §8.2.

**PCB rule 9 – isolation barrier (EMC review 2026-10-30, updated T-0067):** no copper (pour, trace, via) under U5
between pins 1–4 and 5–8. Keep the GND and GND_CAN islands apart around the body by the package creepage (CA-IS3050G
SOIC-8-WB: 8 mm CLR/CPG), at least ≥ 4 mm. **C70 is the only part that crosses the gap**, on its own pads next to
U5. D9, D10, F3, FB2, D11, U6, FL1, R71/R72 sit on the GND_CAN side; U5 pins 1–4 and R70 on the GND side. FL1 and
R71/R72 go between D9 and U5 (D9 at J4).

## Prototype test list

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

- Decision 98: buy one sample of each connector set **before layout**. Check that plugs cannot go in reversed, whether the J4 plug enters the J5 socket (label them if so), and the fit at 36 mm rail pitch. pdm-4ch J10 is now the fixed terminal KF135T-10.16-2P C475108 (decision 121): check the wire entry faces the board edge, the M4 screw access at the 36 mm pitch and the pad fit. The J10/J11 pair on pdm-hc2 is unchanged. Hand-solder J10 with a powerful iron; check the joints. Before the next revision, re-check connector stock, plug sets included (decision 121).
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
- T-0121: check the KiCad footprints `Infineon_PG-HSOF-8-1` (Q30, pads 1 G / 2 S / 3 D) and `TSOT-23-8` (U30; TI DDF land
  1.05 × 0.45 mm pads, 2.6 mm column pitch) against the JLCPCB footprints of C5464765 and C5219210. Recheck stock (C5464765
  2016 on 2026-11-07, C5219210 2923 on 2026-11-03).
- T-0143: check KiCad `D_SMC` (D31; pads 2.5 × 3.3 mm, gap 4.3 mm) against the JLCPCB footprint of C42371557 (`SMC_L7.2-W5.8-LS8.1-BI`, pads 3 × 3.8 mm, gap 4.6 mm; hongjiacheng suggested land: pads 3.03 × 3.82 mm, gap at most 3.84 mm) and recheck its stock (10271 on 2026-11-04).
- T-0021: BOM lines without `LCSC` are now only H1–H4 and the DNP positions.
- T-0160: check the CPL rotation of D7/D8 (C2286; JLCPCB footprint pad 1 = anode, KiCad pad 1 = cathode, cathode on the same side) and the KiCad `LED_0603_1608Metric` pads against `LED-SMD_L1.6-W0.8-R-RD`.

## For /system

- T-0160 (`/system firmware`): IO13 drives the status LED (high = on, ≈ 0.7 mA); keep its internal pull-up off; hold it low in Sleep. Leave spare inputs on J6 (IO35–IO37, IO42) with a pull enabled while unused.
- Decision 93 (`/system firmware`): read IO12 (high = SW_SUPPLY present); alert only while VBAT_SENSE shows a healthy battery.
- T-0107 (`/system firmware`): the IS scale constant is now **RIS = 500 Ω** (2 × 1 kΩ). IL = VIS / 500 Ω × kILIS, ≈ 0.33 V/A for the BTT6050 and ≈ 0.128 V/A for the BTT6010 (design-notes §6.1). A sense current of about 5.8 mA reads full scale (2.9 V), below the minimum IIS(FAULT) of 6 mA, so DEN rule 2 still sees every fault.
- T-0069 RIS note below: C17975 is gone again since T-0107. The 40 mA fault case is now 0.8 W in two 0.25 W parts, still covered only by firmware.

- T-0069: firmware requirements for DEN (design-notes §6.1) belong in the `/system firmware` list. T-0069 swapped one
  unique extended part (−/+): C23228 (basic) is replaced by C17975 (extended, 1206 680 Ω); C25819 (basic) is added.
- RIS at the 40 mA maximum fault current (≈ 1.1 W) is covered only by firmware; hardware cover would need a ≥ 1.5 W
  resistor – owner decision if wanted.

- T-0118: the PTC interrupt-rating problem is settled (decision 81): F1–F4 C70113, R54–R56 0.2 Ω C7420022, unique extended
  parts ±0. A competent person reviews F1–F4 and R54–R56 before installation (F4: panel switches).

- DIN carrier and printed enclosure design: `/system mechanical`.
