# pdm-4ch status

Updated: 2026-11-01

**Where it stands:** schematic complete (scripted edits), ERC: 6 `lib_symbol_mismatch` notices only. Netlist checked
after every edit. No PCB. Decisions 1–7, 9–14, 17, 18 apply. Panel connector J5 and the pin map changed on
2026-10-30 (decisions 17, 18): SW_SUPPLY on J5.5, MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9,
channel-4 drive moved to IO11.

**2026-11-01 (T-0064, decisions 26/27, unattended):** battery input J10 now has D30 + C30 (1 µF/100 V) on the
terminal net `VBAT_IN`, a DNP ferrite position FL30 bridged by the copper net tie JP30 to `VS`, and C31 100 µF/63 V
bulk on VS (same controller part as HC2). Each channel has C104 1 µF/100 V at the BTT6050 VS tab and a DNP SMAJ30CA
D103 from OUT to GND (refs x04/x03 per channel). Invariant 4 now states the PROFET output rule. ERC unchanged
(6 `lib_symbol_mismatch`), netlist checked. Details and failure-mode notes: design-notes §8.1/§8.2.

**Waiting for the owner:** decision 21 **[proposed]** (sense SW_SUPPLY on IO12 so a tripped F4 can be reported).

## Next

1. Open in KiCad: tidy what the scripts placed (labels, part positions; the new parts in `analog_sw` and the
   VBAT/NTC block at the bottom of the root sheet), run *Update Symbols from Library* (LMR51610, USB-C; keep Q3–Q6
   on the BC817 symbol with value MMBT5551 – same pinout), then ERC.
2. After `/emc pdm-4ch` and `/validate pdm-4ch deep`: fix findings.
3. Verify the custom footprint `Infineon_PG-TDSO-14_ThermalVias` against the JLCPCB/EasyEDA footprint (C534868).
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
7. Before ordering: check the `CP_Elec_8x10` and `C_1206` footprints against the JLCPCB footprints of C487384
   and C13832; before fitting D103–D403 read the demagnetisation note in design-notes §8.2.

## For /system

- T-0064 added two unique extended parts (C487384 bulk 100 µF/63 V, C13832 1 µF/100 V); no basic/preferred part
  exists. If T-0065/decision 30 needs a 100 V ceramic for C1, reuse C13832 to avoid a third fee.
- ARCHITECTURE "Shared sheets" table, root row: add C30/C31, FL30 (DNP)/JP30 and net VBAT_IN to the battery input
  description (only invariant 4 was changed in T-0064).

- Terminal blocks: J5 is still a 2×5 pin header; ~20 poles in 1 module width (power 2, outputs 4, panel 10, CAN 4–5).
