# pdm-hc2 status

Updated: 2026-11-01

**Where it stands:** schematic complete (scripted), ERC: 6 `lib_symbol_mismatch` notices only; netlist checked.
TPS48110A-Q1 + 2 × BSC030N08NS5 per channel, values in `docs/design-notes.md` §4a. No PCB. Decisions 1–6, 8–15, 17, 18
apply. Shared `analog_sw` sheet and controller pin map updated on 2026-10-30 (same as `pdm-4ch`): SW_SUPPLY on J5.5,
MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9.

**2026-11-01 (T-0064, decisions 26/27, unattended):** battery input J10 now has D30 + C30 (1 µF/100 V) on the
terminal net `VBAT_IN`, a DNP ferrite position FL30 bridged by the copper net tie JP30 to `VS`, and C31 100 µF/63 V
on VS (same controller part as 4-ch). HC2-only: C106/C206 100 µF/63 V on VS per channel (3 × 100 µF in total), and
D103/D203 SMAJ33CA (C19077549, preferred) from each OUT to GND at J11. ERC unchanged (6 `lib_symbol_mismatch`),
netlist checked. Details, part facts and the bilge-output failure mode: design-notes §8.1/§8.2.

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
6. Cost lever: R1/R2 (2.2 k pull-downs on IO8/IO11, left over from the 4-ch drive) have no function here – remove
   in `/cost` or keep the controller part identical to `pdm-4ch`.

## For /system

- **Bilge output fusing (T-0064 failure mode, needs README/installation rule):** D103/D203 sit outside the
  back-to-back MOSFETs. If a TVS fails short, a float-switch run feeds the short through the PDM output wire. The
  float circuit stays independent (invariant 8) only if the PDM leg has its own fuse, between J11 and the junction
  with the float circuit, that opens before the float fuse. Add this to the README next to the external breaker of
  decision 39; a competent person reviews the bilge wiring before installation.
- T-0064 added two unique extended parts (C487384, C13832); see pdm-4ch STATUS.

- Module width: probably 2 module widths because of the terminals; confirm with the enclosure.
