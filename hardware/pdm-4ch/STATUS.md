# pdm-4ch status

Updated: 2026-11-02

**Where it stands:** schematic complete (scripted edits), ERC: 5 `lib_symbol_mismatch` notices only (since T-0066). Netlist checked
after every edit. No PCB. Decisions 1–7, 9–14, 17, 18 apply. Panel connector J5 and the pin map changed on
2026-10-30 (decisions 17, 18): SW_SUPPLY on J5.5, MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9,
channel-4 drive moved to IO11.

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

## For /system

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
