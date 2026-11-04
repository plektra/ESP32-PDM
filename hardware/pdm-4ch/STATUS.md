# pdm-4ch status

Updated: 2026-11-04 (T-0137)

**Where it stands:** schematic complete (scripted edits), ERC: 5 `lib_symbol_mismatch` notices only (since T-0066). Netlist checked
after every edit. No PCB. Decisions 1–7, 9–14, 17, 18 apply. Panel connector J5 and the pin map changed on
2026-10-30 (decisions 17, 18): SW_SUPPLY on J5.5, MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9,
channel-4 drive moved to IO11.

**2026-11-04 (T-0137: T-0129, owner ruling Q-0066, unattended, no schematic change):** the TVS across Q30 is **not fitted yet; back with the owner**. Stop (iii) of the brief applies: every part that keeps Q30 VDS below 60 V at the 31 A bounding current with an adequate pulse rating also lets VS fall below 0 V at that current. Example: SMDJ40CA C42371557 (preferred, same SMC package), VDS 59.4 V at 31 A, VS +3.1 V at the 12 A textbook pulse but −4.0 V at 31 A. C31 has no reverse rating (decision 82). SMCJ30CA already on the BOM is the worst for this: −15.1 V at 31 A and still −8.0 V at 12 A. §8.6 (b) and (c) stay unchanged until the owner chooses. Numbers per candidate and the question: `docs/reviews/2026-11-04-fix-pdm-4ch-T-0137.md`. Facts added for seven TVS parts in `docs/part-facts/`.

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

**Waiting for the owner:** decision 21 **[proposed]** (sense SW_SUPPLY on IO12 so a tripped F4 can be reported); which TVS goes across Q30, given that VS goes negative at the 31 A bound (T-0129, report T-0137).

## Next

1. Open in KiCad: tidy what the scripts placed (labels, part positions; the new parts in `analog_sw` and the
   VBAT/NTC block at the bottom of the root sheet), run *Update Symbols from Library* (USB-C; keep Q3–Q6
   on the BC817 symbol with value MMBT5551 – same pinout), then ERC.
2. After `/emc pdm-4ch` and `/validate pdm-4ch deep`: fix findings.
3. ~~Verify `Infineon_PG-TDSO-14_ThermalVias` against the JLCPCB footprint~~ done (T-0066). At the first order, check the
   CPL rotation of U11–U14 and U3 (EasyEDA draws both packages rotated 90°).
4. Remaining part checks from the BOM audit: Kangnex WJ15EDGVC CAN connector on the Phoenix MCV footprint; PESD2CAN
   pin 3 = common; Molex 39301080 = 5569-08A2 (if still used).
5. PCB layout after the terminal blocks and enclosure are decided (`/system mechanical`): 2 oz, VS copper on both
   layers around the cooling tabs, switches spread out and away from the ESP32; TH1 next to the hottest switch;
   J5 TVSs at the connector.
6. PCB rules from T-0064 (design-notes §8.1/§8.2):
   - **VS copper from the four switches to D30 wide** (both layers, 2 oz): it is the output surge path
     (OUT → PROFET body diode → VS → D30), decision 27.
   - JP30 is the VBAT_IN–VS link: draw it as a copper bridge as wide as the VS copper (the placeholder footprint
     `NetTie-2_SMD_Pad2.0mm` is far too small for 40 A). FL30 has no footprint yet; decide at pre-compliance.
   - D30 and C30 directly at the J10 terminals; C31 close to J10; C104–C404 at each VS tab.
   - MLCCs on VS/VBAT_IN (C30, C104–C404): away from the terminal screws and board edges and not across a bending
     line (a cracked MLCC shorts the battery input).
   - D103–D403 (DNP) next to J11, GND return straight to J10.2.
   - T-0121 (design-notes §8.6): Q30 in the 40 A path between JP30 and VS. VBAT_FL and VS copper as wide as the VS
     copper, both layers. **≥ 6 cm² 2 oz copper on Q30's drain tab (VS)**, otherwise Q30 runs too hot at 40 A (minimal pad:
     Tj ≈ 200 °C). U30 next to Q30 with short SOURCE/GATE traces. C32 at U30, away from Q30's tab. The surge loop
     switches → VS → Q30 → D30 short and wide.
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
- **T-0042 / Q-0034 – switch-path margin:** measure IN − device GND (U11–U14 pin IN vs the channel's ground network) at
  SWIN = 10.5 V with the channel on, once with the 3.3 V rail removed and once with it present. Repeat at a 10.5 V battery
  with D55's drop (SWIN ≈ 9.8–10.1 V). Pass: ≥ 2.0 V (VIN(H) min). If short, the planned fix is **RIN R101/R201/R301/R401 →
  4.7 kΩ**. The divider on the shared sheet stays an owner decision. Calculation in design-notes §3.
- T-0012: check the hardware switch path with a bouncing contact (no output chatter, τ ≈ 1.5 ms). Measure the ON/OFF
  switch voltage (≈ 8 V at the switch, ≈ 8.5 V at the battery).

## Pre-order checklist (T-0065)

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
  1.05 × 0.45 mm pads, 2.6 mm column pitch) against the JLCPCB footprints of C122552 and C5219210. Recheck stock (C122552
  4707, C5219210 2923 on 2026-11-03).
- T-0021: BOM lines without `LCSC` are now only J5, J10, J11 (no part yet, `/system mechanical`), H1/H2 and the DNP
  positions.

## For /system

- T-0121 (sync): the ARCHITECTURE root row should mention the pdm-4ch reverse-battery blocker: VBAT_IN → FL30/JP30 →
  `VBAT_FL` → Q30 IPT007N06N (U30 LM74500-Q1, C32) → VS, on pdm-4ch only (HC2 unchanged, decision 40).
- T-0121 (`/system mechanical`): J10 keyed/polarised on pdm-4ch too (decision 34; owner ruling Q-0054 "Still key J10").
- T-0121 (sync): supply-path budget. ARCHITECTURE says "shared supply path ≤ 2 mΩ". On pdm-4ch, Q30 adds
  ≤ 0.75 mΩ (25 °C) / ≈ 1.05–1.1 mΩ hot. Suggested wording: "terminal + VS copper ≤ 2 mΩ, plus the pdm-4ch blocker Q30
  ≤ 1.1 mΩ hot". The heat budget shows this is harmless (design-notes §8.6: 4 × 4 A Tj +1 K; `--r-path` default 4 mΩ already
  covers it).

- T-0107 (sync): the ARCHITECTURE root row still says "C30 1 µF/100 V". It is now 2.2 µF/100 V C170101 (decision 26 range 1–2.2 µF).
- T-0107 (`/system firmware`): the IS scale constant is now **RIS = 500 Ω** (2 × 1 kΩ). IL = VIS / 500 Ω × kILIS, ≈ 0.33 V/A for the BTT6050 and ≈ 0.128 V/A for the BTT6010 (design-notes §6.1). A sense current of about 5.8 mA reads full scale (2.9 V), below the minimum IIS(FAULT) of 6 mA, so DEN rule 2 still sees every fault.
- T-0069 RIS note below: C17975 is gone again since T-0107. The 40 mA fault case is now 0.8 W in two 0.25 W parts, still covered only by firmware.

- T-0105 (sync): `tools/heat_budget.py --p-other` default 2.2 → 2.3 W (design-notes §4; result unchanged, Tj ≈ 101 °C).

- T-0069: firmware requirements for DEN (design-notes §6.1) belong in the `/system firmware` list. T-0069 swapped one
  unique extended part (−/+): C23228 (basic) is replaced by C17975 (extended, 1206 680 Ω); C25819 (basic) is added.
- RIS at the 40 mA maximum fault current (≈ 1.1 W) is covered only by firmware; hardware cover would need a ≥ 1.5 W
  resistor – owner decision if wanted.

- T-0118: the PTC interrupt-rating problem is settled (decision 81): F1–F4 C70113, R54–R56 0.2 Ω C7420022, unique extended
  parts ±0. A competent person reviews F1–F4 and R54–R56 before installation (F4: panel switches).
- T-0065 unique extended parts: −PESD0402V05, −TPS7B91; +C170101 (2.2 µF/100 V); +C107198 (4.7 nF/1 kV) removed again in T-0119.

- T-0064 added two unique extended parts (C487384 bulk 100 µF/63 V, C13832 1 µF/100 V); no basic/preferred part
  exists. If T-0065/decision 30 needs a 100 V ceramic for C1, reuse C13832 to avoid a third fee.

- Terminal blocks: J5 is still a 2×5 pin header; ~20 poles in 1 module width (power 2, outputs 4, panel 10, CAN 4–5).
