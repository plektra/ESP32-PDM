# pdm-hc2 status

Updated: 2026-11-02

**Where it stands:** schematic complete (scripted), ERC: 5 `lib_symbol_mismatch` notices only (since T-0066); netlist checked.
TPS48110A-Q1 + 2 × BSC030N08NS5 per channel, values in `docs/design-notes.md` §4a. No PCB. Decisions 1–6, 8–15, 17, 18
apply. Shared `analog_sw` sheet and controller pin map updated on 2026-10-30 (same as `pdm-4ch`): SW_SUPPLY on J5.5,
MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9.

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

**Blocked (owner, one-way):** the PTC check failed. 1812L050/60GR is rated I_max 40 A, but a hard short behind F1/F3/F4
can draw ≈ 188 A (30 V / 0.16 Ω). F2 therefore stays SMD0805B050TF. Question in the T-0065 report.

**Waiting for the owner:** decision 19 **[proposed]** (21 A MOSFET option, halogen inrush), which depends on the
searchlight choice (decision 16, open). Decision 21 **[proposed]** (SW_SUPPLY sense on IO12).

## Next

1. Open in KiCad: tidy the label-wired `hc_channel` sheet and the parts the panel-cable script placed, *Update
   Symbols from Library* (keep Q3–Q6 on the BC817 symbol with value MMBT5551), ERC.
2. `/validate pdm-hc2 deep` (part facts of TPS48110A-Q1, BSC030N08NS5, the equations) and `/emc pdm-hc2`.
3. Verify the custom footprint `Texas_DGX0019A_VSSOP-19_3x5.1mm_P0.5mm` against the JLCPCB footprint (C17556513).
4. Searchlight: if it stays ~21 A, check NTMFS5C612NL (SO-8FL) against the TDSON-8-1 footprint and rerun the heat
   budget; if halogen, decide the short-circuit setting after a MOSFET SOA check.
5. PCB: Kelvin sense on the 1 mΩ shunt, MMBT3904 between the MOSFETs, TH1 next to the MOSFETs, ≥ 25 A output
   terminals, ≈ 50 A input.
   T-0064 rules (design-notes §8.1/§8.2):
   - **D103/D203 next to the J11 terminal, GND return a short, wide path straight to J10.2** (not via the logic
     ground); decision 27.
   - JP30 (VBAT_IN–VS) as a copper bridge as wide as the VS copper for ≈ 50 A (the placeholder footprint
     `NetTie-2_SMD_Pad2.0mm` is far too small); FL30 has no footprint yet, decided at pre-compliance.
   - D30, C30 at the J10 terminals; C31 near J10; C106/C206 at each channel's VS next to RSNS/Q11.
   - C30 (MLCC on the battery input) away from the terminal screws, board edges and bending lines.
   T-0065 layout rules (design-notes §8.3): C19 (100 nF) right at U3 VIN/GND; R44/C20 footprints tight at the SW
   node; R13/C18/R14 at J3 next to the shield tabs; U6 DPAK with copper under the tab (≈ 0.5 W); C1 1206 away from
   board edges and screws.
6. Cost lever: R1/R2 (2.2 k pull-downs on IO8/IO11, left over from the 4-ch drive) have no function here – remove
   in `/cost` or keep the controller part identical to `pdm-4ch`.

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

- **Bilge output fusing (T-0064 failure mode, needs README/installation rule):** D103/D203 sit outside the
  back-to-back MOSFETs. If a TVS fails short, a float-switch run feeds the short through the PDM output wire. The
  float circuit stays independent (invariant 8) only if the PDM leg has its own fuse, between J11 and the junction
  with the float circuit, that opens before the float fuse. Add this to the README next to the external breaker of
  decision 39; a competent person reviews the bilge wiring before installation.
- T-0064 added two unique extended parts (C487384, C13832); see pdm-4ch STATUS.

- Module width: probably 2 module widths because of the terminals; confirm with the enclosure.
