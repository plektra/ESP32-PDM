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

In the BOM/CPL: 199 placed parts, 54 unique LCSC parts (one BOM line per LCSC part), all top side. Left out: DNP parts, H1–H4, J6 (service pads),
JP1/JP30 (copper bridges) and the THT connectors J4, J5, J10, J11, which the owner buys and hand-solders (decision 85).
Their sockets and plugs go in the same cart as separate LCSC parts.

In the placement preview, check the rotation of U3, U11–U14 (EasyEDA draws them rotated 90°) and D7/D8 (C2286 pad 1 =
anode). The CPL uses KiCad's rotation without correction; fix them in the preview.

## Price and stock check (2026-11-17, live LCSC/JLCPCB lookup, 2 assembled boards)

| Item | USD |
|---|---|
| Parts at need quantity (398 pcs, all at the 1+ price) | 38.93 |
| Extended-part loading fees: 14 unique × 3 USD | 42.00 |
| **Parts + fees** | **80.93** |
| Hand-soldered sockets J4, J5, J10, J11 + plugs for J4, J5, J11 (separate LCSC lines) | ≈ 5.01 |

PCB fabrication, Standard PCBA setup/stencil and shipping come from the JLCPCB quote page and are not included.
Unit prices change daily; recheck in the cart.

Extended parts (fee each): C170101, C487384, C2687131, C70113, C165948, C96963, C5464765, C7420022, C52155402,
C2913206, C22427220, C528763, C534868, C5219210. Everything else is basic or preferred (no fee).

Stock flags:
- **U30 LM74500-Q1 C5219210: out of stock (0)**, minimum order 5. Blocks the order until it is restocked or the owner
  pre-orders it as a global sourcing/consigned part. Its footprint check (T-0121) is still open too.
- **D1, D16–D19, D50–D54 SMAJ30CA C19077548: 172 in stock** for 20 needed, so it is thin. JLCPCB's minimum purchase is
  293 pcs (≈ 9 USD at the 100+ price).
- Under 2000 in stock: L1 C96963 (1173), U3 C22427220 (1524), U11–U14 C534868 (1604), Q30 C5464765 (1650),
  J10 C475108 (821).
- U1 ESP32-S3-MINI-1 is Standard-PCBA-only (already the basis, decision 100).

## BOM-step dry run (owner, 2026-11-17)

JLCPCB matched every line to the LCSC number in our BOM. What it flagged:

- "Multiple lines in the BOM have been matched to the same part" on C307331, C15849 and C28233 (same part under
  different value spellings). Fixed: `tools/jlc_package.py` now writes one line per LCSC part (54 lines).
- SW_BOOT1/SW_RESET1 "Unconfirmed" (generic value `SW_Push`): C318884 TS-1187A-B-A-B is the intended part; confirm it.
- U30 LM74500-Q1 C5219210: 0 at JLCPCB (Source column "0 JLCPCB"); still the open stock blocker above.
