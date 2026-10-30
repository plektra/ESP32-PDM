# pdm-hc2 status

Updated: 2026-10-30

**Where it stands:** schematic complete (scripted), ERC: 6 `lib_symbol_mismatch` notices only; netlist checked.
TPS48110A-Q1 + 2 × BSC030N08NS5 per channel, values in `docs/design-notes.md` §4a. No PCB. Decisions 1–6, 8–15 apply.

**Waiting for the owner:** decision 19 **[proposed]** (21 A MOSFET option, halogen inrush). Depends on the
searchlight choice (decision 16, open: halogen or LED + heated glass).

## Next

1. Open in KiCad: tidy the label-wired `hc_channel` sheet, *Update Symbols from Library*, ERC.
2. `/validate pdm-hc2 deep` (part facts of TPS48110A-Q1, BSC030N08NS5, the equations) and `/emc pdm-hc2`.
3. Verify the custom footprint `Texas_DGX0019A_VSSOP-19_3x5.1mm_P0.5mm` against the JLCPCB footprint (C17556513).
4. Searchlight: if it stays ~21 A, check NTMFS5C612NL (SO-8FL) against the TDSON-8-1 footprint and rerun the heat
   budget; if halogen, decide the short-circuit setting after a MOSFET SOA check.
5. PCB: Kelvin sense on the 1 mΩ shunt, MMBT3904 between the MOSFETs, ≥ 25 A output terminals, ≈ 50 A input.

## For /system

- Same shared-sheet items as `pdm-4ch` (panel connector, battery voltage).
- Module width: probably 2 module widths because of the terminals; confirm with the enclosure.
