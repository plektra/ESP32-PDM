# Cost review, scope system (pdm-4ch and pdm-hc2), 2026-11-05

This is a full re-pricing after decisions 85 and 92-98. No board is ordered. The last full report was `2026-11-03-cost-system.md`; the 11-03 and 11-04 re-checks priced only diffs.

Method:
- BOM from `kicad-cli sch export bom --exclude-dnp` on both root sheets, which gives 76 distinct LCSC codes.
- All 76 codes plus the five connector plugs were looked up with `jlc_stock_check` on 2026-11-05. Prices are list prices at the tier for parts per board times boards per order.
- SMT joints are about 520 (4-ch) and 560 (HC2) at 0.0016 $, which is 0.83 $ per board.

## Headline finding (new)

**The ESP32-S3-MINI-1-N8 (C2913206) is flagged `pcba_type: standard_only` in the JLCPCB catalog.** This comes from `jlc_get_part`, snapshot 2026-11-05T20:23Z.
- All 25 Espressif S3 module listings are standard-only.
- The only Economic-capable S3 options are the bare ESP32-S3FH4R2 chip, DOIT ESPS3-32/32E modules (stock 336-627) and two boxed boards.
- All 75 other BOM codes are "economic".
- One standard-only part moves the whole order to Standard PCBA.
- Every earlier cost report and decisions 33 and 85 assume Economic.
- Q-0016's condition ("merge package variants only if Standard PCBA is forced") would then be met.
- I could not check the quote page myself, so this is unverified. See Q1.

## Figures

### Fee sources (fetched 2026-11-05)

| Item | Figure | Source |
|---|---|---|
| Economic setup / stencil | 8.18 / 1.53 $ per design per order | [JLCPCB PCBA price](https://jlcpcb.com/help/article/pcb-assembly-price), last updated Oct 22 2026; unchanged since 11-03 |
| Economic extended loading | 3.07 $ per unique extended part | same |
| Standard setup / stencil (single side) | 25.56 / 8.21 $ | same |
| Standard feeder loading | 1.53 $ per unique part, basic included | same |
| Standard fixtures | 8.21 $ each, "1-29 pcs requires 2" = 16.42 $; applicability unknown, **not in totals** | same |
| Confirm placement / SMT joint | 0.45 $ / 0.0016 $ | same |
| THT labour | Not used: the owner solders all four connector sockets (decision 85) | |
| **PCB 2 oz, 2 layers** | **ESTIMATE.** The 11-03 figures of 15 / 20 / 38 $ (5 / 10 / 30 pcs, 85x55 mm) scaled by outline area: x1.4 for 4-ch (about 100x65 mm), x1.6 for HC2 (100x75 mm). ±50 %. | The JLCPCB copper page lists 2 oz without a price; a web search on 2026-11-05 found no JLCPCB 2 oz figure |

Not in any total: shipping, VAT, attrition, panel switches, wiring, enclosure or DIN carrier.

### Per board, SMT assembled by JLCPCB

Standard is the expected basis. Economic is hypothetical; it is only reachable via L1 or L2. Connector sets are bought by the owner and shown separately.

| Board | Qty | Basis | Parts | Fixed per order | PCB (est.) | **Per board** | Order | Connector sets per board |
|---|---|---|---|---|---|---|---|---|
| pdm-4ch | 5 | Standard | 21.27 | 121.43 | 21.0 | **50.59** | 252.94 | 5.93 |
| pdm-4ch | 10 | Standard | 19.04 | 121.43 | 28.0 | **34.82** | 348.18 | 5.13 |
| pdm-4ch | 30 | Standard | 17.55 | 121.43 | 53.2 | **24.20** | 726.10 | 4.67 |
| pdm-4ch | 5/10/30 | Economic | same | 53.14 | same | 36.93 / 27.99 / 21.93 | 184.65 / 279.89 / 657.81 | |
| pdm-hc2 | 5 | Standard | 21.17 | 130.61 | 24.0 | **52.99** | 264.96 | 7.27 |
| pdm-hc2 | 10 | Standard | 19.68 | 130.61 | 32.0 | **36.84** | 368.41 | 6.14 |
| pdm-hc2 | 30 | Standard | 17.97 | 130.61 | 60.8 | **25.25** | 757.37 | 5.57 |
| pdm-hc2 | 5/10/30 | Economic | same | 53.14 | same | 37.50 / 29.09 / 22.66 | 187.49 / 290.94 / 679.90 | |

- **Standard fixed fees:** 25.56 + 8.21 + 0.45 + 1.53 × unique SMT parts. That is 57 parts on 4-ch and 63 on HC2, excluding DNP parts and the four sockets.
- **Economic fixed fees:** 8.18 + 1.53 + 0.45 + 3.07 × 14 unique extended parts, the same on both boards.
- **Fixture fee:** if it applies, add 16.42 $ per design and order (1.64 $ per board at 10).
- **All-in per board with connectors, Standard, at 5 / 10 / 30:** 4-ch 56.52 / 39.95 / 28.87; HC2 60.26 / 42.98 / 30.82.
- **Both boards in one run, all-in (5+5 / 10+10 / 30+30):** about 584 / 829 / 1 790 $.

### Connector sets (decision 98, first pricing)

| Set | Socket | Plug | Per board at 1 / 10 / 30 | Stock socket / plug |
|---|---|---|---|---|
| J10, both boards, Kefa 10.16 mm | C6394053 1.5389 (10+: 1.2723) | C6394029 2.4531 (10+: 2.0753) | 3.99 / 3.35 / 2.97 | **39 / 50** |
| J11 4-ch, 5.08 mm | C441238 0.1304 | C440882 0.3572 | 0.49 / 0.40 / 0.35 | 8193 / 8455 |
| J11 HC2, 7.62 mm | C577772 0.646 | C577752 1.184 | 1.83 / 1.50 / 1.31 | **40 / 63** |
| J5, 3.81 mm 10-pole | C26895 0.17 | C26865 0.8717 | 1.04 / 0.88 / 0.81 | 4082 / 8792 |
| J4, 3.81 mm 4-pole | C7245 0.0772 | C7244 0.3307 | 0.41 | 96304 / 55626 |

The J10 set is the most expensive passive item on either board: 3.35 $ at 10 boards, about 12 % of the 4-ch price. The earlier placeholders were 0.57 $ for the socket and 1.20 $ for all plug halves.

### Top cost drivers at 10 boards, Standard

**pdm-4ch, 34.82 $:**
- Standard fixed fees: 12.14 $ (35 %).
- 4 × BTT6050: 4.38 $ (13 %).
- ESP32-S3 module: 4.17 $ (12 %).
- Q30 IPT007N06N: 3.05 $ (9 %).
- PCB estimate: 2.80 $ (8 %).
- U30 LM74500: 1.54 $ (4 %).
- LMR51610Y plus CA-IS3050G: 1.99 $ (6 %).
- 6 × C170101 plus 4 PTC: 0.92 $ (3 %).
- Rest, about 40 lines: 3.8 $ (11 %).

**pdm-hc2, 36.84 $:**
- Standard fixed fees: 13.06 $ (35 %).
- 2 × TPS48110A: 6.55 $ (18 %).
- ESP32-S3 module: 4.17 $ (11 %).
- PCB estimate: 3.20 $ (9 %).
- 4 × BSC030N08NS5: 2.62 $ (7 %).
- LMR51610Y plus CA-IS3050G: 1.99 $ (5 %).
- Bulk caps and PTCs: 1.5 $ (4 %).

### Change since the last full report (2026-11-03)

| Basis | 4-ch @10 | HC2 @10 |
|---|---|---|
| 11-03 report (Economic, connectors and THT labour inside) | 25.42 | 31.19 |
| Today, same basis (Economic, connectors outside) | 27.99 | 29.09 |
| Today, Standard (expected) | **34.82** | **36.84** |

Bridge for 4-ch Economic (rounded, not exact):
- Q30 +3.05, U30 +1.54, D31 +0.22.
- PCB estimate for the larger outline +0.8.
- Extended fees −1.5 (unique extended parts went from 19 to 14).
- Sockets now bought separately −1.1.
- THT labour and joints −0.4.

The Economic-to-Standard step (+6.83 on 4-ch, +7.75 on HC2) is not a design change; it comes from the U1 flag.

Stock of thin parts on 2026-11-05:
- TPS48110A 949 (989 on 11-03).
- BTT6050 1698.
- SWPA6045 inductor 1221.
- LM74500 2846.
- IPT007N06N 4677.
- LMR51610Y 3046.

## Levers

Largest saving first. Savings are per board at 10 per order, Standard basis, unless stated.

| # | Saving | What changes | Trade-off | Must-stay check | Effort | Evidence |
|---|---|---|---|---|---|---|
| L1 | **7.14 $ (4-ch), 8.05 $ (HC2)** at 10; 14.3 / 16.1 at 5; 2.4 / 2.7 at 30. About 71 $ per design and order | Leave U1 off the JLCPCB order and hand-reflow the module yourself (bought separately), so Economic PCBA is possible | You solder an LGA-type module with a ground pad on 5-10 boards; yield and rework risk. Decision 85 already hand-solders the connectors | Nothing cut | Owner's time, no design change | `jlc_get_part` C2913206 `standard_only`; fee table |
| L2 | **about 8.5 $** at 10 on both boards (6.83 platform + 1.68 module price) | Replace the module with DOIT ESPS3-32E-N4 (C49164659, Economic-capable, 2.49 $, N4, stock **503**) | Different outline and pinout, no datasheet or certification checked, stock under 500, half the flash of the N8 | Not in the switch-to-output path; pin-map invariants must be rechecked | Medium: new footprint, symbol and pin map on both boards | `jlc_search` pcba_type economic, 8 results. Not recommended before L1 is judged |
| L3 | **about 5.5 $ per board at 10+10**, 10.9 at 5+5, 1.8 at 30+30 (109 $ per order) | One combined panel and one PCBA design for both boards (decision 33, conditional): one setup/stencil/confirm (34.22 $) plus 49 shared feeder lines | Fixed 1:1 ratio; JLCPCB panel surcharge and whether it counts as one design are unverified | Nothing cut | Layout phase | 49 of 57 / 63 unique SMT codes are shared |
| L4 | **0.61 $ (4-ch), 0.77 $ (HC2)**; 6.1 / 7.65 $ per order. **Zero under Economic** | Merge near-duplicate lines, since Q-0016 is triggered: C2 0.1 µF 0603 C14663 → C307331 (0402); C12 C52923 → C15849; C13 C28323 → C15849; R10 C31850 → C25768; HC2 R9 C23231 → C36871 | Footprint changes at layout. C13 is the L78M05 input cap (X7R, 50 V); X5R 1 µF loses capacity under bias at 29 V, so check the datasheet curve first, otherwise keep C28323 | Nothing cut | Small scripted edits | Prices and library types from 2026-11-05 |
| L5 | **10.6 $ (4-ch), 11.6 $ (HC2)** for 30 instead of 10 boards per order; 15.8 / 16.2 for 10 instead of 5 | Order quantity | Cash up front; stock on the shelf if the design changes; the first run is 5+5 (Q-0027) | Nothing cut | None | Figures table |
| L6 | **1.85 $ (4-ch only)** at 10; 2.2 at 5; 1.6 at 30 | pdm-4ch J10: use the 7.62 mm 32 A set already on HC2 J11 (1.50 $ instead of 3.35 $). Keying holds because J11 is 5.08 mm | Decision 95 sets a 32 A input limit with four BTT6010, so a 32 A connector has no margin. Only sensible if the 4-ch limit drops to the standard-build 16 A and the BTT6010 option goes | **Fails at 32 A**, passes at 16 A | Owner decision, then a footprint swap | `jlc_stock_check` C577772/C577752/C6394053/C6394029 |

Not proposed (must-stay, or already ruled):
- Fewer TVS or fuses, the NTC, the isolation, and USB-C pads (decision 83).
- The AGM601LL for Q30 (decision 91).
- SMAJ33CA → SMAJ30CA on HC2 outputs. It would save one line (1.53 $ per order under Standard) but costs the 28.8 V float-case stand-off margin (decisions 27 and 43).
- BTT6010 population. It costs +1.47 $ per channel at 10 (2.63 against 1.16 $) plus 1.53 $ per order for an extra unique line.

No basic or preferred substitute exists for the 14 extended parts. A `no_fee` search for pluggable terminals returned 0 of 2059.

**Five largest levers:** L1 (U1 off the order), L2 (Economic-capable module), L5 (order 30 instead of 10), L3 (one panel), L6 (4-ch J10 smaller, needs an input-limit ruling).

## Rule findings

- **C1, MAJOR: a standard-only part forces Standard PCBA.**
  - Mechanism: `C2913206` is flagged `standard_only`, and Economic is assumed in all figures so far.
  - Effect: +6.83 $ (4-ch) and +7.75 $ (HC2) per board at 10, +13.7 / +15.5 at 5. Every unique part, basic included, costs 1.53 $.
  - Cheapest fix: L1, which needs no design change.
- **C2: extended parts where basic or preferred fits.** No new case. There are now 14 unique extended parts per board excluding the hand-soldered sockets, down from 19 / 20 on 11-03 when connectors were counted.
- **C3, MINOR: low stock.**
  - Parts: J10 socket 39, J10 plug 50, HC2 J11 socket 40, HC2 J11 plug 63. All single-source Kefa with custom footprints (decision 98).
  - A 5+5 order and a 10+10 order (20 J10 sets) fit.
  - A 30+30 order needs 60 J10 sets and does not fit.
  - Cheapest fix: buy the connector sets early with spares and recheck stock at order time.
  - TPS48110A at 949 is thin but above 500.
- **C4: single source.** Kefa and Kangnex connectors, Infineon BTT6050, BSC030N08NS5 and IPT007N06N, TI TPS48110A, LMR51610 and LM74500, Chipanalog CA-IS3050G, Espressif module, APV NTC.
- **C5: non-standard values.** None.
- **C6: footprints.** The five new connector footprints and the D31 SMC land are already on the pre-order checklist; not rechecked here.

## Questions for the owner

- **Q1.** Does the JLCPCB quote page force Standard PCBA for U1? Please include it in the Q-0026 check. Default: yes, assume Standard.
- **Q2.** If Standard is forced, hand-reflow U1 (L1, about 7-8 $ per board at 10) or pay for Standard? Default: pay for Standard on the first 5+5 run.
- **Q3.** Keep the 10.16 mm 65 A J10 set on 4-ch (L6)? Default: keep decision 98.
- **Q4.** Accept a DOIT ESPS3-32E module (L2)? Default: no.

## Not checked

- PCB price: no live quote and no JLCPCB 2 oz figure, so the estimate is scaled by area.
- Whether the Standard fixture fee (16.42 $) applies.
- JLCPCB panel surcharge and coupon (Q-0059) conditions.
- Shipping and duties on the owner-bought connectors.
- DOIT datasheet and pinout.
- X5R bias loss of C15849 at 29 V.
- Circuit and EMC correctness (validator and EMC reviewer).

## Notes added when saving

The cost-controller could not write this file because of the worktree guard, so the main session saved its text unchanged and added this section.

- **Re-checked:** C2913206 `pcba_type: standard_only` and the 4.1669 $ price at 10+ (`jlc_get_part`, 2026-11-05). The fixed-fee sums, per-board totals, both-boards totals and the L1, L3, L4 and L5 savings recompute correctly.
- **Connector totals differ slightly from the set table.** The set table sums to 5.04 / 4.54 $ for 4-ch at 10 / 30 and 5.50 $ for HC2 at 30. The per-board table says 5.13 / 4.67 / 5.57 $. The difference is at most 0.13 $ per board and the cause was not traced; the J4 set shows one price for all quantities, which may be part of it.
- **L2 on HC2 is about 9.4 $, not 8.5 $:** 7.75 $ platform + 1.68 $ module price.
- **L1 and L2 depend on Q-0026.** Their platform saving exists only if JLCPCB offers Economic PCBA with 2 oz copper. If 2 oz alone forces Standard, the platform saving is zero: L1 saves nothing and L2 saves only the 1.68 $ module price difference.
- **Update 2026-11-06, Q-0026 answered (decision 99):** the owner found on the JLCPCB quote page that Economic PCBA is not offered with 2 oz copper. Standard is therefore the only basis while the boards stay 2 oz: the Economic rows above do not apply, L1 saves nothing, and L2 saves only the module price difference. The figures and the findings block below are otherwise unchanged from 2026-11-05.

<!-- findings:begin -->
```json
[
  {"id":"C1","kind":"finding","severity":"MAJOR","board":"system","location":"BOM: U1 ESP32-S3-MINI-1-N8 C2913206 (both boards)","summary":"JLCPCB lists C2913206 as standard_only, so the whole order is Standard PCBA: +6.8 USD (4-ch) and +7.8 USD (HC2) per board at 10, +13.7/+15.5 at 5; every earlier cost figure and decisions 33/85 assume Economic","fix":"check the quote page with U1 in the BOM; if Standard is forced apply L1 (U1 hand-soldered, off the order) or accept the cost; merge duplicate lines (L4)","door":"one-way","reason":"money: the assembly process of an order; touches decision 85 (confirmed) if the process changes (policy items 1 and 2)","touches":["money","decision:85"],"cost_delta_usd":6.83},
  {"id":"L1","kind":"lever","severity":"INFO","board":"system","location":"order: U1 ESP32-S3-MINI-1-N8","summary":"Leave U1 off the JLCPCB order and have the owner hand-reflow it (bought separately): Economic PCBA becomes possible, saving about 7.1 USD (4-ch) / 8.1 USD (HC2) per board at 10, 14.3/16.1 at 5, 2.4/2.7 at 30","fix":"decide at order time; no schematic change; add U1 to the owner's hand-soldered list next to J4/J5/J10/J11","door":"one-way","reason":"money (order process) and it changes decision 85, which lists the hand-soldered parts (policy items 1 and 2)","touches":["money","decision:85"],"cost_delta_usd":-7.14},
  {"id":"L2","kind":"lever","severity":"INFO","board":"system","location":"shared sheet: U1 module","summary":"Economic-capable DOIT ESPS3-32E-N4 (C49164659, 2.49 USD, stock 503) instead of ESP32-S3-MINI-1-N8: about 8.5 USD per board at 10; different outline and pinout, no datasheet check, stock under 500","fix":"not recommended before L1 is judged; needs a new footprint, symbol and pin-map review on both boards","door":"one-way","reason":"changes the MCU module, pin map and firmware base on both boards; owner's choice (policy items 2 and 4)","touches":["pin-map","shared-sheet","firmware","new-extended-part","owner-fact"],"cost_delta_usd":-8.5},
  {"id":"L3","kind":"lever","severity":"INFO","board":"system","location":"PCB phase: panel of both designs","summary":"One panel and one PCBA design for both boards saves about 109 USD per order under Standard (5.5 USD per board at 10+10, 10.9 at 5+5, 1.8 at 30+30); JLCPCB multi-design surcharge unverified","fix":"decide at the PCB phase after the JLCPCB panel quote; already decision 33 (conditional)","door":"two-way","reason":"layout decision before any order, within decision 33; no money spent yet","touches":[],"cost_delta_usd":-5.5},
  {"id":"L4","kind":"lever","severity":"INFO","board":"system","location":"BOM lines C14663, C52923, C28323, C31850 (both boards), C23231 (HC2)","summary":"Under Standard PCBA each unique line costs 1.53 USD per order: merging five near-duplicate lines saves 6.1 USD (4-ch) / 7.65 USD (HC2) per order (0.61 / 0.77 USD per board at 10); zero under Economic","fix":"C2 to C307331 (0402), C12 and C13 to C15849 (after DC-bias check at 29 V), R10 to C25768, HC2 R9 to C36871","door":"two-way","reason":"capacitor and resistor part swaps to standard values before any order (Q-0016 condition met); no confirmed decision changes","touches":["shared-sheet"],"cost_delta_usd":-0.61},
  {"id":"L5","kind":"lever","severity":"INFO","board":"system","location":"ordering: boards per order","summary":"30 boards per order instead of 10 saves 10.6 USD (4-ch) / 11.6 USD (HC2) per board under Standard; 10 instead of 5 saves 15.8 / 16.2","fix":"decide quantity at the order (decision 33 fixes 5+5 for the first run)","door":"one-way","reason":"money: order quantity (policy item 1)","touches":["money"],"cost_delta_usd":-10.6},
  {"id":"L6","kind":"lever","severity":"INFO","board":"pdm-4ch","location":"J10 battery connector","summary":"Use the 7.62 mm 32 A set (C577772 + C577752) instead of the 10.16 mm 65 A set on pdm-4ch: saves 1.85 USD per board at 10, but 32 A has no margin at the 32 A input limit with four BTT6010","fix":"only if the 4-ch input limit is lowered to the standard-build 16 A (decision 95) and the BTT6010 option is dropped","door":"one-way","reason":"contradicts decisions 95 and 98 (confirmed) and touches a connector rating and heat-budget limits (policy items 2 and 3)","touches":["decision:95","decision:98","connector","safety"],"cost_delta_usd":-1.85},
  {"id":"C3","kind":"finding","severity":"MINOR","board":"system","location":"connectors J10 C6394053 / C6394029, HC2 J11 C577772 / C577752","summary":"Kefa J10 socket stock 39, plug 50, HC2 J11 socket 40, plug 63: 5+5 and 10+10 fit, 30+30 needs 60 J10 sets and does not; single source, custom footprints","fix":"buy the connector sets early with a few spares; recheck stock at order time","door":"two-way","reason":"purchase timing is the owner's anyway; no design change","touches":[]},
  {"id":"Q1","kind":"question","severity":"MAJOR","board":"system","summary":"Does the JLCPCB quote page force Standard PCBA for U1 ESP32-S3-MINI-1-N8 (include it in the Q-0026 check)?","default":"yes, assume Standard PCBA","door":"two-way","reason":"a sensible default exists; the answer only changes the cost basis until the order","touches":[]},
  {"id":"Q2","kind":"question","severity":"INFO","board":"system","summary":"If Standard is forced: hand-reflow U1 yourself (L1, about 7-8 USD per board at 10) or pay for Standard PCBA?","default":"pay for Standard on the first 5+5 run; no hand soldering of the module","door":"one-way","reason":"money and decision 85 (assembly split); the default is not binding until the owner confirms the order","touches":["money","decision:85"]},
  {"id":"Q3","kind":"question","severity":"INFO","board":"pdm-4ch","summary":"Keep the 10.16 mm 65 A J10 set on pdm-4ch (L6), or lower the 4-ch input limit to 16 A and use the 7.62 mm set?","default":"keep decision 98 as it is","door":"one-way","reason":"contradicts decisions 95 and 98 and the connector rating (policy items 2 and 3)","touches":["decision:95","decision:98","connector","safety"]},
  {"id":"Q4","kind":"question","severity":"INFO","board":"system","summary":"Accept a DOIT ESPS3-32E-N4 module (Economic-capable) instead of the Espressif MINI-1 (L2)?","default":"no","door":"one-way","reason":"module and pin-map change across both boards; owner's choice (policy items 2 and 4)","touches":["pin-map","shared-sheet","firmware","owner-fact"]}
]
```
<!-- findings:end -->
