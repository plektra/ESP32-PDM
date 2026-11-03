# Cost review – system (pdm-4ch and pdm-hc2), after the schematic fix rounds

Date: 2026-11-03. Task T-0086, unattended. Reviewer: cost-controller. No PCB exists yet and no board is ordered
(`docs/queue.json` `"ordered": null`). Earlier report: `2026-10-30-cost-system.md` (baseline, T-0002).

Sources read: `CLAUDE.md`, `docs/AUTONOMY.md`, `docs/decisions.md` (1–71), `docs/CONTINUE-FROM-HERE.md`,
`docs/design-notes.md` §RIS/DEN and F2 notes, both `STATUS.md` files, the owner inbox, the 2026-10-30 cost report.

Method:
- BOMs: `kicad-cli sch export bom --exclude-dnp` from both root sheets, grouped by value, footprint and LCSC. DNP
  parts (D103–D403 on 4-ch, C20/R44 snubber, C70, FL1, R14 …) are not in the totals because JLCPCB does not place them.
- Joint counts: pad counts per reference from `kicad-cli sch export netlist --format kicadxml` (4-ch 504 SMT + 20 THT,
  HC2 536 SMT + 18 THT).
- Library type, stock and price: pcbparts `jlc_search` / `jlc_get_part`, all 72 distinct LCSC codes, 2026-11-03.
- Cost model: `$CLAUDE_JOB_DIR/scripts/costmodel.py`.

## Figures

### Where the numbers come from (all fetched 2026-11-03)

| Item | Figure | Source |
|---|---|---|
| Economic PCBA setup | 8.18 $ per design per order | [JLCPCB PCBA price](https://jlcpcb.com/help/article/pcb-assembly-price), "last updated Oct 22, 2026" |
| Economic stencil | 1.53 $ | same page |
| Extended part loading | **3.07 $** per unique extended part; basic and preferred are free (Standard PCBA: 1.53 $ for every unique part) | same page, unchanged since 2026-10-30 |
| Confirm parts placement | 0.45 $ | same page |
| THT hand soldering | 3.58 $ per order + 0.0164 $ per joint (manual-assembly rate; the page lists no separate THT rate) | same page |
| SMT placement | 0.0016 $ per joint | same page |
| Standard PCBA (comparison) | 25.56 $ setup + 8.21 $ stencil (single side) | same page |
| Part prices | LCSC tier price for the six big parts (BTT6050, TPS48110A, ESP32-S3-MINI-1-N8, CA-IS3050G, LMR51610Y, BSC030N08NS5) at order qty × count; **the 1+ price for all other parts** (slightly high, < 0.3 $ per board) | pcbparts `jlc_get_part`, 2026-11-03 |
| **PCB, 2 layers, 2 oz, ≈ 85 × 55 mm** | **ESTIMATE, unchanged:** 15 $ (5 pcs), 20 $ (10), 38 $ (30), ± 50 % | No live quote was possible. A web search on 2026-11-03 found no JLCPCB 2 oz price; the JLCPCB [copper-weight page](https://jlcpcb.com/help/article/jlcpcb-copper-weight) lists 2 oz as available without a price. |

Placeholders: J5 (10-pole header) 0.18 $, J10 0.57 $ (KF135T-10.16-2P, C475108), J11 0.30 $ (4-ch) / 0.29 $ (HC2) are the
2026-10-30 estimates; no part has been chosen (`/system mechanical`) and each is counted as one extended part.
Not in the totals: shipping, customs, VAT, JLCPCB attrition, plug halves (1.20 $/board, estimate from 2026-10-30:
C7244 0.33 $ + C26865 0.87 $), enclosure (≈ 1 $ printed ASA, estimate), panel switches and wiring.

### Per board, Economic PCBA, 2 oz (PCB price is an estimate)

| Board | Qty | Parts | Joints | Fixed per order¹ | PCB per order (est.) | **Per board** | Order total |
|---|---|---|---|---|---|---|---|
| pdm-4ch (4 × BTT6050) | 5 | 16.34 $ | 1.13 $ | 72.07 $ | 15 $ | **34.88 $** | 174.42 $ |
| pdm-4ch | 10 | 15.08 $ | 1.13 $ | 72.07 $ | 20 $ | **25.42 $** | 254.22 $ |
| pdm-4ch | 30 | 14.24 $ | 1.13 $ | 72.07 $ | 38 $ | **19.04 $** | 571.20 $ |
| pdm-hc2 | 5 | 21.93 $ | 1.15 $ | 75.14 $ | 15 $ | **41.12 $** | 205.58 $ |
| pdm-hc2 | 10 | 20.52 $ | 1.15 $ | 75.14 $ | 20 $ | **31.19 $** | 311.89 $ |
| pdm-hc2 | 30 | 19.14 $ | 1.15 $ | 75.14 $ | 38 $ | **24.07 $** | 722.02 $ |

¹ Setup 8.18 + stencil 1.53 + confirm 0.45 + THT labour 3.58 + extended parts × 3.07: **19** on pdm-4ch (72.07 $), **20**
on pdm-hc2 (75.14 $), J5/J10/J11 included. Per board add ≈ 2.2 $ for plug halves and enclosure.

Both boards ordered separately in the same run: 380.00 $ (5 + 5), 566.12 $ (10 + 10), 1 293.22 $ (30 + 30).

If 2 oz forces **Standard PCBA** (Q-0026 still open), per board: 4-ch 47.31 / 31.63 / 21.11 $, HC2 55.99 / 38.62 / 26.55 $ at
5 / 10 / 30 (+ 12.4 / 6.2 / 2.1 $ and + 14.9 / 7.4 / 2.5 $). 63 and 73 unique parts at 1.53 $.

Population options (pdm-4ch): a BTT6010-1ERA (C534858) costs 3.20 $ at 1+ against 1.28 $ for the BTT6050, so about
**+1.6 to +1.9 $ per channel** (no tier table fetched); the first BTT6010 in a build adds one 3.07 $ extended fee per order.
Decision 36 fixes the standard population at four BTT6050, so these figures are for reference only.

### Top cost drivers at 10 units

**pdm-4ch** (25.42 $):

| Driver | Per board | Share |
|---|---|---|
| 19 extended-part fees (58.3 $/order) | 5.83 $ | 23 % |
| 4 × BTT6050 (C534868, 1.0972 $ at 30+) | 4.39 $ | 17 % |
| ESP32-S3-MINI-1-N8 (C2913206, 4.1788 $) | 4.18 $ | 16 % |
| PCB 2 oz (estimate) | 2.00 $ | 8 % |
| Setup, stencil, confirm, THT labour | 1.37 $ | 5 % |
| SMT + THT joints | 1.13 $ | 4 % |
| LMR51610Y (C22427220) | 1.08 $ | 4 % |
| CA-IS3050G (C528763) | 0.92 $ | 4 % |
| J10/J11/J5/J4 terminals | ≈ 1.1 $ | 4 % |
| Rest (≈ 45 lines) | ≈ 3.4 $ | 13 % |

**pdm-hc2** (31.19 $):

| Driver | Per board | Share |
|---|---|---|
| 2 × TPS48110AQDGXRQ1 (C17556513, 3.285 $) | 6.57 $ | 21 % |
| 20 extended-part fees (61.4 $/order) | 6.14 $ | 20 % |
| ESP32-S3-MINI-1-N8 | 4.18 $ | 13 % |
| 4 × BSC030N08NS5 (C501507, 0.6561 $ at 30+) | 2.62 $ | 8 % |
| PCB 2 oz (estimate) | 2.00 $ | 6 % |
| Setup, stencil, confirm, THT labour | 1.37 $ | 4 % |
| SMT + THT joints | 1.15 $ | 4 % |
| LMR51610Y | 1.08 $ | 3 % |
| CA-IS3050G | 0.92 $ | 3 % |
| 4 × C487384 100 µF/63 V + 1 mΩ shunts + SS510B | ≈ 1.5 $ | 5 % |

At 5 boards the fixed costs are 41 % (4-ch) / 37 % (HC2) of the price; at 30 boards 12 % / 11 %.

### Change since the last report (2026-10-30)

| Item | 4-ch @10 | HC2 @10 |
|---|---|---|
| Then | 24.87 $ | 30.49 $ |
| **Now** | **25.42 $** | **31.19 $** |
| Change | **+0.55 $** | **+0.70 $** |

Why (rounded; the last report used tier prices for every part, this one uses 1+ prices for the small parts, which
accounts for about +0.2 $ of the difference):
- Extended fees: 17 → **19** (4-ch), 19 → **20** (HC2): +0.61 $ and +0.31 $ per board at 10.
  New extended parts: C13832 (1 µF/100 V, decision 41), C170101 (2.2 µF/100 V, decision 48), C487384 (100 µF/63 V, decision 41),
  C107198 (4.7 nF/1 kV, decision 46), C17975 (680 Ω 1206, 4-ch only, decision 52).
  Removed: BLM18AG601SN1D, PESD0402V05, TPS7B91, ISO1044 (decision 45); the CA-IS3050G replaces the ISO1044, so the count stays.
- Cheaper: CA-IS3050G for ISO1044 (−0.71 $, decision 61); FB, ESD diodes and LDO now basic or preferred (decision 45).
- More parts: C31/C106/C206 bulk capacitors, C30/C104–C404 100 V caps, HC2 slew, filter and sense parts (decisions 25, 41–44, 57–60, 68).
- Stock of the two thinnest parts: TPS48110A 999 → **989**; L1 1 231 → 1 231; BTT6050 1 748 → 1 748.

## Levers

Ranked by saving per board at 10 units (order-size and panel levers first, they apply to everything). "Order" = per
order.

| # | Saving | What changes | Trade-off | Must-stay check | Effort | Evidence |
|---|---|---|---|---|---|---|
| L1 | 30 instead of 10 per order: **−6.38 $** (4-ch) / **−7.12 $** (HC2) per board; 10 instead of 5: **−9.46 / −9.93 $** | Order quantity | Cash up front (+316 $ / +411 $ for 30 against 10); stock on the shelf if the design changes. First order is 5 + 5 by Q-0027 | nothing cut | none | Figures table |
| L2 | **−62.9 $ per order** when both boards are ordered: −6.29 $ per board at 5 + 5, −3.15 $ at 10 + 10, −1.05 $ at 30 + 30 | One panel, one PCBA design: saves one setup, stencil, confirm and THT labour (13.74 $) and 16 shared extended fees (49.12 $); J11 differs per board and is counted twice | Fixed 1 : 1 ratio; JLCPCB surcharge for different designs in a panel not verified (already decision 33, conditional) | nothing cut | layout (PCB phase) | 16 shared codes: C107198, C13832, C165948, C170101, C19078719, C22427220, C2687131, C269104, C2913206, C487384, C52155402, C528763, C8410, C96963, J5, J10 |
| L3 | **−1.62 $** per board at 10 (−3.24 $ at 5, −0.54 $ at 30), −16.2 $ per order and design | Leave the four through-hole connectors (J4, J5, J10, J11) off the PCBA order and solder them by hand: removes 4 extended fees (12.28 $), the THT labour (3.58 $) and 20 joints (0.33 $) | Owner buys the connectors separately (shipping not priced), solders 18–20 joints per board, including the high-current terminals J10/J11; a cold joint on a 40–50 A terminal is a risk the JLCPCB step has not | nothing cut, the parts stay; heat-budget ratings depend on the terminal solder joint, so the owner's joint quality matters | the owner's time | `Figures` fee lines; no connector is chosen yet |
| L4 | **−1.20 $** per board at 10 (−0.90 $ if L5 is taken) | USB-C fitted only as service pads: removes J3, F2, C18, R13, D4–D6, FB1, R11/R12 and 3 extended fees (C165948, C269104, C107198) | Flashing and service need a jig or OTA; decision 31 keeps USB-C fitted on the prototype run | USB is not in the switch → output path; no external-line protection is lost because the port goes | small | Part prices above; decision 31 |
| L5 | **−0.31 $** per board at 10 on both boards (−6.14 $ per order for both, −3.07 $ if panelled) | C18 USB-shield capacitor 4.7 nF/1 kV (C107198, extended) → **1 nF/2 kV C9196** (basic, already on the BOM as C50–C53); the RC corner of R13 ‖ C18 moves from 34 Hz to 160 Hz. No basic 4.7 nF ≥ 500 V part exists (`jlc_search` no_fee: 0 results) | The shield-to-GND filter is a little less lossy for ESD energy; decision 46 is an agent's (auto), the choice was for a standard value | EMC: shield RC is a footprint for the pre-compliance scan; no switch path or protection is cut | one line in `ksch.py`, a footprint stays 1206 | `jlc_get_part` C107198 extended, C9196 basic |
| L6 | **−0.82 $** per board at 10, **−8.18 $ per order** (UNVERIFIED) | Use JLCPCB's monthly "free assembly" coupon, which waives the 8 $ setup for 1–6 layer boards | The blog gives no conditions on copper weight, board size or Economic PCBA and no end date; the coupon needs an order over 1 $ and is issued each month in the account | nothing cut | owner checks the cart | [JLCPCB blog](https://jlcpcb.com/blog/free-assembly-for-1-6-layer-pcbs-and-discounts-on-8-20-layer-pcba), fetched 2026-11-03 |
| L7 | **−0.26 $** per board at 10 (4-ch only; −3.07 $ per order) | RIS (R103/R203/R303/R403) 680 Ω 1206 C17975 (extended) → two **1 kΩ 1206 C4410** (basic) in parallel = 500 Ω (0.33 V/A instead of 0.45 V/A; 4.5 A BTT6050 → 1.5 V, 8 A BTT6010 → 2.7 V, still under the 3.3 V clamp) | 4 extra parts and 8 joints; sense resolution at small currents falls by a quarter, which is below what the alarms need; firmware scale constant changes; the 40 mA fault case dissipates 0.8 W in two 0.25 W parts instead of 1.09 W in one (both still over, covered by the firmware DEN rule) | "current measurement beyond what alarms need" is tradable; overcurrent protection is in the PROFET itself | small + firmware constant | no basic 1206 680 Ω (decision 52); `jlc_search` C4410 basic, 1.73 M in stock; 330 Ω and 2.2 kΩ 1206 are extended |
| L8 | **−0.27 $** (4-ch) / **−0.41 $** (HC2) per board at 5; break-even at 9 (4-ch) / 15 (HC2) boards; none at 10+ | Use the already needed C170101 2.2 µF/100 V (0.133 $) for the 1 µF/100 V places (4-ch: C30, C104–C404 = 5; HC2: C30, C102, C202 = 3) so that C13832 and its fee go | +0.068 $ per capacitor; only pays for runs of 5–8 boards | nothing cut | small | `jlc_search` prices |
| L9 | avoids **+1.6 to +1.9 $ per BTT6010 channel** and one 3.07 $ fee per order | Keep decision 36 (four BTT6050), put heavy loads on HC2 | none | heat budget unchanged | none | `jlc_get_part` BTT6010-1ERA C534858 3.1976 $ at 1+ |

Not proposed as levers (must stay or owner ruled): 1 oz copper, fewer TVS or fuses, the NTC (Q-0024), the ESP32 module or its
variants (all four S3-MINI-1 variants are extended, the N8 is the cheapest), the isolation, PESD2CAN (no basic CAN-rated part),
the 100 µF/63 V electrolytic (no basic ≥ 63 V part; decision 41).

**Five largest levers:** L1 (quantity), L2 (one panel), L3 (hand-soldered connectors), L4 (USB-C service pads), L6 (free-assembly coupon, unverified).

## Rule findings

**C1 – Extended parts where a basic or preferred part fits (MINOR).**
- C107198 (4.7 nF/1 kV) → C9196 (L5); C17975 (680 Ω 1206) → 2 × C4410 (L7). Both are two-way.
- Everything else extended was searched with `library_type=no_fee` and has no substitute: USB-C J3, PTC F1/F3/F4 (C19078719) and F2
  (C269104), PESD2CAN, buck U3, CA-IS3050G, ESP32, NTC (kept by ruling), L1, BTT6050, TPS48110A, BSC030N08NS5, shunt C2903470,
  100 V caps C13832/C170101, C487384, J4 C8410, J5 (no basic 2×5 header), J10, J11.
- Extended count: **19** on pdm-4ch, **20** on pdm-hc2 (was 17 and 19); after L5, L7 **17** and **19**.

**C2 – Non-standard values.** None. All values are E12/E24 (68 k, 220 k, 22 k, 39 k, 12 k, 1 mΩ shunt, 4.7 nF, 680 Ω). Pass.

**C3 – Low stock and single source.**
- Nothing below 500 today. Thin: TPS48110AQDGXRQ1 **989**, SWPA6045S8R2MT (L1) **1 231**, BTT6050-1ERA 1 748, C170101 79 836
  (fine). At 30 + 30 boards the HC2 uses 60 TPS48110A (6 %); L1 alternates (decision 49) are on file.
- Single source: BTT6050 and BSC030N08NS5 (Infineon); TPS48110A and LMR51610 (TI); CA-IS3050G (Chipanalog, stock 5 922; the ISO1044
  fallback has a different footprint and pinout); ESP32-S3-MINI-1-N8 (Espressif); the APV NTC.
- LMR51610**YF** (decision 30 reserve) had 458 in stock on 2026-10-30; not re-checked.

**C4 – Parts without an LCSC code.** Only J5, J10, J11 (`/system mechanical`). Their prices are placeholders; at most
±1 $ per board and ±9 $ per order with the fees.

**C5 – Standard PCBA only.** If Q-0026 shows Economic PCBA is not offered with 2 oz, each unique part costs 1.53 $: merging package
variants of 100 nF (0402, 0603, 0805) and 1 µF (0402, 0603) removes about 6 lines, ≈ 9 $ per order (decision 33). Zero under Economic.

## Questions for the owner

1. **Q-0026 is still open: 2 oz with Economic PCBA.** Does the JLCPCB quote page offer Economic PCBA with 2 oz? If only Standard,
   add 6.2 $ (4-ch) / 7.4 $ (HC2) per board at 10. Default: assume Economic.
2. **Live PCB quote.** Please paste the 2 oz price for the real board outline at 5, 10 and 30 once layout exists; it is 8–22 % of the price today and is an estimate.
3. **Do you want to try the free-assembly coupon (L6) and hand-solder the connectors (L3)?** Default: no, the first order is plain Economic PCBA.
4. **USB-C on later runs (L4).** Default: stays fitted (decision 31).

## Not checked

- PCB price (no live quote). The panel surcharge for two designs and whether Economic PCBA accepts a panel.
- Tier prices below the 1+ price for ~65 small parts; the BTT6010 tier table; stock of the YF buck and of the 3.81 mm header.
- J5, J10, J11 and the plug halves are estimates; enclosure, DIN clip, panel switches, LEDs and cable are not on the BOM.
- Shipping, customs, VAT, JLCPCB attrition. EMC DNP footprints that may be fitted after the pre-compliance scan (C70, FL1, snubber, TVS D103–D403 on 4-ch: ≈ 0.04 $ each).
- Datasheet for the L7 and L5 replacements (C4410 power rating and C9196 voltage derating are from the catalogue only); `part-facts` check before adoption.
- Validator topics (U1 footprint name S2-MINI vs S3, R3/R4/R7/R8 value vs decision 35).

<!-- findings:begin -->
```json
[
  {
    "id": "C1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "system",
    "location": "C18 (C107198) and R103/R203/R303/R403 (C17975): extended parts where basic parts fit",
    "summary": "Two avoidable extended-part types: 4.7 nF/1 kV USB-shield capacitor and the 680 ohm 1206 RIS, 3.07 USD per order and design each",
    "fix": "C18 -> 1 nF/2 kV C9196 (basic, already used); RIS -> two 1 kOhm 1206 C4410 in parallel (see L5, L7)",
    "door": "two-way",
    "reason": "agent decisions 46 and 52 (auto), component values, no must-stay function touched",
    "touches": ["shared-sheet"],
    "cost_delta_usd": -0.31
  },
  {
    "id": "C3",
    "kind": "finding",
    "severity": "INFO",
    "board": "system",
    "location": "U11/U12 TPS48110AQDGXRQ1 (pdm-hc2), L1 SWPA6045S8R2MT",
    "summary": "TPS48110A stock is 989 and L1 1231, both single-source or thin; nothing is below 500",
    "fix": "Re-check stock on the day of the order; L1 alternates are on file (decision 49)",
    "door": "two-way",
    "reason": "documentation, no design change",
    "touches": []
  },
  {
    "id": "L1",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "ordering",
    "summary": "30 instead of 10 boards per order saves 6.38 USD (4-ch) / 7.12 USD (HC2) per board; 10 instead of 5 saves 9.46 / 9.93 USD",
    "fix": "Owner sets the order quantity per board",
    "door": "one-way",
    "reason": "policy item 1: an order is money",
    "touches": ["money"],
    "cost_delta_usd": -6.38
  },
  {
    "id": "L2",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "PCB panel",
    "summary": "One panel for both designs saves 62.9 USD per order (3.15 USD per board at 10 + 10)",
    "fix": "Panelise pdm-4ch and pdm-hc2 at the PCB phase if the JLCPCB multi-design surcharge does not cancel the saving (decision 33)",
    "door": "one-way",
    "reason": "policy item 1: it shapes an order; already conditional in confirmed decision 33",
    "touches": ["money", "decision:33"],
    "cost_delta_usd": -3.15
  },
  {
    "id": "L3",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "J4, J5, J10, J11 assembly process",
    "summary": "Hand-soldering the four through-hole connectors removes 4 extended fees and the THT labour: 16.2 USD per order and design (1.62 USD per board at 10)",
    "fix": "Leave J4/J5/J10/J11 out of the PCBA order, buy and solder them by hand",
    "door": "one-way",
    "reason": "policy item 1 and 4: the owner buys parts and does the soldering of high-current terminals",
    "touches": ["money", "owner-fact", "connector"],
    "cost_delta_usd": -1.62
  },
  {
    "id": "L4",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "J3 USB-C and its protection",
    "summary": "USB-C as service pads on later runs saves 3 extended fees and parts: 1.20 USD per board at 10",
    "fix": "Make J3, F2, C18, R13, D4-D6, FB1 DNP or pads for a pogo jig on a later run",
    "door": "one-way",
    "reason": "policy item 2: contradicts confirmed decision 31 (USB-C stays fitted on the prototype run)",
    "touches": ["decision:31", "connector"],
    "cost_delta_usd": -1.2
  },
  {
    "id": "L5",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "C18 on both boards",
    "summary": "4.7 nF/1 kV C107198 (extended) to 1 nF/2 kV C9196 (basic): 0.31 USD per board at 10, RC corner 34 Hz to 160 Hz",
    "fix": "Change the value and LCSC code of C18 on both boards (shared sheet), then run the part-facts check on C9196",
    "door": "two-way",
    "reason": "component value on a shared sheet, decision 46 is auto",
    "touches": ["shared-sheet"],
    "cost_delta_usd": -0.31
  },
  {
    "id": "L6",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "ordering, JLCPCB account",
    "summary": "A monthly JLCPCB assembly coupon may waive the 8.18 USD setup per order (conditions for 2 oz and Economic PCBA unverified)",
    "fix": "Owner checks the coupon centre and the cart at order time",
    "door": "one-way",
    "reason": "policy items 1 and 4: money, facts only the owner has",
    "touches": ["money", "owner-fact"],
    "cost_delta_usd": -0.82
  },
  {
    "id": "L7",
    "kind": "lever",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "R103/R203/R303/R403 RIS",
    "summary": "RIS 680 ohm 1206 C17975 (extended) replaced by two 1 kohm 1206 C4410 (basic) in parallel: 0.26 USD per board at 10, sense scale 0.33 V/A",
    "fix": "Replace each RIS by two C4410 in parallel; firmware scale constant becomes 500 ohm; check C4410 power rating with part-facts",
    "door": "two-way",
    "reason": "component change, current measurement accuracy beyond alarm needs is tradable; decision 52 is auto",
    "touches": ["firmware"],
    "cost_delta_usd": -0.26
  },
  {
    "id": "L8",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "C30, C104-C404 (4-ch), C30, C102, C202 (HC2)",
    "summary": "Using C170101 for the 1 uF/100 V places removes the C13832 fee; pays only for runs of fewer than 9 (4-ch) or 15 (HC2) boards",
    "fix": "Only if the first run stays at 5 boards: swap the five or three capacitors to 2.2 uF/100 V C170101",
    "door": "two-way",
    "reason": "component value, no must-stay function touched",
    "touches": ["shared-sheet", "new-extended-part"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "Q1",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "summary": "Does the JLCPCB quote page offer Economic PCBA with 2 oz copper (Q-0026 is still open)?",
    "default": "Assume Economic PCBA; if only Standard, per board at 10 add 6.2 USD (4-ch) / 7.4 USD (HC2)",
    "door": "two-way",
    "reason": "a sensible default exists; only the cost figure changes",
    "touches": []
  },
  {
    "id": "Q2",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "summary": "What does JLCPCB quote for the real board outline in 2 oz at 5, 10 and 30 pieces once layout exists?",
    "default": "Keep the estimate of 15 / 20 / 38 USD per order",
    "door": "two-way",
    "reason": "default keeps the estimate; refined at the PCB phase",
    "touches": []
  },
  {
    "id": "Q3",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "summary": "Should the first order use the free-assembly coupon (L6) or hand-soldered connectors (L3)?",
    "default": "No: plain Economic PCBA with all parts assembled by JLCPCB",
    "door": "two-way",
    "reason": "a sensible default exists; both stay possible at order time",
    "touches": []
  }
]
```
<!-- findings:end -->
