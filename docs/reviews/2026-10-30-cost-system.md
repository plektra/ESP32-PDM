# Cost review – system (pdm-4ch and pdm-hc2), schematic phase

Date: 2026-10-30. Task T-0002, unattended, deep. Reviewer: cost-controller. No PCB exists yet. This is the first cost
report, so there is no earlier report to compare with.

Sources read:
- `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/decisions.md`, `docs/design-notes.md`, `docs/AUTONOMY.md`.
- Both `STATUS.md` files.
- `docs/reviews/2026-10-30-emc-system.md`, for the cost of the EMC findings.

Method:
- BOMs were exported with `kicad-cli sch export bom` into `$CLAUDE_JOB_DIR/tmp`.
- Netlists were exported with `kicad-cli sch export netlist --format kicadxml`; pad counts and nets come from them.
- The cost model is `$CLAUDE_JOB_DIR/scripts/cost.py`; the lever deltas come from `levers.py`.

Where the prices come from (all fetched 2026-10-30):

| Item | Figure | Source |
|---|---|---|
| Part prices | LCSC tier price matching the order quantity (per-board qty × boards) | pcbparts `jlc_get_part` / `jlc_stock_check`, JLCPCB/LCSC catalogue |
| Economic PCBA setup | 8.18 $ per design per order | [JLCPCB PCB assembly price](https://jlcpcb.com/help/article/pcb-assembly-price), "last updated Oct 22, 2026" |
| Economic stencil | 1.53 $ | same page |
| Confirm parts placement | 0.45 $ | same page |
| Extended part loading fee | 3.07 $ per unique extended part per design per order | same page (the 3.07 $ in my instructions is still current) |
| Basic and preferred extended parts | no loading fee | [JLCPCB PCBA FAQ](https://jlcpcb.com/help/article/pcb-assembly-faqs) |
| SMT placement | 0.0016 $ per joint | assembly price page |
| THT hand soldering | 3.58 $ per order + 0.0164 $ per joint | assembly price page |
| Standard PCBA (for comparison) | 25.56 $ setup + 8.21 $ stencil + 1.53 $ per unique part, basic parts included | assembly price page |
| PCB, 2 layers, 2 oz, ≈ 85 × 55 mm, 1.6 mm, HASL | **ESTIMATE**: 15 $ (5 pcs), 20 $ (10 pcs), 38 $ (30 pcs), ± 50 % | No live quote: the JLCPCB calculator could not be read. JLCPCB lists 2 oz as a standard option without a price ([copper weight guide](https://jlcpcb.com/help/article/jlcpcb-copper-weight), 2026-09-09). A substrate price change took effect on 2026-06-26 ([JLCPCB pricing notice](https://jlcpcb.com/news/jlcpcb-pcb-pricing-notice)). One blog puts the 2 oz upcharge at +2–5 $ for 5 boards ([prototypeguru](https://prototypeguru.com/low-cost-pcb-prototype/)). |
| Economic PCBA limits | single-sided, 2/4/6 layers, 0.8–1.6 mm, 2–50 pcs | [JLCPCB PCBA capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities). The page does **not** say whether 2 oz copper is allowed with Economic PCBA (see Q1). |

Assumptions:
- **Parts with no `LCSC` field** (22 BOM lines, rule finding C1) are priced with the basic or preferred part proposed in C1.
- **J5, J10 and J11** have no part yet. They are priced as estimates:
  - J5: 3.81 mm 10P header, ≈ 0.18 $ (WJ15EDGVC-3.81-10P, interpolated from 9P C49737 at 0.156 $ and 11P C48703 at 0.195 $).
  - J10: KF135T-10.16-2P (C475108), 65 A, 0.57 $.
  - J11: 4-ch ≈ 0.30 $ (4P 5.08 mm); HC2 KF7620-7.62-2P (C475104), 32 A, 0.29 $.
  - Each of them is counted as one extended part.
- **THT joints:** J4 4 + J5 10 + J10 2 + J11 4 (4-ch) or 2 (HC2).
- **Not included:**
  - shipping, customs and VAT;
  - JLCPCB attrition, i.e. the extra passives it orders (< 0.10 $ per board);
  - the loose plug halves, see the separate line below;
  - the enclosure;
  - the additions from the EMC review.

## Figures

### Per board, Economic PCBA, 2 oz (PCB price is an estimate)

| Board | Qty | Parts per board | Fixed per order¹ | PCB per order (est.) | **Per board** | Order total |
|---|---|---|---|---|---|---|
| pdm-4ch (4 × BTT6050) | 5 | 16.62 $ | 65.93 $ | 15 $ | **33.90 $** | 169.50 $ |
| pdm-4ch (4 × BTT6050) | 10 | 15.18 $ | 65.93 $ | 20 $ | **24.87 $** | 248.65 $ |
| pdm-4ch (4 × BTT6050) | 30 | 14.26 $ | 65.93 $ | 38 $ | **18.82 $** | 564.46 $ |
| pdm-hc2 | 5 | 21.82 $ | 72.07 $ | 15 $ | **40.29 $** | 201.47 $ |
| pdm-hc2 | 10 | 20.22 $ | 72.07 $ | 20 $ | **30.49 $** | 304.87 $ |
| pdm-hc2 | 30 | 18.77 $ | 72.07 $ | 38 $ | **23.49 $** | 704.80 $ |

¹ Fixed per order:
- pdm-4ch: setup 8.18 + stencil 1.53 + confirm 0.45 + THT labour 3.58 + 17 extended parts × 3.07 = 65.93 $.
- pdm-hc2: the same with 19 extended parts × 3.07 = 72.07 $.

Other populations and modes, per board at 5 / 10 / 30 units:

| Variant | 5 | 10 | 30 |
|---|---|---|---|
| pdm-4ch, 2 × BTT6010 + 2 × BTT6050 (one more extended part) | 37.64 $ | 28.58 $ | 21.93 $ |
| pdm-4ch, 4 × BTT6010 | 40.16 $ | 30.31 $ | 23.44 $ |
| pdm-4ch, **Standard PCBA**, if 2 oz rules out Economic (Q1) | 44.19 $ | 30.01 $ | 20.53 $ |
| pdm-hc2, **Standard PCBA** | 51.49 $ | 36.09 $ | 25.36 $ |

Kit parts JLCPCB does not assemble, per board (estimate):
- Plug halves: J4 4P WJ15EDGK (C7244) 0.33 $ + J5 10P WJ15EDGK (C26865) 0.87 $ = **1.20 $**. Power terminals are assumed to be fixed screw terminals with no plug.
- Enclosure: self-printed ASA, ≈ 40 g at ≈ 25 $/kg ≈ **1.0 $**. This is an estimate; no JLC3DP quote was taken.

### Top cost drivers at 10 units

**pdm-4ch** (24.87 $ per board):

| Driver | Per board | Share |
|---|---|---|
| Extended-part loading fees (17 × 3.07 $ / 10) | 5.22 $ | 21 % |
| BTT6050-1ERA × 4 (C534868, 1.167 $) | 4.67 $ | 19 % |
| ESP32-S3-MINI-1-N8 (C2913206, 4.176 $) | 4.18 $ | 17 % |
| PCB 2 oz (est.) | 2.00 $ | 8 % |
| ISO1044BDR (C2878225) | 1.62 $ | 7 % |
| Setup, stencil, confirm, THT labour | 1.37 $ | 6 % |
| LMR51610YDBVR (C22427220) | 1.35 $ | 5 % |
| SMT and THT joints (480 + 20) | 1.10 $ | 4 % |
| Terminals J10/J11/J5/J4 (board side) | 1.12 $ | 5 % |
| Everything else (≈ 40 lines) | ≈ 2.2 $ | 9 % |

**pdm-hc2** (30.49 $ per board):

| Driver | Per board | Share |
|---|---|---|
| TPS48110AQDGXRQ1 × 2 (C17556513, 3.283 $) | 6.57 $ | 22 % |
| Extended-part loading fees (19 × 3.07 $ / 10) | 5.83 $ | 19 % |
| ESP32-S3-MINI-1-N8 | 4.18 $ | 14 % |
| BSC030N08NS5 × 4 (C501507, 0.765 $) | 3.06 $ | 10 % |
| PCB 2 oz (est.) | 2.00 $ | 7 % |
| ISO1044BDR | 1.62 $ | 5 % |
| LMR51610YDBVR | 1.35 $ | 4 % |
| Setup, stencil, confirm, THT labour | 1.37 $ | 4 % |
| Joints (476 SMT + 18 THT) | 1.06 $ | 3 % |

**What dominates:**
- At 5–10 boards the fixed costs are 35–40 % of the price: setup, stencil and above all the extended-part fees.
- At 30 boards the fixed costs fall to ≈ 15 %, and the ESP32, the output switches and the ISO1044 dominate.
- The 15 extended parts the two boards share cost 46 $ **twice** when both boards are ordered as separate designs.

### Change since the last report

There was no earlier cost report; this is the baseline.

The open EMC findings (`2026-10-30-emc-system.md`) would add the following if they are adopted (estimates):

| EMC item | Added cost per board | Note |
|---|---|---|
| E3 bulk + HF capacitor at J10 | +0.20–0.30 $ | no basic electrolytic was checked, so this may be +3.07 $/order |
| E5 2 × SMAJ30CA on HC2 outputs | +0.06 $ | preferred part, no fee |
| E1, E4, E7 small ceramics | +0.05 $ | basic parts |
| E6 CMC, if fitted | +0.3 $ and +3.07 $/order | extended |
| EMC lever L1, LMR51610**YF** | +1.48 $ | also low stock, see C4 |

## Levers

Ranked by saving per board at 10 units. "Both boards" means pdm-4ch and pdm-hc2 are ordered in the same run.

| # | Saving | What changes | Trade-off | Must-stay check | Effort | Evidence |
|---|---|---|---|---|---|---|
| L1 | **−6.05 $** (4-ch) / **−7.00 $** (HC2) per board for 30 instead of 10 per order; 10 instead of 5 saves −9.0 / −9.8 $ | Order quantity per run | Cash up front: +316 $ (4-ch) / +400 $ (HC2) for 30 against 10; risk of a respin with stock on the shelf | nothing cut | none | Figures table |
| L2 | **−59.79 $ per order** when both boards are ordered: −2.99 $/board at 10 + 10, −5.98 $ at 5 + 5, −1.00 $ at 30 + 30 | Put pdm-4ch and pdm-hc2 in **one panel**, i.e. one PCBA design. This saves one setup (8.18), stencil (1.53), confirm (0.45), THT labour (3.58) and the 15 shared extended parts (46.05) | Boards come in a fixed 1:1 ratio. Both use the same stack-up (2 oz is fine for both). Panel ≤ 250 × 250 mm. Assembly must be single-sided on both. **UNVERIFIED:** JLCPCB's surcharge for "different designs in a panel" and whether Economic PCBA accepts a multi-design panel | nothing cut | layout: panel at the PCB phase | Fee table; 15 shared extended parts (list in rule finding C2) |
| L3 | **−1.20 $/board per design** at 10 (−12.28 $/order); −24.56 $/order for both boards | Four basic/preferred swaps on the shared sheets (details below) | 3 footprint changes (FB 0603 → 0805, F2 0805 → 1812, ESD 0402 → DFN1006). The LDO goes SOT-23-5 → DPAK, which needs more area; 6 mA Iq from NET-S against 1.8 µA | protection kept or better: the ESD clamp improves from 40 V to 10 V; NMEA isolation is unchanged | small layout effort; datasheet checks: H5VL10B capacitance on USB FS; L78M05 at 29 V clamp | `jlc_get_part` C1017, C7420372, C58069, C19078719 |
| L4 | **−1.30 $/board** at 10 (−2.22 $ at 5) | Make USB-C a DNP or service-pad footprint (D+/D−/VBUS/GND pads for a pogo jig). This removes J3, D4–D6, F2, FB1, D3, R11/R12, C4/C5 and 3 extended fees. Overlaps with L3: after L3 it saves ≈ −0.5 $ | Convenience: flashing and service need a jig or OTA; native USB stays in the design (decision 4 is not touched) | USB is not on the switch → output path; no protection of external lines is lost, because the port is gone | small | `levers.py` usb_dnp |
| L5 | **≈ −1.0 $/board** (estimate) | Fixed screw terminals instead of pluggable header + plug for J4/J5 (plug halves alone are 1.20 $) | No hot-swap of the panel cable in service; no pre-wired harness | nothing cut | decide in `/system mechanical` | C7244 0.33 $, C26865 0.87 $ |
| L6 | **−0.83 $/board** at 10 (both boards) | LMR51610**X**DBVR (C20539658, 400 kHz, 0.521 $ at 10+) instead of **Y** (1.1 MHz, 1.347 $). Same DBV package per the catalogue; stock 3270 | 400 kHz needs a larger L (likely 15–22 µH, unchecked) and different output ripple. Fundamental and harmonics move in the conducted band. This conflicts with EMC lever L1 (YF variant) | nothing cut | datasheet re-design of L/C, EMC review | `jlc_stock_check` LMR51610 |
| L7 | **−0.71 $/board** at 10 | CA-IS3050G (C528763, Chipanalog, 5 kV RMS, 0.916 $ at 10+) instead of ISO1044BDR (1.621 $) | Different package (SOIC-8-WB) and pinout; second source for the transceiver. Datasheet not read: supply ranges and VCC2 must be verified | NMEA 2000 isolation kept (5 kV vs 3 kV RMS) | footprint + datasheet check | `jlc_get_part` C528763 |
| L8 | **−0.32 $/board** at 10 (−3.07 $/order) | TH1 NTC (extended C52155402; no basic or preferred NTC exists on JLCPCB) → MMBT3904 (preferred C7420353) as a diode sensor on IO9 | Lower accuracy, needs a bias resistor and a firmware calibration; decision 18 names the NTC part | heat budget unchanged; the BTT6050 / TPS48110 keep their own thermal shutdown | small + firmware | `jlc_search` NTC no_fee: 0 results |
| L9 | avoids **+3.71 $/board** (4-ch, 2 + 2 mix) | Population policy: fit BTT6010 only on channels that need > 4 A. Order mixed builds in the same order so the extra BTT6010 fee (3.07 $) is paid once | none | heat budget per channel unchanged (decision 7, `heat_budget.py --mix`) | documentation | `levers.py` mix / all6010 |
| L10 | −0.01 $/board | HC2: remove R1/R2 (pull-downs on unused IO8/IO11) | Breaks "controller part identical on both boards". **Recommendation: keep** | – | – | STATUS pdm-hc2 item 6 |

L3 in detail. Each swap removes one extended part type, saving 3.07 $ per order per design:

| Part now | Replacement | Note |
|---|---|---|
| FB1/FB2 BLM18AG601SN1D (C19330, extended) | GZ2012D601TF (C1017, basic) | 600 Ω @ 100 MHz, 500 mA, 0805. FB1 carries USB VBUS, so the basic 0603 C1002 (200 mA) is **not** enough there |
| F2 SMD0805B050TF (C269104) | the 1812L050/60GR already used for F1/F3/F4 | same 0.5 A hold, 60 V |
| D4–D6 PESD0402V05 (C19626254) | H5VL10B (C7420372, preferred) | DFN1006-2L, 5 V, clamp 10 V, 15 pF |
| U6 TPS7B91 (C37396819) | L78M05ABDT-TR (C58069, basic) | DPAK, 35 V, 500 mA. 78L05/HT7550 (30 V) were rejected: too close to the SMAJ18CA clamp of 29.2 V |

Not proposed as levers:
- **1 oz copper.** The heat-budget ratings must stay (4 A per BTT6050 needs 2 oz).
- **Fewer TVS diodes.** Must stay.
- **ESP32-S3 chip-down or ESP32-C6.** Decision 4.
- **PESD2CAN → SMF24CA.** No no-fee CAN-rated part with known capacitance was found.
- **SMCJ30CA → smaller TVS.** It is surge protection.

**Five largest levers:**
1. L1, board count per order.
2. L2, one panel for both boards.
3. L3, four basic swaps.
4. L4, USB-C DNP.
5. L5, fixed terminals.

## Rule findings

**C1 – Parts with no `LCSC` field (MINOR, system, shared sheets).** 22 BOM lines on both boards have no part number,
so JLCPCB cannot place them as drawn. Proposed codes, all basic or preferred and checked 2026-10-30:

| Ref | Value | Proposed | Notes |
|---|---|---|---|
| C2, C13 | 100 nF 0603 | C14663 | basic, 50 V |
| C4, C6 | 1 µF 0603 | C15849 | basic, 50 V; already used on HC2 |
| C5 | 4.7 µF/16 V 0603 | C19666 | basic |
| C7, C9 | 100 nF 0805 | C28233 | basic, 100 V; already on the BOM |
| C8 | 22 µF 0805 | C45783 | basic, 25 V, on 3V3 |
| C10, C11 | 100 nF 0402 | C307331 | already on the BOM |
| C12 | 1 µF 0402 | C52923 | basic, 25 V, on the 5 V CAN side |
| D12–D15 (HC2: D12, D13) | BAT54C | C22466350 | hongjiacheng, preferred |
| FB1, FB2 | BLM18AG601SN1D | C19330 as drawn (extended), or C1017 (L3) | |
| R1, R2, R5, R6 | 2.2 k 0402 | C25879 | |
| R11, R12 | 5.1 k 0402 | C25905 | |
| R15–R17, R21, R24, R27 | 10 k 0402 | C25744 | already on the BOM |
| J5, J10, J11 | – | no footprint or part yet | `/system mechanical` |

**C2 – Extended parts where a basic or preferred part fits.**
- These are the four parts in L3.
- No no-fee alternative exists on JLCPCB for: USB-C, PTC fuses, power inductors, NTC, isolated CAN, the buck, the BTT/TPS
  switches, the shunt, pluggable or screw terminals, and the ESP32. Each was checked with `jlc_search` / `jlc_stock_check`
  `library_type=no_fee`, and each returned no candidate.
- Shared extended parts, 15 per design:
  - J3 USB-C (C165948), F1/F3/F4 (C19078719), FB (C19330), PESD0402V05, LMR51610Y, PESD2CAN, F2 (C269104), ISO1044,
    ESP32-S3-MINI-1-N8, TPS7B91, NTC, J4 (C8410), L1 (C96963).
  - J10 and J5, once chosen.
- Board-only extended parts:
  - pdm-4ch: BTT6050 and J11.
  - pdm-hc2: TPS48110A, BSC030N08NS5, the 1 mΩ shunt (C2903470) and J11.

**C3 – Non-standard values.** None. All resistors are E24/E12 (5.1 k, 6.8 k ×10, 3.9 k ×10, 1.2 k ×10, 22 Ω, 680 Ω
included), and so are the capacitors and the 8.2 µH. Pass.

**C4 – Low stock and single source (INFO).**
- Nothing on the BOM is below 500 today. Live stock 2026-10-30:

  | Part | Stock |
  |---|---|
  | TPS48110AQDGXRQ1 | **999** (60 used at 30 boards) |
  | SWPA6045S8R2MT | 1 231 |
  | BTT6050-1ERA | 1 748 |
  | LMR51610YDBVR | 2 228 |
  | TPS7B91 | 2 516 |
  | BTT6010-1ERA | 2 713 |

- **Below 500:**
  - LMR51610**YF** (EMC lever L1): 458.
  - 3.81 mm 11P header: 436 (the 10P needs checking when J5 is chosen).
- **Single source:**
  - BTT60x0 and BSC030N08NS5: Infineon.
  - TPS48110A, LMR51610 and ISO1044: TI. The ISO1044 has the CA-IS3050G as an alternative (L7).
  - ESP32 module: Espressif.
  - The APV NTC.
- **L1 second sources** in the same 6045 size: SLW6045S8R2MST (C47018494) and FNR6045S8R2MT (C168074). Their stock is
  ≈ 1 500 each.
- Re-check stock before ordering; at 30 boards the TPS48110A stock is the tightest.

**C5 – Unique basic parts matter only under Standard PCBA (INFO).**
- Standard PCBA charges 1.53 $ for every unique part, basic included (52 on pdm-4ch, 59 on pdm-hc2).
- Merging package variants would cut about 6 lines (≈ 9 $ per order), but only if Q1 forces Standard PCBA:
  - 100 nF in 0402/0603/0805;
  - 1 µF in 0402/0603;
  - 10 k and 4.7 k 0402 vs 1206 (the 1206 parts are deliberate: input voltage and pulse).
- Under Economic PCBA the saving is 0.

## Questions for the owner

1. **Q1 – 2 oz with Economic PCBA.**
   - JLCPCB's capability page lists no copper limit for Economic PCBA. An old forum report says assembly was not offered
     with 2 oz.
   - Please check the JLCPCB quote page with 2 oz + Economic PCBA. If only Standard is offered, add +5.1 $/board
     (4-ch) or +5.6 $/board (HC2) at 10.
   - 1 oz is not a fix, because the heat-budget ratings depend on 2 oz.
2. **Q2 – How many of each board per order?** Vega's needs set the order size, and order size is the largest lever (L1).
3. **Q3 – One panel for both boards (L2)?** This only works if the boards are always needed in pairs, or if spares of
   one type are acceptable.
4. **Q4 – USB-C as a fitted connector, or service pads only (L4)?**
5. **Q5 – Pluggable or fixed terminals (L5)?** To be settled in `/system mechanical`.
6. **Q6 – NMEA 2000 bus side.** Must the isolated side stay powered from NET-S? If not, a CA-IS3050 variant with
   integrated isolated supply (C41383098, catalogue only) could also replace the TPS7B91/FB2/D11 chain. This was not
   evaluated.
7. **Q7 – Standard population for Vega's pdm-4ch.** All BTT6050, or a 2 + 2 mix (L9)? It depends on the load list
   (design-notes §9).

## Not checked

- The **PCB price** was not quoted live. The figures are estimates (± 50 %), as is the effect of the June 2026 substrate
  price change.
- The **multi-design panel** surcharge and whether Economic PCBA accepts one (L2).
- **Datasheets** were not read for the lever replacements: H5VL10B, L78M05ABDT, CA-IS3050G, LMR51610X (inductor and
  capacitor values) and GZ2012D601TF. Every lever needs a `part-facts` check before it is adopted.
- **Thermal check of U6 TPS7B91** (SOT-23-5) at NET-S 16 V with the ISO1044 bus-side current. It looks warm; this is for
  the validator. L3's DPAK would also solve it.
- **Footprint name.** U1 uses `RF_Module:ESP32-S2-MINI-1` for an ESP32-S3-MINI-1. The validator should confirm it is the
  intended, identical land pattern.
- **Enclosure** cost: no JLC3DP quote, and no DIN clip or hardware priced.
- **Panel side.** Front-panel switches, LEDs and cable are not on these BOMs.
- **Not included in the totals:** shipping, customs/VAT and JLCPCB attrition.
- **4-layer stack-up** (EMC layout rule 3). Not priced; expect a clearly higher PCB cost than 2 layers with 2 oz.

<!-- findings:begin -->
```json
[
  {
    "id": "C1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "system",
    "location": "root, power-usb, can, analog_sw: C2,C4-C13,D12-D15,FB1,FB2,R1,R2,R5,R6,R11,R12,R15-R17,R21,R24,R27,J5,J10,J11",
    "summary": "22 BOM lines have no LCSC field, so JLCPCB cannot place them as drawn",
    "fix": "Add the basic/preferred codes listed in rule finding C1 (C14663, C15849, C19666, C28233, C45783, C307331, C52923, C22466350, C25879, C25905, C25744); J5/J10/J11 in /system mechanical",
    "class": "big",
    "reason": "Missing LCSC field is a small change in kind, but it touches shared sheets and board=system",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "C4",
    "kind": "finding",
    "severity": "INFO",
    "board": "system",
    "location": "U3/L1 (power-usb), U11/U12 (pdm-hc2 hc_channel), BTT6050",
    "summary": "Nothing is below 500 in stock, but TPS48110A (999), L1 SWPA6045S8R2MT (1231) and BTT6050 (1748) are thin and single-source; the EMC option LMR51610YF has only 458",
    "fix": "Re-check stock before ordering; note L1 second sources SLW6045S8R2MST C47018494 / FNR6045S8R2MT C168074 after a datasheet check",
    "class": "big",
    "reason": "board=system, affects shared sheet power-usb",
    "touches": ["shared-sheet"]
  },
  {
    "id": "C5",
    "kind": "finding",
    "severity": "INFO",
    "board": "system",
    "location": "BOM, package variants of 100 nF / 1 uF",
    "summary": "52/59 unique parts cost 1.53 $ each only under Standard PCBA; merging package variants would save ~9 $ per order then",
    "fix": "Only if Q1 forces Standard PCBA: merge 100 nF and 1 uF package variants",
    "class": "big",
    "reason": "board=system, shared sheets",
    "touches": ["shared-sheet"]
  },
  {
    "id": "L1",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "ordering",
    "summary": "Order 30 instead of 10 per run: -6.05 $/board (4-ch), -7.00 $/board (HC2); 10 instead of 5 saves -9.0/-9.8 $",
    "fix": "Owner sets the order quantity per board from Vega's needs",
    "class": "big",
    "reason": "Cost lever needing an owner decision on quantity and cash; board=system",
    "touches": [],
    "cost_delta_usd": -6.05
  },
  {
    "id": "L2",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "PCB/PCBA ordering, panel",
    "summary": "One panel holding pdm-4ch + pdm-hc2 saves one setup, stencil, THT fee and 15 shared extended fees: -59.79 $/order (-2.99 $/board at 10+10)",
    "fix": "Panelise both designs as one PCBA design at the PCB phase, after checking the JLCPCB multi-design surcharge",
    "class": "big",
    "reason": "Trades flexibility (fixed 1:1 ratio), mechanical/panel choice, board=system",
    "touches": ["mechanical"],
    "cost_delta_usd": -2.99
  },
  {
    "id": "L3",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "power-usb FB1, F2, D4-D6; can FB2, U6",
    "summary": "Four basic/preferred swaps remove 4 extended fees: FB->GZ2012D601TF C1017, F2->1812L050/60GR, PESD0402V05->H5VL10B C7420372, TPS7B91->L78M05ABDT C58069",
    "fix": "Adopt after part-facts checks (USB FS capacitance of H5VL10B, L78M05 at 29 V clamp, DPAK area)",
    "class": "big",
    "reason": "Touches shared sheets and changes footprints; protection parts swapped",
    "touches": ["shared-sheet", "protection"],
    "cost_delta_usd": -1.2
  },
  {
    "id": "L4",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "power-usb J3, D4-D6, F2, FB1, D3, R11, R12, C4, C5",
    "summary": "USB-C as DNP or pogo pads removes 3 extended fees and ~0.27 $ parts: -1.30 $/board at 10 (overlaps L3)",
    "fix": "Owner decides whether a fitted USB-C service port is needed",
    "class": "big",
    "reason": "Connector change on a shared sheet; trades a convenience feature",
    "touches": ["shared-sheet", "connector"],
    "cost_delta_usd": -1.3
  },
  {
    "id": "L5",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "J4, J5 (and J10/J11 when chosen)",
    "summary": "Fixed screw terminals instead of pluggable header + plug: about -1.0 $/board (the plug halves alone cost 1.20 $)",
    "fix": "Decide in /system mechanical",
    "class": "big",
    "reason": "Connector and mechanical choice",
    "touches": ["connector", "mechanical"],
    "cost_delta_usd": -1.0
  },
  {
    "id": "L6",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "power-usb U3 LMR51610YDBVR, L1",
    "summary": "LMR51610XDBVR (400 kHz, C20539658, 0.52 $) instead of the Y variant (1.35 $): -0.83 $/board; needs a re-designed L/C and conflicts with EMC lever L1",
    "fix": "Evaluate with the datasheet and the EMC reviewer before adopting",
    "class": "big",
    "reason": "Shared sheet, changes the switching frequency (EMC)",
    "touches": ["shared-sheet"],
    "cost_delta_usd": -0.83
  },
  {
    "id": "L7",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "can U5 ISO1044BDR",
    "summary": "CA-IS3050G (C528763, 5 kV RMS, 0.92 $ at 10+) instead of ISO1044 (1.62 $): -0.71 $/board, second source; different package/pinout",
    "fix": "part-facts check of the CA-IS3050G datasheet (supplies, pinout, timing), then footprint change",
    "class": "big",
    "reason": "Shared sheet, NMEA 2000 isolation part replaced",
    "touches": ["shared-sheet", "protection", "new-extended-part"],
    "cost_delta_usd": -0.71
  },
  {
    "id": "L8",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "root TH1 (NTC, IO9)",
    "summary": "No basic NTC exists; an MMBT3904 diode sensor (preferred) would remove one extended fee: -0.32 $/board at 10, at the cost of accuracy and calibration",
    "fix": "Owner decides whether NTC accuracy is worth 3.07 $ per order",
    "class": "big",
    "reason": "Changes confirmed decision 18 (named NTC part) and firmware",
    "touches": ["decision:18", "shared-sheet", "firmware"],
    "cost_delta_usd": -0.32
  },
  {
    "id": "L9",
    "kind": "lever",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "U11-U14 population",
    "summary": "Each BTT6010 channel adds 1.57 $ at 10 and a mixed build adds one 3.07 $ fee per order (2+2 mix: +3.71 $/board); fit BTT6010 only where > 4 A and order mixed builds together",
    "fix": "Document the population and ordering rule in pdm-4ch STATUS / README",
    "class": "small",
    "reason": "Documentation only, follows confirmed decision 7, no design change",
    "touches": [],
    "cost_delta_usd": 0.0
  },
  {
    "id": "L10",
    "kind": "lever",
    "severity": "INFO",
    "board": "pdm-hc2",
    "location": "root R1/R2 (IO8/IO11 pull-downs)",
    "summary": "Removing R1/R2 on HC2 saves only ~0.01 $/board; recommendation is to keep the controller part identical",
    "fix": "Keep as is",
    "class": "big",
    "reason": "Controller part of the root sheet is shared",
    "touches": ["shared-sheet"],
    "cost_delta_usd": -0.01
  },
  {
    "id": "Q1",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "PCB fabrication / PCBA mode",
    "summary": "Does JLCPCB accept 2 oz copper with Economic PCBA? If not, Standard PCBA adds +5.1 $ (4-ch) / +5.6 $ (HC2) per board at 10",
    "fix": "Owner checks the JLCPCB quote page with 2 oz + Economic PCBA before layout",
    "class": "big",
    "reason": "Question; affects the budget",
    "touches": ["budget"]
  },
  {
    "id": "Q2",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "ordering",
    "summary": "How many pdm-4ch and pdm-hc2 boards per order (5, 10, 30)? This is the largest cost lever",
    "fix": "Owner states the quantities for Vega and spares",
    "class": "big",
    "reason": "Question",
    "touches": []
  },
  {
    "id": "Q3",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "panel",
    "summary": "Is a combined 1:1 panel of pdm-4ch + pdm-hc2 acceptable (L2)?",
    "fix": "Owner decides",
    "class": "big",
    "reason": "Question",
    "touches": ["mechanical"]
  },
  {
    "id": "Q4",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "power-usb J3",
    "summary": "Is a fitted USB-C service connector required, or are pads/DNP plus OTA enough (L4)?",
    "fix": "Owner decides",
    "class": "big",
    "reason": "Question",
    "touches": ["connector", "shared-sheet"]
  },
  {
    "id": "Q5",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "J4, J5, J10, J11",
    "summary": "Pluggable or fixed screw terminals (L5)?",
    "fix": "Settle in /system mechanical",
    "class": "big",
    "reason": "Question",
    "touches": ["connector", "mechanical"]
  },
  {
    "id": "Q6",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "can sheet, NET-S supply",
    "summary": "Must the isolated CAN side stay powered from NET-S? If not, an isolated CAN part with integrated isolated supply could also remove the TPS7B91/FB2/D11 chain",
    "fix": "Owner/architect confirms the NMEA 2000 powering requirement",
    "class": "big",
    "reason": "Question; touches NMEA isolation and a shared sheet",
    "touches": ["shared-sheet", "protection"]
  },
  {
    "id": "Q7",
    "kind": "question",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "U11-U14 population",
    "summary": "Standard population for Vega's pdm-4ch: all BTT6050 (24.87 $) or a 2+2 mix with BTT6010 (28.58 $ at 10)?",
    "fix": "Owner decides from the load list",
    "class": "big",
    "reason": "Question",
    "touches": ["decision:7"]
  }
]
```
<!-- findings:end -->
