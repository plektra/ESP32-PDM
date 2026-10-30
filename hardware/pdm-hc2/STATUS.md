# pdm-hc2 status

Updated: 2026-10-30

**Where it stands:** schematic complete (scripted), ERC: 6 `lib_symbol_mismatch` notices only; netlist checked.
TPS48110A-Q1 + 2 × BSC030N08NS5 per channel, values in `docs/design-notes.md` §4a. No PCB. Decisions 1–6, 8–15, 17, 18
apply. Shared `analog_sw` sheet and controller pin map updated on 2026-10-30 (same as `pdm-4ch`): SW_SUPPLY on J5.5,
MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9.

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
6. Cost lever: R1/R2 (2.2 k pull-downs on IO8/IO11, left over from the 4-ch drive) have no function here – remove
   in `/cost` or keep the controller part identical to `pdm-4ch`.

## For /system

- Module width: probably 2 module widths because of the terminals; confirm with the enclosure.
