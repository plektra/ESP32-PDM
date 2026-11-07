# Cost review, scope system (pdm-4ch and pdm-hc2), 2026-11-07 (second report of the day)

This is a full re-pricing after decisions 103–121:
- pdm-4ch is 16 A only.
- Q30 is the AGM601LL.
- pdm-4ch J10 is the fixed screw terminal KF135T-10.16-2P.
- BOM merges, the two LEDs and the buck input filter footprints are in.

The last full report was `2026-11-05-cost-system.md`. `2026-11-07-cost-system.md` priced only the T-0158…T-0161 changes. No board is ordered.

Method:
- **BOM:** `kicad-cli sch export bom --exclude-dnp`, grouped by the LCSC field, run on copies of both root sheets in a temporary folder (design files untouched).
  - pdm-4ch: 59 codes (55 SMT and 4 hand-soldered connectors).
  - pdm-hc2: 64 codes (60 SMT and 4 connectors).
  - SMT joints from the netlist (connected pins of fitted SMT parts): about 559 (4-ch) and 580 (HC2).
- **Prices:** every code and the five plugs looked up with `jlc_get_part` / `jlc_stock_check` on 2026-11-07. Stock is live. Price is the LCSC list price at the tier for (parts per board × assembled boards). No attrition or minimum-order extras are included.
- **Assembly basis:** Standard PCBA. Decisions 99 and 100 rule out Economic with 2 oz copper, and U1 C2913206 is still `standard_only` today.

## Figures

### Fee and PCB sources

| Item | Figure | Source, date |
|---|---|---|
| Standard setup / stencil, single side | 25.56 / 8.21 $ per design per order | [JLCPCB PCBA price](https://jlcpcb.com/help/article/pcb-assembly-price), "last updated Oct 22, 2026", fetched 2026-11-07; unchanged |
| Standard, double side | 51.12 / 16.42 $ | same |
| Feeder loading, Standard | 1.53 $ per unique part, **basic and extended alike** | same |
| Confirm placement / SMT joint | 0.45 $ / 0.0016 $ | same |
| Economic extended loading | 3.07 $ (not used: Standard basis) | same |
| Fixture | 8.21 $ each; 1–29 pcs needs 2, so **16.42 $**. Whether it applies is unknown; **not in totals** | same |
| Hand soldering by JLCPCB | 0.0164 $ per joint + 3.58 $ per order (not used: the owner solders, decision 85) | same |
| Other Standard items seen today (not in totals) | Handling fee: only when the Economic/Standard price gap is under 14.93 $. Bulk orders: 0.48 $ per board minimum surcharge. Stencil and fixture storage: 4.93 $ each, conditions not stated | same |
| PCB 2 oz, 2 layers, 5 pcs | **40.67 $** per design (€36.43 at 1.1165) | owner's JLCPCB quote 2026-11-06 (100×65 and 100×75 mm test Gerbers) |
| PCB 2 oz, 10 / 30 pcs | **ESTIMATE, ±50 %:** 4-ch 54 / 103 $, HC2 62 / 118 $. Method: the 11-05 area-scaled estimates × 1.94, which is the ratio of the real 5-pc quote to its estimate | no JLCPCB 2 oz price found by web search 2026-11-07 |

Not in any total: shipping, VAT/duty, attrition, the fixture fee, panel switches, wiring, DIN carrier, enclosure.

### Per board

SMT is assembled by JLCPCB on Standard. Connector sets are bought by the owner and shown separately.

| Board | PCBs / assembled | Parts | Fixed per order | PCB | **Per assembled board** | Order (JLCPCB) | Connector sets per board | + fixture per board, if it applies |
|---|---|---|---|---|---|---|---|---|
| pdm-4ch | **5 / 2 (first order, decision 101)** | 19.10 | 118.37 | 40.67 | **99.51** | **199.02** | 2.50 | +8.21 |
| pdm-4ch | 5 / 5 | 18.65 | 118.37 | 40.67 | **51.36** | 256.78 | 2.50 | +3.28 |
| pdm-4ch | 10 / 10 | 16.83 | 118.37 | 54 (est.) | **34.96** | 349.64 | 2.23 | +1.64 |
| pdm-4ch | 30 / 30 | 15.61 | 118.37 | 103 (est.) | **23.88** | 716.36 | 2.10 | +0.55 |
| pdm-hc2 | 5 / 2 | 22.75 | 126.02 | 40.67 | **107.03** | 214.05 | 7.27 | +8.21 |
| pdm-hc2 | 5 / 5 | 21.24 | 126.02 | 40.67 | **55.50** | 277.51 | 7.27 | +3.28 |
| pdm-hc2 | 10 / 10 | 19.75 | 126.02 | 62 (est.) | **39.48** | 394.76 | 6.14 | +1.64 |
| pdm-hc2 | 30 / 30 | 18.03 | 126.02 | 118 (est.) | **27.09** | 812.79 | 5.57 | +0.55 |

- **Fixed per order** = 25.56 + 8.21 + 0.45 + 1.53 × unique SMT lines (55 on 4-ch, 60 on HC2). Joints (0.89 / 0.93 $ per board) are included in "Order".
- **First order (pdm-4ch, 5 PCBs, 2 assembled):** 199.02 $ + 2 connector sets (5.00 $) = **about 204 $**, or **about 220 $** if the fixture fee applies. STATUS and CONTINUE-FROM-HERE still say "about 218 $", the 11-06 figure from before T-0158, T-0159 and decision 121.
- **Connector sets per board, 4-ch (1+ tier):**
  - J10 C475108: 0.56 $ (no plug).
  - J11 C441238 + C440882: 0.49 $.
  - J5 C26895 + C26865: 1.04 $.
  - J4 C7245 + C7244: 0.41 $.
- **Connector sets per board, HC2 (1+ tier):**
  - J10 C6394053 + C6394029: 3.99 $.
  - J11 C577772 + C577752: 1.83 $.
  - J5 and J4: as on 4-ch.
- **Unique extended SMT parts:** 14 per board. This only matters for Economic; under Standard every line costs the same 1.53 $.

### Top cost drivers

**pdm-4ch first order (199.02 $):**
- Feeder loading: 84.15 $ (42 %).
- PCB, 2 oz: 40.67 $ (20 %).
- Parts: 38.20 $ (19 %).
- Setup, stencil and confirm: 34.22 $ (17 %).
- Joints: 1.79 $.

**pdm-4ch at 10 boards (34.96 $ per board):**
- Fixed fees: 11.84 $ (34 %).
- PCB: 5.40 $, estimate (15 %).
- 4 × BTT6050: 4.38 $ (13 %).
- ESP32-S3-MINI-1-N8: 4.17 $ (12 %).
- Then LM74500-Q1 1.54 $, LMR51610 1.08 $, CA-IS3050G 0.91 $, AGM601LL 0.77 $, 6 × C170101 0.57 $.
- Rest: about 3.4 $.

**pdm-hc2 at 10 boards (39.48 $ per board):**
- Fixed fees: 12.60 $ (32 %).
- 2 × TPS48110A: 6.55 $ (17 %).
- PCB: 6.20 $, estimate (16 %).
- Module: 4.17 $ (11 %).
- 4 × BSC030N08NS5: 2.62 $ (7 %).
- Then LMR51610 1.08 $, CA-IS3050G 0.91 $, 3 × C487384 0.66 $.
- Rest: about 4.7 $.

### Change since the last reports

| | 4-ch @5 | 4-ch @10 | HC2 @5 | HC2 @10 |
|---|---|---|---|---|
| 11-05 report, with the PCB at today's figure (40.67 $ at 5; 54 / 62 $ at 10) | 54.52 | 37.42 | 56.33 | 39.84 |
| Today | **51.36** | **34.96** | **55.50** | **39.48** |
| Change | −3.16 | −2.46 | −0.83 | −0.36 |

Where the 4-ch change comes from:
- Q30 IPT007N06N → AGM601LL: −2.7 $ at 5, −2.3 $ at 10.
- T-0159 merges (−3 lines) and the T-0160 LEDs (+1 line): −3.06 $ per order, which is −0.61 $ per board at 5 and −0.31 $ at 10.
- 4-ch connector sets: 5.93 → 2.50 $ per board (J10 KF135T without a plug, decision 121).

HC2: −3 lines from T-0159, +1 line for the LEDs.

The 11-07 change report estimated −4.8 $ per board at 5, counting the old J10 socket and plug. That is consistent: J10 is now cheaper still.

Price and stock moves since 11-05:
- Module: 4.17 → 4.73 $ at the 1+ tier; still 4.17 $ at 10+.
- BTT6050 stock: 1698 → 1638.
- TPS48110A stock: 949 → 934.

## Levers

Largest saving first. Savings are given per order and per board. None cuts a must-stay function unless marked.

| # | Saving | What changes | Trade-off | Must-stay check | Effort | Evidence |
|---|---|---|---|---|---|---|
| L1 | **11.1 $/board (4-ch), 12.4 $ (HC2)** for 30 instead of 10 per order; 16.4 / 16.0 $ for 10 instead of 5. First order: assembling all 5 PCBs costs **+57.76 $, i.e. 19.25 $ per extra board**. Compare about 100 $ per board for 2 assembled in a later order | Boards per order; for the first order, how many of the 5 PCBs are assembled | Cash up front, for boards of a revision that will change (decisions 101 and 102 chose a prototype-only run) | Nothing cut | None | Per-board table |
| L2 | **About 106 $ per combined order** (10.6 $/board at 5+5, 5.3 $ at 10+10) | One panel and one PCBA design for both boards at a later order: one setup/stencil/confirm (34.22 $) and 47 shared SMT lines (71.91 $) | Fixed 1:1 ratio of the boards. JLCPCB multi-design surcharge and 2 oz panel price are unverified. Not for the first order (decision 102) | Nothing cut | Layout phase | 47 of the 55 / 60 SMT codes are shared (BOM export) |
| L3 | **Avoids +33.77 $ per order** (double-sided Standard: 51.12 + 16.42 $, against 25.56 + 8.21 $) | Layout rule: all SMT parts on one side. The through-hole connectors are hand-soldered anyway | Board area. No such rule is in STATUS yet | Nothing cut | Rule text only | Fee page 2026-11-07 |
| L4 | **About 7.7 $ per order** (3.8 $/board at 2 assembled) | The owner hand-solders about five single-use, large-pad parts that are not in the surge path (for example C3, C8, C13 in 0805, R13 in 1206, SW_BOOT/SW_RESET) instead of JLCPCB placing them | Owner time and workmanship. Changes the hand-solder list of decision 85. Excludes the parts on VS copper (D30, D31, C31 on 2 oz pours) and all 0402 | Nothing cut if they are soldered | BOM edit at order time | 1.53 $ per line |
| L5 | **1.53 $ per order per board design** (net −0.07 $/board at 10, −0.69 $ at 2) | C3 (2.2 µF/50 V X5R 0805 C377773, +3V3 to GND, used once on each board) → C170101 2.2 µF/100 V X7R 1206, which is already on the BOM | 1206 footprint instead of 0805; +0.08 $ per part. Same value, and X7R loses less capacitance under DC bias | Nothing cut | One shared-sheet edit | BOM export; prices above |
| L6 | **1.53 $ per order (HC2)** | R105/R205 (1 MΩ 0402 C26083, VS to EN, top of the UV/OV divider) → C17927 1 MΩ 1206, already on the BOM as R13. C26083 then leaves the HC2 BOM | 1206 footprint. The resistor sits directly on VS and gets a 200 V rating instead of 50 V (the 0402 is already below the 48.4 V clamp, so this is not a finding) | Nothing cut; value and 1 % tolerance unchanged | One hc_channel edit | BOM export; R105 nets VS–EN |

Five largest: L1, L2, L3, L4, L5.

Scenarios checked and not proposed:
- **1 oz copper** (about 35 $ less per design at 5 pcs): fails must-stay.
  - 4-ch BTT6050 at 40 °C drops to 3.5 A; at 4 A it reaches 120 °C (design-notes §4 table).
  - HC2 on 1 oz was examined on 2026-11-06 and not chosen.
  - Copper stays 2 oz (decision 101).
- **HC2 J10 as the cheap fixed KF135T** (C475108, 0.56 $, stock 2071, instead of the 3.99 $ Kefa set): fails must-stay. HC2 has no reverse-battery element; the keyed J10 is its only protection (decision 40).
- **BTT6010 population:** C534858 costs 3.09 $ at 1+ against 1.28 $, so +1.82 $ per channel plus one more part line (1.53 $). Decision 103 has no BTT6010 build in this version.
- **Economic PCBA, a hand-reflowed U1, or a DOIT module:** closed by decisions 99 and 100.
- **JLCPCB hand-soldering the connectors:** 22 joints on 4-ch, 0.36 $ per board + 3.58 $ per order, plus loading fees if charged. This is a convenience cost, not a saving; decision 85 keeps the connectors with the owner.
- **Value merges that change function:** BTT6050 C101 100 pF, C102 10 nF and R105 22 Ω; the VBAT divider 220 k/22 k → 22 k/2.2 k; the buck feedback 68 k. Each needs a datasheet check or a change to a confirmed decision, for 1.53 $ per order.
- **Removing SW_BOOT/SW_RESET or the LEDs on the prototype:** one line each. Both are useful for bring-up, and decision 106 confirmed the LEDs.

## Rule findings

- **R1 (MINOR, pdm-hc2): connector stock for the later HC2 order.**
  - Live stock today (`jlc_get_part` / `jlc_stock_check`, 2026-11-07): J11 socket C577772 **0** (minimum order 18), plug C577752 63; J10 socket C6394053 **39**, plug C6394029 50.
  - Decision 121 recorded C6394053 as 4 on the same day. The live figure is now 39: either it was restocked or the earlier read was a snapshot.
  - Effect: a 5-board HC2 order needs 5 J10 sets and 5 J11 sets. J10 fits; J11 does not (decision 120: buy from any seller).
  - Cheapest fix: if HC2 is expected within months, buy the HC2 J10 sets together with the 4-ch connector samples, and re-check stock at order time. No design change.
- **R2 (INFO, docs):** the first-order figure "about 218 $" in `docs/CONTINUE-FROM-HERE.md` and `hardware/pdm-4ch/STATUS.md` is stale. It is now about 204 $, or about 220 $ with the fixture fee. Fix: update both lines in the next sync.
- **Extended where a basic/preferred part fits:** none. `jlc_search library_type="no_fee"` returned nothing on 2026-11-07 for:
  - USB-C 16P;
  - a 10 k 0603 NTC;
  - an 1812 PTC rated at least 60 V and 0.5 A;
  - 2.2 µF, at least 100 V, X7R 1206.
  Under Standard PCBA the library class makes no fee difference anyway.
- **Non-standard values:** none. All are E12/E24, plus 0 Ω and the 1 mΩ and 200 mΩ shunts.
- **Low stock (< 500):** only the four Kefa codes above. Every other code has at least 934:
  - TPS48110A 934, BTT6050 1638, C96963 1221, AGM601LL 2016;
  - KF135T C475108 2071, LM74500 2846, LMR51610 2995.
- **Single source:** Espressif module, BTT6050, TPS48110A, LM74500-Q1, LMR51610, CA-IS3050G, AGM601LL, BSC030N08NS5, APV NTC, and the Kefa/Kangnex connectors. Known. Approved alternates exist only for the L1 inductor (decision 49).

## Questions for the owner

- **Q1.** Does the 16.42 $ Standard fixture fee appear on the quote for 5 PCBs with 2 assembled? Default: assume yes and budget about 220 $.
- **Q2.** Assemble more than 2 of the 5 pdm-4ch PCBs? Each extra assembled board costs 19.25 $ in this order. Default: keep 2 (decision 101).
- **Q3.** Hand-solder a handful of large single-use SMD parts yourself to save about 7.7 $ on the first order (L4)? Default: no, JLCPCB places all SMT parts.

## Not checked

- PCB price at 10 and 30 pcs (estimates only); the JLCPCB panel / multi-design surcharge; whether the fixture and storage fees apply.
- JLCPCB attrition and minimum-purchase extras for passives at 2 boards; shipping, VAT, the monthly coupon (decision 85).
- Enclosure, DIN carrier and panel-switch costs (no design yet).
- Datasheet and placement checks for L5/L6 (the validator's job). The heat budget was not re-run, since no output change is proposed.

<!-- findings:begin -->
```json
[
  {"id":"R1","kind":"finding","severity":"MINOR","board":"pdm-hc2","location":"J10 C6394053/C6394029, J11 C577772/C577752","summary":"Live stock 2026-11-07: J11 socket C577772 0, plug 63; J10 socket C6394053 39 (decision 121 recorded 4), plug 50; a 5-board HC2 order fits J10 but not J11 from LCSC","fix":"buy HC2 connector sets early from any seller (decision 120) and re-check at order time; no design change","door":"two-way","reason":"purchase timing only; the purchase itself is the owner's at order time","touches":[],"cost_delta_usd":0.0},
  {"id":"R2","kind":"finding","severity":"INFO","board":"pdm-4ch","location":"docs/CONTINUE-FROM-HERE.md, hardware/pdm-4ch/STATUS.md first-order line","summary":"First-order figure 'about 218 $' is stale; now about 204 $ (199.02 JLCPCB + 5.00 connector sets), about 220 $ with the fixture fee","fix":"update the figure in the next sync package","door":"two-way","reason":"documentation only","touches":[],"cost_delta_usd":0.0},
  {"id":"L1","kind":"lever","severity":"INFO","board":"system","location":"ordering: boards per order / assembled count","summary":"30 instead of 10 per order saves 11.1 USD/board (4-ch) and 12.4 (HC2); in the first order each extra assembled 4-ch board costs 19.25 USD against about 100 USD per board for 2 in a later order","fix":"decide at order time","door":"one-way","reason":"money (policy item 1) and decision 101 (assembled count)","touches":["money","decision:101"],"cost_delta_usd":-11.1},
  {"id":"L2","kind":"lever","severity":"INFO","board":"system","location":"PCB phase: combined panel of both designs","summary":"One PCBA design for both boards at a later order saves about 106 USD per order (34.22 setup/stencil/confirm + 47 shared lines x 1.53); 5.3 USD/board at 10+10","fix":"quote the combined panel at the HC2 PCB phase (decision 33 condition; not for the first order, decision 102)","door":"two-way","reason":"a layout choice within decision 33 before any order; no money spent","touches":[],"cost_delta_usd":-5.3},
  {"id":"L3","kind":"lever","severity":"INFO","board":"system","location":"layout rule, both boards","summary":"Keep all SMT on one side: a double-sided Standard job adds 33.77 USD per order (setup 51.12 vs 25.56, stencil 16.42 vs 8.21)","fix":"add 'all SMT parts on one side' to both STATUS layout rules","door":"two-way","reason":"layout rule before layout starts, revertible by a commit","touches":[],"cost_delta_usd":0.0},
  {"id":"L4","kind":"lever","severity":"INFO","board":"pdm-4ch","location":"order BOM: C3, C8, C13, R13, SW_BOOT1/SW_RESET1","summary":"Owner hand-solders about five single-use large-pad SMD lines: saves about 7.7 USD per order (3.8 USD/board at 2 assembled); not VS-copper surge parts or 0402","fix":"leave those lines off the JLCPCB BOM at order time","door":"one-way","reason":"changes the hand-solder split of decision 85 and the order (policy items 1 and 2)","touches":["money","decision:85"],"cost_delta_usd":-0.77},
  {"id":"L5","kind":"lever","severity":"INFO","board":"system","location":"power-usb: C3 2.2uF/50V 0805 C377773 (+3V3)","summary":"C3 to C170101 2.2uF/100V X7R 1206 (already on both BOMs) removes one line per board: 1.53 USD per order, +0.08 USD per part","fix":"swap C3 LCSC/footprint to C170101 / C_1206_3216Metric on the shared sheet, both boards","door":"two-way","reason":"same-value part swap to a part on the BOM before any order","touches":["shared-sheet"],"cost_delta_usd":-0.07},
  {"id":"L6","kind":"lever","severity":"INFO","board":"pdm-hc2","location":"hc_channel: R105/R205 1M 0402 C26083 (VS to EN)","summary":"R105/R205 to C17927 1M 1206 (already R13) removes C26083 from the HC2 BOM: 1.53 USD per order, higher voltage rating on VS","fix":"swap R105/R205 LCSC/footprint to C17927 / R_1206_3216Metric","door":"two-way","reason":"same-value part swap to a part on the BOM before any order","touches":[],"cost_delta_usd":-0.15},
  {"id":"Q1","kind":"question","severity":"INFO","board":"pdm-4ch","summary":"Does the 16.42 USD Standard fixture fee appear on the quote for 5 PCBs / 2 assembled?","default":"assume yes; budget about 220 USD for the first order","door":"two-way","reason":"a sensible default exists; only the budget figure depends on it","touches":[]},
  {"id":"Q2","kind":"question","severity":"INFO","board":"pdm-4ch","summary":"Assemble more than 2 of the 5 pdm-4ch PCBs in the first order (19.25 USD per extra assembled board)?","default":"keep 2 (decision 101)","door":"one-way","reason":"money and decision 101 (policy items 1 and 2)","touches":["money","decision:101"]},
  {"id":"Q3","kind":"question","severity":"INFO","board":"pdm-4ch","summary":"Hand-solder about five large single-use SMD parts yourself to save about 7.7 USD on the first order (L4)?","default":"no; JLCPCB places all SMT parts","door":"one-way","reason":"decision 85 (assembly split) and owner's time (policy items 2 and 4)","touches":["decision:85"]}
]
```
<!-- findings:end -->

Sources: [JLCPCB PCB assembly price](https://jlcpcb.com/help/article/pcb-assembly-price), [JLCPCB copper weight](https://api.jlcpcb.com/help/article/jlcpcb-copper-weight). LCSC/JLCPCB part data came from the pcbparts tools on 2026-11-07.
