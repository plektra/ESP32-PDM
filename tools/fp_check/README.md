# Footprint check against the JLCPCB (EasyEDA) footprints

Scripted comparison of a board's KiCad pads with the EasyEDA footprints JLCPCB places from. First run:
`docs/reviews/2026-11-21-footprints-pdm-4ch.md`. Work files go to a temporary directory, not the repo.

```
KPY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$KPY tools/fp_check/dump_pads.py hardware/pdm-4ch/ESP32-PDM-4CH.kicad_pcb $T/pads.json   # KiCad pads, footprint frame
python3 -I tools/fp_check/fetch_fp.py $T/easy.json C844867 C5464765 ...                  # EasyEDA pads (pcbparts MCP)
python3 -I tools/fp_check/compare.py $T/pads.json $T/easy.json > $T/cmp.txt              # rotation, origin offset, lands
python3 -I tools/fp_check/raw.py $T/pads.json $T/easy.json Q30=C5464765                   # raw pads of one part
python3 -I tools/fp_check/cpl_fix.py hardware/pdm-4ch/fab/ESP32-PDM-4CH-cpl-jlc.csv REF=LCSC ...  # corrected CPL rows
```

`compare.py` fits by pad **number**. For polarised two-pin parts check the EasyEDA pin names against the nets
(D7/D8: EasyEDA pad 1 = anode, KiCad pad 1 = cathode, so the number fit's 180° is wrong and 0° is right).
Rotation convention: JLCPCB rotation = KiCad rotation + the correction (both counter-clockwise; SOT-23 +180°,
SOIC +270°, as in the usual JLCPCB rotation tables). The `FIX` table in `cpl_fix.py` holds the pdm-4ch results.

After a rebuild, cross-check the CPL: `$KPY tools/fp_check/verify_cpl.py <board>.kicad_pcb fab/<stem>-cpl-jlc.csv $T/easy.json`
(places the EasyEDA pads by the CPL and reports the distance to the board pads per part).
