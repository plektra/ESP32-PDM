# pdm-4ch JLCPCB package

**Ready to order (2026-11-22).** Step by step: `ORDER-CHECKLIST.md`. Silkscreen, validation, EMC fixes, footprint
check and CPL corrections are done (`../STATUS.md`).

Regenerate after any board or schematic change (it runs the DRC gate first):

    python3 tools/jlc_package.py pdm-4ch

| File | Upload where |
|---|---|
| `ESP32-PDM-4CH-gerbers.zip` | jlcpcb.com → Order now → Add Gerber file |
| `ESP32-PDM-4CH-bom-jlc.csv` | PCB Assembly step → BOM |
| `ESP32-PDM-4CH-cpl-jlc.csv` | PCB Assembly step → CPL (pick and place) |
| `package-report.md` | not uploaded: DRC gate, parts left out and why, rotations to check |
| `ESP32-PDM-4CH-assembly.pdf` | not uploaded: assembly drawing for bring-up, every reference on F.Fab at 2:1 (decision 224; `kicad-cli pcb export pdf --layers F.Fab,Edge.Cuts --sketch-pads-on-fab-layers --sketch-DNP-footprints-on-fab-layers --black-and-white --mode-single --scale 2`) |

## Quote settings (decisions 99–103, 122, 150)

| Setting | Value |
|---|---|
| Layers | 4 (F.Cu, In1 GND, In2, B.Cu) |
| Size | 100 × 75 mm |
| Thickness | 1.6 mm |
| Outer copper | 2 oz (the load current runs on F.Cu/B.Cu) |
| Inner copper | JLCPCB default for 4 layers with 2 oz outer |
| Surface finish | HASL lead-free (as set in the board file) |
| Smallest via | 0.3 mm drill (380 holes; another 183 of 0.4 mm) |
| Quantity | 5 PCBs, of which 2 assembled (decision 101) |
| Assembly | **Standard PCBA**, top side only (decisions 99, 100, 122); Economic is not offered with 2 oz |
| Fixture fee | check whether the 16.42 USD Standard PCBA fixture fee applies (CONTINUE-FROM-HERE) |

In the BOM/CPL: 199 placed parts, 54 unique LCSC parts (one BOM line per LCSC part), all top side. Left out: DNP parts, H1–H4, J6 (service pads),
JP1/JP30 (copper bridges) and the THT connectors J4, J5, J10, J11, which the owner buys and hand-solders (decision 85).
Their sockets and plugs go in the same cart as separate LCSC parts.

The CPL is corrected against JLCPCB's footprints (`CPL_FIX` in `tools/jlc_package.py`, 24 parts, report
`docs/reviews/2026-11-21-footprints-pdm-4ch.md`); `package-report.md` lists them. In the placement preview they should
already sit right: check, do not rotate them again. D7/D8 need no correction.

## Price check (2026-11-21, `docs/reviews/2026-11-21-cost-pdm-4ch.md`, 5 PCBs / 2 assembled)

Basis: Standard PCBA, top side only. Every unique LCSC line costs 1.53 USD feeder loading, basic and extended alike
(the Economic 3 USD extended-part fee does not apply).

| Item | USD |
|---|---|
| Parts at need quantity (398 pcs, live tier prices) | 37.76 |
| Feeder loading: 54 lines × 1.53 | 82.62 |
| Setup 25.56 + stencil 8.21 + confirm placement 0.45 | 34.22 |
| SMT joints (≈ 560 per board × 0.0016) | 1.79 |
| PCB, 4 layers, 2 oz, 100 × 75 mm, 5 pcs (owner's quote 43.95 EUR) | 49.07 |
| **JLCPCB order** | **205.46** |
| Hand-soldered sockets J4, J5, J10, J11 + plugs for J4, J5, J11 (separate LCSC lines) | 5.00 |
| **First order with connector sets** | **210.46** |
| Fixture fee, if the quote shows it | +16.42 |

Shipping, VAT, duty and minimum-purchase rounding are not included. Unit prices change daily; recheck in the cart.

Extended parts: C844867, C170101, C487384, C2687131, C70113, C165948, C96963, C5464765, C7420022, C52155402,
C2913206, C22427220, C528763, C534868, C5219203. Under Standard PCBA they cost the same 1.53 USD loading fee as basic parts.

Stock flags:
- U30 is LM74502H-Q1 C5219203 (decision 222; the LM74500-Q1 was out of stock): 1993 in stock on 2026-11-21,
  footprint checked 2026-11-21.
- SMAJ30CA C19077548: 23897 in stock on 2026-11-21 (was 172 on 2026-11-17).
- Under 2000 in stock (2026-11-21): L1 C96963 (1173), U11–U14 C534868 (1604), Q30 C5464765 (1650), U30 C5219203 (1993).
  Connectors (2026-11-22): all over 6000, J10 C475108 6023.
- U1 ESP32-S3-MINI-1 is Standard-PCBA-only (already the basis, decision 100).

## BOM-step dry run (owner, 2026-11-17)

JLCPCB matched every line to the LCSC number in our BOM. What it flagged:

- "Multiple lines in the BOM have been matched to the same part" on C307331, C15849 and C28233 (same part under
  different value spellings). Fixed: `tools/jlc_package.py` now writes one line per LCSC part (54 lines).
- SW_BOOT1/SW_RESET1 "Unconfirmed" (generic value `SW_Push`): C318884 TS-1187A-B-A-B is the intended part; confirm it.
- U30 LM74500-Q1 C5219210: 0 at JLCPCB (Source column "0 JLCPCB"). Resolved: U30 is now LM74502H-Q1 C5219203.
