# pdm-hc2 status

Updated: 2026-11-07 (T-0185 "For /system" sync sweep)

**2026-11-07 (T-0185: "For /system" sweep, unattended, documents only):** the ARCHITECTURE root row now names D7/R59, D8/R67 and J6 (decisions 113, 115, 116), and the Mechanics table has its own HC2 J10 row (C6394053 + C6394029, unchanged). No schematic change. Report: `docs/reviews/2026-11-07-fix-sync-T-0185.md`.

**2026-11-07 (T-0180: T-0176, unattended, documents only):** the HC2 turn-off edge (PD direct, estimated about 500 V/µs) is on the prototype test list as a pre-compliance scan trial: R116/R216 0 Ω → 10–22 Ω by hand, scope and VHF check, SOA recompute before any value is kept (decision 25 stays). R116/R216 stay 0 Ω C17168; no schematic, footprint or BOM change. Design-notes §4a.3. Report: `docs/reviews/2026-11-07-fix-pdm-hc2-T-0180.md`.

**2026-11-07 (T-0179: T-0166, T-0168, T-0177, owner rulings Q-0068/Q-0069, unattended, documents only):** J11 keeps C577772 + C577752 (no design change); buy C577772 from any seller, marking KF2EDGSRM-7.62 (flange header); no C577767, C7422678 or other socket; the order waits if none can be bought. The J11 output plug fits the pdm-4ch J10 battery socket and vice versa: mark the battery plug and check it before power-up (pre-order checklist, README). No schematic, footprint or BOM change. Report: `docs/reviews/2026-11-07-fix-shared-T-0179.md`.

**2026-11-07 (T-0161: T-0153, owner ruling 2026-11-06, unattended, shared – `power-usb`, same on both boards):** buck input filter position. Net-(D2-K) is split: D2.K → **JP1** (copper bridge, bridged solder-jumper footprint, no part) ‖ **L2** (DNP, SWPA6045S8R2MT C96963 footprint, example 8.2 µH) → C1/C19/U3. D3 (USB) stays on the U3 side, so USB-only input is unchanged (3.74 V at 0.40 A, decision 87). Damping option **C22 2.2 µF C170101 + R73 10 Ω C17903 across C1, both DNP**. A 0 Ω chip part was not used: neither C17168 nor C21189 publishes pulse data for the ≈ 86 A / ≤ 9.6 A²s F1 trip. The 0.6 mm copper bar carries 87 A²s at 2 oz (Onderdonk). With JP1 fitted, the buck input changes only by ≈ 0.2 mΩ. L2 must be fitted only together with C22/R73: undamped, the filter peak (≤ 21 Ω) is only 1.4× below the buck's 29 Ω negative input impedance at a cranking dip, and a surge step can push U3 VIN to ≈ 64 V (65 V recommended). F1, R54 and their ratings are unchanged. ERC 0 errors, 5 warnings (unchanged); +4 DNP parts, unique +0. Design-notes §8.3. **A competent person reviews F1 and R54 before installation.** Report: `docs/reviews/2026-11-07-fix-shared-T-0161.md`.

**2026-11-07 (T-0160: T-0150, T-0151, T-0152, owner rulings 2026-11-06, unattended, shared – controller part of the root sheet, same on both boards except J6 pins 4–6):** sign-of-life LEDs and service pads. **D8 + R67** power LED +3V3 → GND; **D7 + R59** status LED IO13 → GND (high = on, off while IO13 is undriven). LEDs KT-0603R red 0603 C2286 (basic, the one new line), resistors 2.2 k C25879 (on the BOM): ≈ 0.7 mA each. D8 draws continuously, also in Eco/Sleep (decision 13), ≈ 2.3 mW from 3.3 V. **J6** unfitted `PinHeader_1x08_P2.54mm_Vertical`, DNP, no BOM line: 1 GND, 2 TXD0, 3 RXD0, **4–6 not connected** (IO35–IO37 are FLT_T1/FLT_I2/FLT_T2 here, FLT nets untouched, auto decision), 7 IO42, 8 +3V3. Pin checks: none strapping, none used in the N8 module. CAN TX/RX LEDs left out (see design-notes §8.7). Pin map and the controller power row updated in ARCHITECTURE. ERC 0 errors, 5 warnings (unchanged); netlist differs only in U1 pins 17, 38–40 and the new parts. 237 parts (+5, J6 DNP), 65 unique (+1). Design-notes §8.7. Report: `docs/reviews/2026-11-07-fix-shared-T-0160.md`.

**2026-11-07 (T-0159: T-0149, owner ruling, decisions 99 and 105, unattended, shared – same on both boards):** near-duplicate BOM lines merged; values and nets unchanged. C2 → C307331 0402, C12 → C15849 0603, R9 → C36871 0402, R10 → C25768 0402. **C13 stays on C28323:** C15849 keeps only 0.10 µF at 29 V and 0.31 µF at 12 V (Samsung's simulation), below the L78M05's 0.33 µF, while C28323 keeps 0.42 µF worst case at 29 V. C14663, C52923, C31850, C23231 are gone: 64 unique (−4), 6.12 USD per order. **Layout:** C2, R9, R10 are 0402, C12 is 0603 (was 0402), C13 stays 0805. ERC 0 errors, 5 warnings (unchanged). 3.3 V setpoint tolerance unchanged (±1 %, ±100 ppm/°C). Design-notes §8.3. Report: `docs/reviews/2026-11-07-fix-shared-T-0159.md`.

**2026-11-06 (cost session, no schematic change):** on hold. Layout and order follow `pdm-4ch` bring-up, so shared-sheet fixes go in once (decision 102). Later orders: 5 bare PCBs, 2 assembled, 2 oz, Standard PCBA, about 230 $ with connector sets (decisions 99, 101). Shared-sheet items T-0149 to T-0153 are queued and will change this board too. The pump start current test moved to the prototype list (decision 100). Moving to 1 oz was examined and not chosen: about 13 A per channel and a lower breaker setting (design-notes §4a).

**Where it stands:** schematic complete (scripted), ERC: 5 `lib_symbol_mismatch` notices only (since T-0066); netlist checked.
TPS48110A-Q1 + 2 × BSC030N08NS5 per channel, values in `docs/design-notes.md` §4a. No PCB. Decisions 1–6, 8–15, 17, 18
apply. Shared `analog_sw` sheet and controller pin map updated on 2026-10-30 (same as `pdm-4ch`): SW_SUPPLY on J5.5,
MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9.

**2026-11-04 (T-0147: "For /system" sweep, unattended, documents only):** the T-0064 and T-0065 cost entries left this list: C13832 and C107198 are no longer on this board, and the record stays in design-notes §8.1 and §8.3. No schematic change. Report: `docs/reviews/2026-11-04-fix-sync-T-0147.md`.

**2026-11-04 (decision 95, /system, no schematic change):** board input limits are 32 A (`pdm-4ch`) and 36 A (`pdm-hc2`) instead of ≈ 40 / 50 A; they set J10, its GND pole and the supply copper in `/system mechanical`. Output terminals are still open.

**2026-11-05 (decision 98, /system mechanical, same on both boards except J11):** all four connectors are keyed plugs on right-angle sockets: J10 C6394053 + C6394029, J11 locking C577772 + C577752, J5 C26895 + C26865, J4 C7245 + C7244. Five new footprints in `lib/ESP32-PDM.pretty` drawn from the maker drawings. Fields only: no net changed; pads match pins; ERC 0 errors, 5 warnings (unchanged). **For the PCB:** mating faces at the board edge; board depth about 75 mm; J10 reaches 34 mm in from the edge; TVSs at the socket pins (invariant 4); keep the J10/J11 rows on one edge, J5/J4 on the other.

**2026-11-05 (decision 97, /system mechanical, root sheet, same on both boards):** the board mounts on a plastic DIN carrier (edge-on, about 36 mm per unit, enclosure by the installer) or in a printed enclosure. H1/H2 had no footprint: H1–H4 are now four `MountingHole_3.2mm_M3` non-plated holes. ERC 0 errors, 5 warnings (unchanged); netlist adds H3/H4 and footprints only. **For the PCB:** holes at the corners with copper keep-out, no copper reachable by carrier or screws (invariant 6), and J10 height sets the pitch.

**2026-11-04 (decision 93, /system, shared `analog_sw` + root sheet, same on both boards):** SW_SUPPLY sense added: R49 10 k 1206 → SW_SENSE, R57 4.7 k, D24 BZT52C3V3, C21 470 nF, R58 10 k (root sheet) → IO12 as a digital input. It replaces the decision 21 divider, which could not work on IO12 (design-notes §5). +5 parts, +0 unique. ERC 0 errors, 5 warnings (unchanged); netlist differs only in those parts and U1 pad 16. Needs the KiCad tidy of the new parts' labels.

**2026-11-04 (decision 94, /system):** plan on one LED work light per HC2 output; about 50 µF per output, confirmed on the prototype; several lights on one output only for low-capacitance loads or a group shown to switch on cleanly. README and design-notes §4a.3 updated. No schematic change.

**2026-11-04 (T-0141: "For /system" sweep, unattended, documents only):** ARCHITECTURE root row updated (C30 2.2 µF C170101; the blocker Q30 is pdm-4ch only, HC2 unchanged, decision 40). `tools/heat_budget.py --p-other` default 2.2 → 2.3 W: 2 × 15 A still Tj ≈ 90 °C with the HC2 arguments of §4a. No schematic change. Report: `docs/reviews/2026-11-04-fix-sync-T-0141.md`.

**2026-11-03 (T-0119: T-0096/T-0090, owner Q-0061/Q-0062, decision 83, unattended, shared – `power-usb`, same on both boards):** USB shield capacitor C18 is now 1 nF/2 kV X7R 1206 C9196 (basic, already on the BOM) instead of 4.7 nF/1 kV C107198 (extended). Footprint, R13 1 MΩ and R14 0 Ω DNP unchanged. Shield RC 1 MΩ ‖ 1 nF, corner ≈ 160 Hz (was 34 Hz). ERC 0 errors, 5 warnings (unchanged); netlist differs only in C18 value/LCSC. 225 parts (+0), 68 unique (−1). Details: design-notes §8.3, `docs/reviews/2026-11-03-fix-shared-T-0119.md`.

**2026-11-03 (T-0118: T-0018, Q-0060/decision 81, unattended, shared – `power-usb`, `can`, `analog_sw`, same on both
boards):** F1–F4 are now TECHFUSE mSMD050-60V C70113 (60 V, I_max 100 A, I_hold 0.50 A, R1max 1.0 Ω, 1812; F2 moved from
`Fuse_0805_2012Metric` to `Fuse_1812_4532Metric`). New 0.2 Ω 2 W alloy 2512 FOJAN FRM252WJR200TK C7420022 in series on the
protected side: R54 (F1 → D1/D2), R55 (F3 → D10/FB2), R56 (F4 → D55); F2 has none. Hard short behind a resistor: 30 V /
0.35 Ω ≈ 86 A < 100 A. Checks: switch path ≈ 2.03 V ≥ 2.0 V at a 10.5 V battery via D55 (F4 + R56 1.2 Ω, less than the
old 1.4 Ω); L78M05 input ≈ 8.5 V at NET-S 9 V; buck input −0.22 V at 0.18 A; USB-only at the 0.40 A peak 3.74 V typ (was
3.80 V; below the 4 V minimum with either part, same result in every corner). ERC 0 errors, 5 warnings (unchanged);
netlist differs only in F1–F4 and R54–R56. +3 parts, +0 unique (+C70113 +C7420022 −C19078719 −C269104). Heat budget: no
output change, losses in mW. Details: design-notes §8.3, `docs/reviews/2026-11-03-fix-shared-T-0118.md`.

**2026-11-03 (T-0107: T-0099, unattended, shared – cost lever L8):** C30 (root, battery input J10, same on both boards) is now 2.2 µF/100 V X7R 1206 C170101 (the part already used as C1; decision 26 allows 1–2.2 µF at J10). CVS C102/C202 (VS_CTRL) are now 2.2 µF/100 V C170101 as well. TPS4811-Q1 Table 9-3 recommends 0.1–10 µF and states no upper limit. τ = 100 Ω × 2.2 µF = 0.22 ms, and the RVS drop is unchanged. pdm-hc2 therefore no longer needs C13832. The C18 swap (T-0096) is blocked: confirmed decision 31 names 4.7 nF, so it goes to the owner. ERC 0 errors, 5 warnings (unchanged). The netlist differs only in C30, C102 and C202. +0 parts, −1 unique. Extended types 20 → 19. Details: design-notes §4a.1 and §8.1, `docs/reviews/2026-11-03-fix-shared-T-0107.md`.


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

**2026-11-03 (T-0073: T-0021/T-0031/T-0033/T-0043/T-0051/T-0060, unattended, shared – same on both boards):** `LCSC` fields added (cost report C1, each checked against value, package and net voltage): C2 C14663, C4/C6 C15849, C5 C19666, C7/C9 C28233, C8 C45783, C10/C11 C307331, C12 C52923, D12/D13 BAT54C C22466350 (preferred; pinout 1/2 anodes, 3 common cathode), R1/R2/R5/R6 C25879, R11/R12 C25905, R15–R17/R21/R24/R27 C25744 – all basic except the BAT54C, no new unique extended part. C13 and FB1/FB2 already had codes from T-0065. R1/R2 and the NTC TH1 (C52155402) stay (Q-0025, Q-0024). VBAT full scale ≈ 32 V and the IO3 strap rule are in design-notes §2.

**2026-11-03 (T-0072: T-0053/T-0062/T-0058/T-0055, unattended, decisions 39/40):** breaker RIWRN R113/R213 47 k →
68 k (C36871, preferred, replaces C25792): IOC ≈ 17.5 A nominal, ≈ 15.2–19.7 A over tolerances, tOC 146 ms unchanged;
Tj 111 °C at 17.5 A, 139 °C at 19.7 A (< 150 °C). OUT sense on the root sheet: R63 220 k / R64 22 k / C62 100 nF
OUT1 → IO4, R65/R66/C63 OUT2 → IO5 (same parts as VBAT_SENSE, no new unique part), IO4/IO5 no-connects removed.
README: external breaker ≤ 15–18 A per output, label requirement, reverse-battery warning. design-notes §1, §4a,
§4a.2 (calculations, failure modes), §8 (HC2 reverse battery), §9 corrected. ERC 0 errors, 5 warnings (unchanged);
netlist checked; pdm-4ch unchanged. **For the PCB:** R63–R66/C62/C63 near U1 with the 220 k at the OUT side.

**2026-11-03 (T-0071: T-0056/T-0005/T-0008, unattended, `hc_channel` ×2):** controller pin filtering, all from
parts already on the BOM. C107/C207 1 nF (C1523) DIODE–GND across Q13/Q23 (TI 9.6.1, mandatory). RVS R114/R214 100 Ω
(C25076) VS → new net `VS_CTRL` on U11/U12 pin 20; C102/C202 became the CVS: 1 µF/100 V 1206 (C13832) on `VS_CTRL`
(drop ≤ 70 mV; PWR_FLAG on `VS_CTRL`). CS X cap C108/C208 1 nF (τ 0.1 µs ≪ tSC 4 µs); Y caps C109/C110, C209/C210
100 pF/100 V **DNP** (unbalanced source impedance, fit only with ferrites at Q-0012); C111–C113/C211–C213 1 nF on
EN/UVLO, OV, IWRN (OV reacts in ≤ 0.4 ms; 10 nF rejected at 4 ms). ERC 0 errors, 5 warnings (unchanged); netlist
checked. Values and failure mode: design-notes §4a.1. **For the PCB:** C107/C207 at the MMBT3904, emitter
Kelvin-routed to U11/U12 GND pin 6; RVS/CVS at pin 20; C108/C208 across pins 17/18.

**2026-11-02 (T-0068, shared `analog_sw` – same as `pdm-4ch`):** C14–C17 → 470 nF (C47339, debounce τ ≈ 1.5 ms); new D55
DSK16 (C22466351, already on the BOM) after F4 in the SW_SUPPLY feed (panel-LED reverse protection, −0.3–0.7 V on the
switch supply). ERC 0 errors, 5 warnings (unchanged). The HC2 reverse-battery note in design-notes §8 is still open (P9).

**2026-11-01 (T-0064, decisions 26/27, unattended):** battery input J10 now has D30 + C30 (1 µF/100 V) on the
terminal net `VBAT_IN`, a DNP ferrite position FL30 bridged by the copper net tie JP30 to `VS`, and C31 100 µF/63 V
on VS (same controller part as 4-ch). HC2-only: C106/C206 100 µF/63 V on VS per channel (3 × 100 µF in total), and
D103/D203 SMAJ33CA (C19077549, preferred) from each OUT to GND at J11. ERC unchanged (6 `lib_symbol_mismatch`),
netlist checked. Details, part facts and the bilge-output failure mode: design-notes §8.1/§8.2.

**2026-11-02 (T-0065, decisions 30–32, unattended, shared sheets – same on both boards):** FB1/FB2 → GZ2012D601TF
(C1017, basic); D4–D6 → H5VL10B (C7420372, preferred, SOD-882); U6 TPS7B91 → L78M05ABDT (C58069, basic, DPAK) with C13
1 µF/50 V input capacitor; buck: C19 100 nF/100 V at VIN, R43 0 Ω boot resistor, R44/C20 SW snubber **DNP**; C1 →
2.2 µF/100 V 1206 (C170101); C50–C53 → 1 nF/2 kV 1206 (C9196, basic); J3 shield on the new net `USB_SHIELD` with R13
1 MΩ ‖ C18 4.7 nF/1 kV to GND, R14 0 Ω hard-tie **DNP**. README USB service rule added. ERC unchanged
(6 `lib_symbol_mismatch`), netlist checked. Details: design-notes §8.3.

**2026-11-02 (T-0066, Q-0037, unattended, shared `power-usb`, same on both boards):** U3 LMR51610 now uses
`Package_TO_SOT_SMD:SOT-23-6` (checked against TI DBV0006A and the JLCPCB footprint of C22427220, pin numbering
identical); custom `LMR51610.kicad_mod` removed from `lib/`. ERC 0 errors, warnings 6 → 5 (U3 mismatch cleared);
netlist: only U3's footprint changed. The PG-TDSO-14 paste fix in the same package affects only pdm-4ch. Details: design-notes §8.4.

**2026-11-03 (T-0106: T-0054/T-0006/T-0061/T-0053, Q-0049–Q-0051/Q-0053, decision 72, unattended, `hc_channel` ×2):**
gate slew fitted per TPS4811-Q1 §8.3.2.1 (decision 25 topology): R104/R204 = R1 10 Ω → **10 k** (C25744); new
R115/R215 10 Ω (C25077) + C114/C214 **1 nF/2 kV 1206** (C9196) from GATE to GND; PD now on its own net through the
0 Ω RGATE_PD R116/R216 (C17168) to GATE. All parts already on the BOM: +6 parts, +0 unique. Output ramp ≈ 0.5–0.75 V/µs
(≈ 40–57 µs for 30 V, was ≈ 400–800 V/µs). **Rating: ≤ ≈ 50 µF load input capacitance per output** (68 µF and 100 µF
fail the SOA from a hot start; 100 µF also trips ISCP): 50 µF + 15 A → ≤ 53 A peak (ISCP ≥ 71 A), SOA margin 1.76
idle / 1.03 hot (Tj 90 °C after 15 A), Tj ≈ 124 °C (Zth). Turn-on into a zero-impedance short is inside SOA from an
idle board (≤ 63 °C, margin 1.18) but not right after running at 15 A (0.69–0.89; no R1/C1 fixes that corner – open
point, prototype test). Turn-off and the fast trip unchanged (PD direct). Eq. 4 OK. Heat budget unchanged (2 × 15 A →
Tj 90 °C). README: HC2 load guidance and the 50 µF limit. T-0053: no change (R113/R213 68 k, decision 39); decision 19
and the 21 A option are withdrawn. ERC 0 errors, 5 warnings (unchanged); netlist differs only in those refs and U11/U12
pin 14 (new net PD). Details: design-notes §4a.3, `docs/reviews/2026-11-03-fix-pdm-hc2-T-0106.md`. **For the PCB:**
C114/C214 and R115/R215 at the MOSFET gates, C1 GND return to U11/U12 GND; R116/R216 close to U11/U12 pin 14, with pads a hand-swap can reach (T-0180 scan item).

**Rules until bench-measured:** no PWM on HC2 outputs (Q-0001). Prototype tests: measure the real load input
capacitance and inrush of every intended HC2 load, including grouped LED work lights (Q-0045), and confirm the ≈ 50 µF
rating (no ISCP trip at switch-on); split LED groups that trip; measure the output ramp (≈ 0.5–0.75 V/µs expected);
switch a hot channel (after 15 A) on into a short and check Q11/Q21 survive (T-0106 open point); check whether an INP
toggle cuts the 3.8 min auto-retry short.

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

0. Gate slew done (T-0106, 50 µF rating). Open: turn-on into a short straight after running at 15 A is outside the
   calculated SOA (bounding model) – prototype test above; `/validate pdm-hc2 deep` rechecks the §4a.3 method.
1. Open in KiCad: tidy the label-wired `hc_channel` sheet and the parts the panel-cable script placed, *Update
   Symbols from Library* (keep Q3–Q6 on the BC817 symbol with value MMBT5551), ERC.
2. `/validate pdm-hc2 deep` (part facts of TPS48110A-Q1, BSC030N08NS5, the equations) and `/emc pdm-hc2`.
3. Verify the custom footprint `Texas_DGX0019A_VSSOP-19_3x5.1mm_P0.5mm` against the JLCPCB footprint (C17556513).
4. PCB: Kelvin sense on the 1 mΩ shunt, MMBT3904 between the MOSFETs, TH1 next to the MOSFETs, J10/J11 per decision 98, 36 A input (decision 95).
   T-0064 rules (design-notes §8.1/§8.2):
   - **D103/D203 next to the J11 socket pins, GND return a short, wide path straight to J10.2** (not via the logic
     ground); decision 27.
   - JP30 (VBAT_IN–VS) as a copper bridge as wide as the VS copper for 36 A (the placeholder footprint
     `NetTie-2_SMD_Pad2.0mm` is far too small); FL30 has no footprint yet, decided at pre-compliance.
   - D30, C30 at the J10 socket pins; C31 near J10; C106/C206 at each channel's VS next to RSNS/Q11.
   - C30 (MLCC on the battery input) away from the J10/J11 flange screws, board edges and bending lines.
   - T-0160 (design-notes §8.7): **J6** (unfitted service pads) inside the board near the EMC test points (VS, 3V3, GND, buck SW, CANH/CANL; `docs/reviews/2026-11-03-emc-system.md` item 9), not at an edge connector, short traces from U1, outside the antenna keep-out, pin 1 (GND) marked. On-board use only: no cable leaves the board (invariant 9 for 3V3; invariant 4, the lines are unprotected). **D7/D8** where they are visible with the board in its carrier.
   T-0161 (design-notes §8.3): the buck input loop C1/C19/U3 stays tight and unchanged; the filter position JP1 ‖ L2 sits **before** C1 (D2.K → JP1/L2 → C1), with room for L2's 6 × 6 mm body. JP1 traces at least as wide as its 0.6 mm bar; JP1 on an outer layer where it can be cut. C22/R73 (DNP) next to C1, outside the C1/C19/U3 loop. D3.K joins on the C1 side.
   T-0065 layout rules (design-notes §8.3): C19 (100 nF) right at U3 VIN/GND; R44/C20 footprints tight at the SW
   node; R13/C18/R14 at J3 next to the shield tabs; U6 DPAK with copper under the tab (≈ 0.5 W); C1 1206 away from
   board edges and screws.
6. Cost lever: R1/R2 (2.2 k pull-downs on IO8/IO11, left over from the 4-ch drive) have no function here – remove
   in `/cost` or keep the controller part identical to `pdm-4ch`.

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
- **E20 / T-0176 – HC2 turn-off edge (pre-compliance scan, T-0180):** the HC2 turn-off edge is not slewed (PD direct through R116/R216 0 Ω, R(PD) 0.69–1.34 Ω into about 10.5 nF, estimated about 500 V/µs against 0.5–0.77 V/µs at turn-on; estimate, not simulated). At the scan, hand-swap R116/R216 0 Ω → 10–22 Ω (0402), look at the turn-off edge on the scope and listen for a click on a VHF receiver at switch-off. Recompute the short-circuit SOA of design-notes §4a.3 (fast trip tSC 4–5 µs; the gate needs about 230 ns at 22 Ω) before any value is kept. Keeping a value amends decision 25 (PD direct) and goes to the owner.
- **Q-0042 / decision 100 – bilge pump start current (SEAFLO SFBP2-G3500-01), mandatory before a board runs a pump in
  service:** procedure in `docs/pump-start-current-test.md`. The start must fall below ≈ 15 A (lower IOC tolerance)
  within ≈ 120 ms, else the breaker trips the forced run. If it does not, back to the owner.

## Pre-order checklist (T-0065)

- Decision 98: buy one sample of each connector set **before layout**. Check that plugs cannot go in reversed, whether the J4 plug enters the J5 socket (label them if so), and the fit at 36 mm rail pitch. Then buy the sets for the order: stock is thin on C6394053 / C6394029, C577772 / C577752. Hand-solder J10 with a powerful iron; check the joints. **J11 C577772 + C577752, owner ruling Q-0068/Q-0069 (T-0179):** keep the set, no design change. The sockets are hand-soldered (decision 85), so buy C577772 **from any seller** (LCSC restock, AliExpress Kefa, other distributors; LCSC 0 / 63 on 2026-11-07, C577772 minimum order 18) and check that the marking reads **KF2EDGSRM-7.62 (flange header)**, not KF2EDGSR. **No C577767, C7422678 or any other socket** (no flange for the C577752 plug's ear screws, no lock; `docs/part-facts/C577767.md`, `docs/part-facts/C7422678.md`). **If no seller has C577772 by order time, the order waits.**
- Plug marking (T-0177, owner action at the decision 98 sample check): the J11 output plug and the pdm-4ch J10 battery plug are the same set (C577772 + C577752) and fit each other. A battery plug in this J11 short-circuits the battery through Q21/Q22 when channel 2 turns on; an HC2 load plug in a pdm-4ch J10 leaves that unit dead. Mark the battery plug (for example a red sleeve or label) and check it before power-up. Layout notes (`docs/reviews/2026-11-07-emc-system-2.md` layout rule 2): silkscreen "OUT1 OUT2" at J11, "BATTERY" and the polarity at the pdm-4ch J10.
- Bilge pump start current: moved to the prototype test list (decision 100).

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
- T-0060 (production / flashing): never burn eFuse `EFUSE_STRAP_JTAG_SEL` – IO3 is held low by the IMON2 network
  (design-notes §2).
- T-0107: C30, C102 and C202 use C170101 2.2 µF/100 V instead of C13832 1 µF, which removes the C13832 loading fee for the 5-board first run. For runs of **15+ pdm-hc2 boards** C13832 at these places is cheaper again (cost report L8). C102/C202 must stay within TPS4811 Table 9-3 (0.1–10 µF).
- T-0021: BOM lines without `LCSC` are now only H1–H4 and the DNP positions.
- T-0160: check the CPL rotation of D7/D8 (C2286; JLCPCB footprint pad 1 = anode, KiCad pad 1 = cathode, cathode on the same side) and the KiCad `LED_0603_1608Metric` pads against `LED-SMD_L1.6-W0.8-R-RD`.

## For /system

- T-0072/T-0055: J10 is keyed (decision 98); the board label carries the reverse-battery warning and the external-breaker requirement (≤ 15–18 A per output).
- T-0072/T-0053: **firmware soft fuse** on IMON for each HC2 output (`/system firmware`): alarm and switch-off above the
  15 A rating (e.g. I²t), since the hardware breaker sits at ≈ 15–20 A. Firmware also reads IO4/IO5 (OUT sense,
  full scale ≈ 31.9 V) and reports "OUT high while off" as a float-driven run.
- **Next HC2 revision:** full reverse-polarity protection at J10 (deferred by Q-0044, keep on the list). Pre-charge path (TPS48111-Q1) if the prototype shows real loads exceed about 50 µF (decision 94).
- Decision 93 (`/system firmware`): read IO12 (high = SW_SUPPLY present); alert only while VBAT_SENSE shows a healthy battery.
- T-0160 (`/system firmware`): IO13 drives the status LED (high = on, ≈ 0.7 mA); keep its internal pull-up off; hold it low in Sleep. Leave IO42 with a pull enabled while unused.

- T-0118: the PTC interrupt-rating problem is settled (decision 81): F1–F4 C70113, R54–R56 0.2 Ω C7420022, unique extended
  parts ±0. A competent person reviews F1–F4 and R54–R56 before installation (F4: panel switches).

- **Bilge output fusing (T-0064 failure mode, needs README/installation rule):** D103/D203 sit outside the
  back-to-back MOSFETs. If a TVS fails short, a float-switch run feeds the short through the PDM output wire. The
  float circuit stays independent (invariant 8) only if the PDM leg has its own fuse, between J11 and the junction
  with the float circuit, that opens before the float fuse. Add this to the README next to the external breaker of
  decision 39; a competent person reviews the bilge wiring before installation.

- DIN carrier and printed enclosure design: `/system mechanical`.
