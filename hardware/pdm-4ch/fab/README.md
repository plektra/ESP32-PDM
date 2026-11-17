# pdm-4ch JLCPCB package

**For quoting only, not for ordering yet.** Still open before an order: silkscreen (layout stage 6), `/validate pdm-4ch`
on the PCB, EMC E22/E23 (`docs/reviews/2026-11-17-emc-pdm-4ch.md`) and the pre-order checklist in `../STATUS.md`.

Regenerate after any board or schematic change (it runs the DRC gate first):

    python3 tools/jlc_package.py pdm-4ch

| File | Upload where |
|---|---|
| `ESP32-PDM-4CH-gerbers.zip` | jlcpcb.com → Order now → Add Gerber file |
| `ESP32-PDM-4CH-bom-jlc.csv` | PCB Assembly step → BOM |
| `ESP32-PDM-4CH-cpl-jlc.csv` | PCB Assembly step → CPL (pick and place) |
| `package-report.md` | not uploaded: DRC gate, parts left out and why, rotations to check |

## Quote settings (decisions 99–103, 122, 150)

| Setting | Value |
|---|---|
| Layers | 4 (F.Cu, In1 GND, In2, B.Cu) |
| Size | 100 × 75 mm |
| Thickness | 1.6 mm |
| Outer copper | 2 oz (the load current runs on F.Cu/B.Cu) |
| Inner copper | JLCPCB default for 4 layers with 2 oz outer |
| Surface finish | HASL lead-free (as set in the board file) |
| Smallest via | 0.3 mm drill (507 vias) |
| Quantity | 5 PCBs, of which 2 assembled (decision 101) |
| Assembly | **Standard PCBA**, top side only (decisions 99, 100, 122); Economic is not offered with 2 oz |
| Fixture fee | check whether the 16.42 USD Standard PCBA fixture fee applies (CONTINUE-FROM-HERE) |

In the BOM/CPL: 199 placed parts, 54 unique LCSC parts, all top side. Left out: DNP parts, H1–H4, J6 (service pads),
JP1/JP30 (copper bridges) and the THT connectors J4, J5, J10, J11, which the owner buys and hand-solders (decision 85).
Their sockets and plugs go in the same cart as separate LCSC parts.

In the placement preview, check the rotation of U3, U11–U14 (EasyEDA draws them rotated 90°) and D7/D8 (C2286 pad 1 =
anode). The CPL uses KiCad's rotation without correction; fix them in the preview.
