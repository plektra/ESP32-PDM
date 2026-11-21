# pdm-4ch: KiCad footprints against the JLCPCB (EasyEDA) footprints – 2026-11-21

Pre-order checklist item (T-0065, T-0067, T-0118, T-0121, T-0143, T-0160, decision 238). Scripted: `tools/fp_check/`
(KiCad pads from the routed board; EasyEDA pads from `jlc_get_pinout footprint=true` through the pcbparts server).
37 LCSC parts compared: every fitted part except plain 0402/0603/0805 values already covered by one representative
each, and the four hand-soldered connectors J4, J5, J10, J11 (checked 2026-11-08). Design files unchanged.

**What the comparison means.** JLCPCB solders on our copper and our stencil. Their EasyEDA footprint only decides
where the machine puts the part: they align its origin to our CPL position and turn it by our CPL rotation. So
there are two questions per part: (1) is our land right for the part (datasheet), and (2) does the CPL put the
part on it (rotation and origin). The CPL from `tools/jlc_package.py` carries KiCad's raw origin and rotation.

## Summary

| Result | Parts |
|---|---|
| Land pass, no CPL correction | all 0402/0603/0805/1206 R and C (incl. RIS C844867, C170101, C9196), C31 C487384, F1–F4 C70113, R54–R56 C7420022, L1 C96963, FB1/FB2 C1017, D1/D10/D16–D19/D50–D54 SMA, D20–D24 SOD-123, D4–D6 SOD-882, TH1, D7/D8 LED (polarity right at 0°), SW_BOOT1/SW_RESET1 |
| Land pass, smaller than the maker's suggestion (accepted) | D30/D31 SMC, D2/D3/D11/D55/D101–D401 SOD-123FL |
| Land pass, **CPL rotation correction** | U3, U5, U11–U14, U30, Q3–Q6, D9, D12–D15, D102–D402 |
| Land pass, **CPL origin correction** | U1 (2.55 mm), J3 (1.57 mm), U6 (1.56 mm), Q30 (270° and 1.6/1.8 mm) |
| **Mismatch, DNP** | FL1: winding pairs on the wrong pads (see F1 below). Not fitted on this order |

Stock 2026-11-21 (snapshot): every fitted part in stock. Thinnest: L1 C96963 1173, BTT6050 C534868 1604 (8 needed),
Q30 C5464765 1650 (live), U30 C5219203 1993, SMDJ40CA 9513, SMAJ30CA 23897 (was 172 on 2026-11-17).
ESP32-S3-MINI C2913206 is `standard_only` (the order is Standard PCBA already).

## Findings

**F1 – FL1 (DNP) cannot be fitted as drawn.** The cjiang land (L 5.5, G1 2.9 mm, design-notes §8.5) matches the
EasyEDA footprint exactly, so EasyEDA's numbering is the only pad map there is. It puts each winding end to end
along the long axis: 1 (−2.1, +1.2) → 2 (+2.1, +1.2) and 4 (−2.1, −1.2) → 3 (+2.1, −1.2). Our
`L_CommonModeChoke_Coilank_ACM4532` pads 1 (−1.8, −1.1) and 2 (−1.8, +1.1) sit on the same short side, and the nets
pair them (CANH_BUS–CANH_XCVR). Fitted at 0°, one winding would join CANH_XCVR to CANL_XCVR; at 90° the land does not
fit the body. No effect on this order: FL1 is DNP and R71/R72 bridge it. Before FL1 is ever fitted, the footprint
pads must be renumbered (1 BL, 2 BR, 3 TR, 4 TL in EasyEDA's frame) and the four CAN tracks and R71/R72 rerouted.
The cjiang drawing still numbers no pads, so confirm on a sample with an ohmmeter (1–2 and 4–3 a few hundred mΩ).

**F2 – CPL rotation.** The CPL carries KiCad rotations. These parts need JLCPCB rotation = KiCad + correction:

| Parts | Package | Correction | Basis |
|---|---|---|---|
| U30 C5219203 | DDF (SOT-23-8 thin) | +180° | pad fit 0.07 mm; names EN/UVLO, GND, NC, VCAP, VS, GATE, OV, SRC match the nets |
| U5 C528763 | SOIC-8 WB | +270° | pad fit 0.13 mm; VCC1, RXD, TXD, GND1, GND2, CANL, CANH, VCC2 match |
| U3 C22427220 | SOT-23-6 | +270° | pad fit 0.01 mm; CB, GND, FB, EN, VIN, SW match |
| U11–U14 C534868 | TDSO-14 | +270° | pad fit 0.40 mm (EasyEDA leads 0.2 mm longer); IN, DEN, IS, GND, OUT, EP match |
| Q3–Q6 C2145 | SOT-23 | +180° | B, E, C match |
| D12–D15 C22466350 BAT54C | SOT-23 | +180° | A, A, K match |
| D102–D402 C7420333 BAT54S | SOT-23 | +180° | by number; EasyEDA names the pins K1/K2/A (its symbol), our nets follow the standard BAT54S pinout 1 = A1, 2 = K2, 3 = K1/A2 |
| D9 C2687131 PESD2CAN | SOT-23 | +180° | by number; UMW datasheet (Feb 2025, p. 1, §4 Pinning information): pin 3 = common of the two bidirectional TVS, 1 and 2 = lines. Our pad 3 = GND_CAN, 1/2 = CANH_BUS/CANL_BUS: pass |

The SOT-23/SOIC/SOT-23-6 values are the ones the usual JLCPCB rotation tables give, which confirms the sign.
**D7/D8 (C2286): no correction.** The number fit says 180°, but EasyEDA's pad 1 is the anode and ours is the cathode;
at 0° the anode lands on our anode pad (Net-(D7-A)). T-0160 closes: keep the KiCad rotation.

**F3 – CPL origin.** EasyEDA puts the origin elsewhere on four parts (offset = EasyEDA origin in the KiCad footprint
frame, then rotated with the part):

| Part | Offset (footprint frame) | Why |
|---|---|---|
| U1 C2913206 | (0, +2.55) mm | KiCad origin = module body centre (antenna included), EasyEDA = pad-array centre. Pads match to 0.03 mm (KiCad footprint ESP32-S2-MINI-1, same land) |
| J3 C165948 | (0, −1.57) mm | Pads match to 0.00 mm; shell holes 0.15 mm apart relative to the pads (KiCad slots 0.6 mm, EasyEDA round 0.8 mm), harmless |
| U6 C58069 | (−1.56, 0) mm | KiCad TO-252-2 origin off the body centre; pads match to 0.01 mm |
| Q30 C5464765 | (−1.60, −1.80) mm, with +270° | EasyEDA origin off the package centre; aligned on the lead-pad centres |

**F4 – Q30 land (T-0121).** The AGM601LL datasheet (VER2.65 p. 5, rendered) gives pitch 1.20, lead length L 1.70,
overall H 11.70, exposed drain depth H2 7.00, drain edge to lead root about 3.0 mm (H3 3.00 BSC / K 3.10 REF), no
land pattern. Our `Infineon_PG-HSOF-8-1` (TOLL = PG-HSOF-8-1): 8 leads at 1.2 mm, lead pads 2.6 mm with ≈ 0.7 mm toe
and ≈ 0.2 mm heel past the leads, drain paste array 7.0 mm deep. Pass. EasyEDA's drain land starts 1.95 mm from the
lead pads (ours ≈ 3.2 mm); irrelevant, since our copper is what gets soldered.

**F5 – lands smaller than the maker's suggestion (accepted, no change).**
- D30 C19077607, D31 C42371557 (SMC, hongjiacheng; suggested pads ≥ 3.03 × 3.82 mm, gap ≤ 3.84 mm): KiCad `D_SMC`
  2.5 × 3.3 mm, gap 4.3 mm. The pads still cover the leads of every SMC body (lead tips 7.75–8.13 mm). Smaller fillets
  only. A larger land would mean moving copper at J10 and the VS pour; not worth it for the prototypes.
- D2/D3/D11/D55/D101–D401 C22466351 (SOD-123FL; suggested J ≥ 1.00, K ≤ 1.90, M ≥ 1.50 mm): KiCad `D_SOD-123F` 1.1 ×
  1.1 mm, gap 1.7 mm. J and K pass, the width M 1.1 mm is under 1.5 mm but covers the 1.0–1.2 mm terminal.
- F1–F4 C70113: our 3.15 mm gap equals the datasheet's 3.2 mm; our pads end 0.45 mm past the body instead of 1.0 mm
  (1.125 × 3.4 mm against 1.78 × 3.2 mm). Terminals (≥ 0.30 mm) fully on copper. Pass.

## Per part (lands)

G = gap between pads, Z = outer span, mm. KiCad / EasyEDA / maker where known.

| Parts | Package | KiCad | EasyEDA | Maker / verdict |
|---|---|---|---|---|
| R103…R407 C844867 | 1206 | G 1.80, Z 4.05 | G 1.75, Z 4.17 | Vishay G 1.50, Z 3.60, X 1.80: pass (decision 238) |
| C1, C3, C22, C30, C104–C404 C170101; C18, C50–C53, C70 C9196 | 1206 | G 1.80, Z 4.10 | G 1.70, Z 4.67 | pass |
| C31 C487384 | CP_Elec_8x10 | pads 3.5 × 2.5, G 3.00, Z 10.0 | 4.2 × 1.4, G 2.33, Z 10.73 | base 8.3 × 8.3, E 3.1: pass |
| F1–F4 C70113 | 1812 | 1.125 × 3.4, G 3.15, Z 5.40 | 1.41 × 3.5, G 2.30, Z 5.11 | 1.78 × 3.2, G 3.2: pass (F5) |
| R54–R56 C7420022 | 2512 | G 4.70, Z 7.15 | G 4.85, Z 7.41 | body 6.4, terminal 0.95 ± 0.25: pass |
| L1 C96963 | SWPA6045 | 1.7 × 5.7, G 2.80 | 2.2 × 5.72, G 2.80 | Sunlord 1.7 × 5.7, a 2.8: pass, exact |
| FB1/FB2 C1017 | 0805 | G 1.25, Z 3.00 | G 0.80, Z 3.06 | pass |
| D4–D6 C7420372 | SOD-882 | 0.40 × 0.70 | 0.30 × 0.60 | bidirectional; pass |
| D1, D10, D16–D19, D50–D54 C19077548/C19077539 | SMA | 2.5 × 1.8, G 1.50, Z 6.50 | 2.07 × 2.06, G 1.79, Z 5.93 | bidirectional; pass |
| D20–D24 C19077396 | SOD-123 | G 2.40, Z 4.20 | G 2.36, Z 4.18 | K on pad 1 = SW net, A = GND: pass |
| D30 C19077607, D31 C42371557 | SMC | 2.5 × 3.3, G 4.30, Z 9.30 | 3.0 × 3.8, G 3.84–4.60 | accepted (F5) |
| D2, D3, D11, D55, D101–D401 C22466351 | SOD-123FL | 1.1 × 1.1, G 1.70 | 1.2 × 1.4, G 2.20 | K pad 1 on both; accepted (F5) |
| D7/D8 C2286 | LED 0603 | G 0.70, Z 2.45 | G 0.70, Z 2.30 | polarity right at 0° (F2) |
| TH1 C52155402, 0402/0603/0805 basics | chip | – | – | pass (pad-centre error ≤ 0.1 mm) |
| SW_BOOT1/SW_RESET1 C318884 | TS-1187A | 4 pads ±3.0 / ±1.875 | ±3.0 / ±1.85 | KiCad numbers the rows 1,1 / 2,2; the 6.0 × 3.7 mm land cannot take the part at 90°, so the switch cannot short IO0/EN to GND by rotation: pass |
| U1, J3, U6, Q30 | – | – | – | pass, origin correction (F3, F4) |
| U3, U5, U11–U14, U30, SOT-23 parts | – | – | – | pass, rotation correction (F2) |
| FL1 C20624726 (DNP) | 4532 CMC | – | – | **mismatch** (F1) |

## Corrected CPL rows (current board)

| Ref | KiCad rot | JLCPCB rot | Mid X | Mid Y | corrected Mid X | corrected Mid Y |
|---|---|---|---|---|---|---|
| U30 | 180 | 0 | 142.45 | −89.25 | – | – |
| U5 | 0 | 270 | 171.45 | −106.45 | – | – |
| U3 | 90 | 0 | 119.75 | −112.15 | – | – |
| U11 / U12 / U13 / U14 | 180 | 90 | – | – | – | – |
| Q3 / Q4 / Q5 | 90 | 270 | – | – | – | – |
| Q6, D9, D13, D14, D102–D402 | 0 | 180 | – | – | – | – |
| D12, D15 | 90 | 270 | – | – | – | – |
| Q30 | 0 | 270 | 148.15 | −96.95 | 146.55 | −95.15 |
| U1 | 0 | 0 | 169.20 | −59.70 | 169.20 | −62.25 |
| J3 | 180 | 180 | 115.15 | −54.15 | 115.15 | −55.72 |
| U6 | 0 | 0 | 186.65 | −121.35 | 185.09 | −121.35 |

Whether JLCPCB's engineers would have caught these in their review is not known; the placement preview at order
time remains the final check, with this table as the expected result.

## Not done here

- Applying the corrections: `tools/jlc_package.py` still writes KiCad's raw rotation and origin (owner's choice, see
  STATUS "Next").
- KiCad title-block comments for decision 220 (the silkscreen already has the licence).
- Connectors J4, J5, J10, J11: checked 2026-11-08, hand-soldered, not in the CPL.

<!-- findings:begin -->
```json
[
  {
    "id": "FP1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "FL1 (DNP), footprint L_CommonModeChoke_Coilank_ACM4532, CAN sheet",
    "summary": "The EasyEDA/cjiang pad order of C20624726 runs each winding along the long side (1-2, 4-3); our footprint pairs pads 1-2 on the short side, so a fitted FL1 would join CANH_XCVR to CANL_XCVR. FL1 is DNP and bridged by R71/R72, so this order is unaffected.",
    "fix": "Before FL1 is ever fitted: renumber the footprint to the EasyEDA order, reroute the four CAN tracks and R71/R72, confirm the windings on a sample.",
    "door": "two-way",
    "reason": "DNP part; layout change only when the EMC scan asks for FL1.",
    "touches": [],
    "cost_delta_usd": 0.0
  },
  {
    "id": "FP2",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-4ch",
    "location": "fab/ESP32-PDM-4CH-cpl-jlc.csv from tools/jlc_package.py",
    "summary": "The CPL carries KiCad's raw rotation and origin. U3, U5, U11-U14 (+270), U30, Q3-Q6, D9, D12-D15, D102-D402 (+180) need a rotation correction and U1, J3, U6, Q30 an origin correction against the JLCPCB footprints; uncorrected they rely on JLCPCB's review to catch it.",
    "fix": "Add a per-LCSC rotation/origin correction table to tools/jlc_package.py (values in this report), rebuild the package, compare with the JLCPCB placement preview.",
    "door": "two-way",
    "reason": "Fabrication-file tooling only; no part, schematic or copper change.",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
