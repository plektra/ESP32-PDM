# pdm-4ch status

Updated: 2026-11-03 (T-0078)

**Where it stands:** schematic complete (scripted edits), ERC: 5 `lib_symbol_mismatch` notices only (since T-0066). Netlist checked
after every edit. No PCB. Decisions 1–7, 9–14, 17, 18 apply. Panel connector J5 and the pin map changed on
2026-10-30 (decisions 17, 18): SW_SUPPLY on J5.5, MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9,
channel-4 drive moved to IO11.

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
5 warnings (unchanged). +1 part, +1 unique part. **Blocked:** T-0046 (R3/R4/R7/R8 split): no basic 1206 2.2 k / 2.4 k
exists; question for the owner in `docs/reviews/2026-11-02-fix-shared-T-0068.md`.

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

**Blocked (owner, one-way):** the PTC check failed. 1812L050/60GR is rated I_max 40 A, but a hard short behind F1/F3/F4
can draw ≈ 188 A (30 V / 0.16 Ω). F2 therefore stays SMD0805B050TF. Question in the T-0065 report.

**Waiting for the owner:** decision 21 **[proposed]** (sense SW_SUPPLY on IO12 so a tripped F4 can be reported).

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
   T-0065 layout rules (design-notes §8.3): C19 (100 nF) right at U3 VIN/GND; R44/C20 footprints tight at the SW
   node; R13/C18/R14 at J3 next to the shield tabs; U6 DPAK with copper under the tab (≈ 0.5 W); C1 1206 away from
   board edges and screws.
7. Before ordering: check the `CP_Elec_8x10` and `C_1206` footprints against the JLCPCB footprints of C487384
   and C13832; before fitting D103–D403 read the demagnetisation note in design-notes §8.2.

**PCB rule 9 – isolation barrier (EMC review 2026-10-30, updated T-0067):** no copper (pour, trace, via) under U5
between pins 1–4 and 5–8. Keep the GND and GND_CAN islands apart around the body by the package creepage (CA-IS3050G
SOIC-8-WB: 8 mm CLR/CPG), at least ≥ 4 mm. **C70 is the only part that crosses the gap**, on its own pads next to
U5. D9, D10, F3, FB2, D11, U6, FL1, R71/R72 sit on the GND_CAN side; U5 pins 1–4 and R70 on the GND side. FL1 and
R71/R72 go between D9 and U5 (D9 at J4).

## Prototype test list

- **T-0042 / Q-0034 – switch-path margin:** measure IN − device GND (U11–U14 pin IN vs the channel's ground network) at
  SWIN = 10.5 V with the channel on, once with the 3.3 V rail removed and once with it present. Repeat at a 10.5 V battery
  with D55's drop (SWIN ≈ 9.8–10.1 V). Pass: ≥ 2.0 V (VIN(H) min). If short, the planned fix is **RIN R101/R201/R301/R401 →
  4.7 kΩ**. The divider on the shared sheet stays an owner decision. Calculation in design-notes §3.
- T-0012: check the hardware switch path with a bouncing contact (no output chatter, τ ≈ 1.5 ms). Measure the ON/OFF
  switch voltage (≈ 8 V at the switch, ≈ 8.5 V at the battery).

## Pre-order checklist (T-0065)

- Recheck JLCPCB stock of the thin parts: TPS48110A (HC2), L1 SWPA6045S8R2MT (1231 on 2026-11-02), BTT6050 (4-ch),
  LMR51610YF (only if the scan asks for FPWM), plus the new C170101 and C107198.
- L1 approved alternates (datasheet-checked, same 8.2 µH / 0.056 Ω max / I_sat 3.9 A / I_rms 2.6 A / 6045 land):
  **Sunltech SLW6045S8R2MST C47018494** (no EasyEDA footprint at JLCPCB – map it to the SWPA land) and
  **cjiang FNR6045S8R2MT C168074**.
- H5VL10B has no published TLP curve (8/20 µs clamp only); accepted on that data (design-notes §8.3).
- Check the KiCad footprints `D_SOD-882`, `TO-252-2`, `L_0805_2012Metric` against the JLCPCB footprints of C7420372,
  C58069, C1017.
- Resolve the F1/F3/F4 PTC I_max question before ordering.
- T-0067: check the KiCad footprints `SOIC-8_7.5x5.85mm_P1.27mm` (U5) and `L_CommonModeChoke_Coilank_ACM4532`
  (FL1) against the JLCPCB footprints of C528763 and C20624726. The FL1 pad numbering must match windings 1→2 / 4→3
  before FL1 is ever fitted (design-notes §8.5).
- T-0051 (production / flashing): never burn eFuse `EFUSE_STRAP_JTAG_SEL` – IO3 is held low by the IS2 network
  (design-notes §2).
- T-0021: BOM lines without `LCSC` are now only J5, J10, J11 (no part yet, `/system mechanical`), H1/H2 and the DNP
  positions.

## For /system

- T-0073: decision 18's "33 V full scale" is amended to ≈ 32 V (decision 38, design-notes §2).
- T-0068/T-0047: `tools/heat_budget.py --p-other` default is still 0.6 W. design-notes §4 documents ≈ 2.2 W for the 4-ch
  board at 30 V with all panel lines on (Tj 101 °C vs 100 °C). Raise the default or its help text in a tools session.
- T-0068/T-0046 blocked (owner): no basic 1206 2.2 k / 2.4 k. Options: 2 k + 2 k basic (C17944) or 2.2 k + 2.4 k
  extended. R3/R4/R7/R8 stay 4.7 k for now (0.19 W at 30 V, 77 %).

- T-0069: firmware requirements for DEN (design-notes §6.1) belong in the `/system firmware` list. T-0069 swapped one
  unique extended part (−/+): C23228 (basic) is replaced by C17975 (extended, 1206 680 Ω); C25819 (basic) is added.
- RIS at the 40 mA maximum fault current (≈ 1.1 W) is covered only by firmware; hardware cover would need a ≥ 1.5 W
  resistor – owner decision if wanted.

- T-0067: ARCHITECTURE `can` row says "ISO1044"; it is now CA-IS3050G (SOIC-8-WB, ≈ 7.5 × 11.5 mm with leads) plus
  DNP FL1/C70 and fitted R70–R72. LEN recheck: 49.3 mA worst case (LEN 1, 0.7 mA margin) / 79.8 mA continuous
  dominant (LEN 2). Measure the NET-S current on the first prototype.
- T-0065: ARCHITECTURE `can` row still says "TPS7B91"; it is now L78M05ABDT (DPAK, ≈ 10.4 × 6.7 mm footprint –
  include in the `/system mechanical` area budget). The NET-S current stays LEN 1 (normal traffic 44.8 mA) / LEN 2
  (continuous dominant 76.8 mA), only 5 mA margin to 50 mA. Recheck if the CAN transceiver changes (T-0030).
- T-0065: the PTC interrupt-rating problem (F1/F3/F4, I_max 40 A vs ≈ 188 A) is a system protection question for the
  owner; F4 feeds the panel switches (bilge forced run, navigation lights), so a competent person reviews it.
- T-0065 unique extended parts: −PESD0402V05, −TPS7B91; +C170101 (2.2 µF/100 V), +C107198 (4.7 nF/1 kV).

- T-0064 added two unique extended parts (C487384 bulk 100 µF/63 V, C13832 1 µF/100 V); no basic/preferred part
  exists. If T-0065/decision 30 needs a 100 V ceramic for C1, reuse C13832 to avoid a third fee.
- ARCHITECTURE "Shared sheets" table, root row: add C30/C31, FL30 (DNP)/JP30 and net VBAT_IN to the battery input
  description (only invariant 4 was changed in T-0064).

- Terminal blocks: J5 is still a 2×5 pin header; ~20 poles in 1 module width (power 2, outputs 4, panel 10, CAN 4–5).
