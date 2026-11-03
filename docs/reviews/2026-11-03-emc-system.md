# EMC review – system (pdm-4ch and pdm-hc2), schematic phase, re-check

Date: 2026-11-03. Task T-0087, unattended. Reviewer: emc-reviewer. No PCB exists (`hardware/*/` holds no `.kicad_pcb`),
so there is no `layout` check.

Sources read: `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/AUTONOMY.md`, `docs/decisions.md` (1–71),
`docs/design-notes.md` §4a, §5, §8, `README.md`, the earlier `docs/reviews/2026-10-30-emc-system.md` and the current netlists of
both boards (`kicad-cli sch export netlist --format kicadxml`, scratch folder). Part facts: `docs/part-facts/C487384.md`
(created for this run: Ymin VKM catalogue pages, reverse-voltage question).

## Summary

The earlier review (E1–E15) has been worked through. Nearly all of it is now in the netlists. I found two new points.

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| MAJOR | 1 |
| MINOR | 1 |

- **E16 (MAJOR):** the bulk capacitors on VS (C31, and C106/C206 on HC2) are polarised aluminium electrolytics. The README
  says the 4-ch board survives a reversed battery; nothing in the datasheet supports that for these capacitors.
- **E17 (MINOR):** the cable practice the EMC design relies on never reached the README.

### Status of the earlier findings (checked against the netlists)

| Earlier | State now | Evidence |
|---|---|---|
| E1 HC2 VS pin | closed | R114/R214 100 Ω in front of VS_CTRL (U11/U12 pin 20), C102/C202 1 µF/100 V (decision 58) |
| E2 HC2 gate speed | **still open, already tracked** | R104/R204 10 Ω in the PU path, PD (pin 14) wired straight to GATE, no capacitor on GATE. Decision 25 asked for slew control, but T-0070 found 20 A into 1000 µF outside the MOSFET SOA; Q-0049/Q-0050 (parked) now ask for a short EMC-only slew. Not repeated in the block. Until then: no PWM on HC2 and the switching clicks stay. |
| E3 battery input | closed | C30 1 µF/100 V on VBAT_IN with D30, C31 100 µF/63 V on VS, C104–C404 at each VS tab, 3 × 100 µF on HC2, FL30/JP30 (decisions 41, 42, 44) |
| E4 HC2 sense pins | closed, Y caps DNP | C107/C108/C111–C113 fitted, C109/C110 DNP (decisions 57–60) |
| E5 HC2 outputs | closed | D103/D203 SMAJ33CA, OUT–GND at J11 (decision 43); invariant 4 reworded |
| E6 CAN barrier | closed | CA-IS3050G, C70 1 nF/2 kV DNP, FL1 CMC DNP with R71/R72 0 Ω (decisions 61–64) |
| E7 buck | closed | C19 100 nF/100 V, R43 0 Ω, R44/C20 snubber DNP, C1 100 V (decisions 47, 48) |
| E8 debounce | closed | C14–C17 470 nF (decision 54); README has the dry-contact and 12 V cranking notes |
| E9 4-ch outputs | closed | D103–D403 DNP footprints, invariant 4 reworded |
| E10 USB | closed | R13/C18 on USB_SHIELD, R14 0 Ω DNP, H5VL10B (decisions 45, 46) |
| E11 capacitor ratings | closed | C50–C53 now 1 nF/2 kV C9196 |
| E12 GND pole | open, with `/system mechanical` | decision 34 |
| E14 PTC I_max | open, one-way, with the owner | design-notes §8.3 (F1/F3/F4 I_max 40 A against ≈ 188 A prospective). Not repeated. |

## Findings

### Passes (re-checked in the current netlist)

- **Panel switch inputs.** SWIN → SMAJ30CA at J5 (D16–D19) → 4.7 k load → 10 k → node with 470 nF, 3.3 V zener and 4.7 k →
  BAT54C. RF path as in the first review; the 470 nF only improves it (about 1 Ω at 160 MHz for the capacitor itself).
- **LED sinks.** D50–D53 at J5 → R19/R22/R25/R28 100 Ω → C50–C53 1 nF/2 kV → collector. MMBT5551 V_CEO 160 V is above the
  clamp. No change.
- **N2K.** J4 → D9 PESD2CAN (CANH/CANL to GND_CAN) → FL1/R71/R72 → CA-IS3050G. NET-S: F3 → D10 SMAJ18CA → FB2 → D11 → L78M05.
  The TVS stays on the cable side of the CMC. Datasheet isolation rating 5 kV_RMS, bus ±58 V.
- **HC2 output clamp.** D103/D203 SMAJ33CA: VRWM 33 V is above the 28.8 V float-switch case, VC 53.3 V is below the
  80 V MOSFET and 100 V SS510B ratings (design-notes §8.2).
- **D30 against the parts behind it.** SMCJ30CA VC 48.4 V against BTT6050 VS(LD) 65 V, BSC030N08NS5 80 V, C31 63 V,
  C30/C104 100 V. No part is operated past its maximum by a plausible event that is not already declared system-level
  (decision 12).
- **Mounting holes** H1/H2 are on no net (invariant 6).

### CRITICAL

None.

### MAJOR

**E16 – system (shared root sheet; hc_channel on HC2): the VS bulk capacitors are polarised and unprotected against a
reversed battery, while the README says pdm-4ch survives reversal.**
- Parts: C31 100 µF/63 V (Ymin VKMD1001J101MV, C487384) on VS–GND on both boards; C106/C206, the same part, on VS of each
  HC2 channel. Netlist: `VS :: … C31.1 …`, `GND :: … C31.2 …` (C31.1 is the positive pad). D30 is a bidirectional
  SMCJ30CA, so it does not conduct below ≈ 33 V in either direction. Nothing sits between J10 and C31.
- Evidence: `README.md` line 47 and design-notes §8 (T-0050): the 4-ch switches survive a reversed supply of ≤ 28 V for
  < 2 min. That analysis covers the BTT6050 only. T-0064 added C31 on 2026-11-01, after the reverse-battery analysis was
  planned, and the analysis was not redone for it.
- Evidence: the Ymin datasheet (`docs/part-facts/C487384.md`, pp. 1–7 read in full) states no reverse-voltage rating and no
  reverse behaviour. `UNVERIFIED` for this part. General practice (not from this datasheet) is that liquid aluminium
  electrolytics tolerate about 1 V reverse at most. At 12–28 V reverse, leakage current rises sharply, the can heats and gas
  builds up; the Φ8 body has a safety vent. The current is limited only by the battery cable and the battery fuse.
- Failure mechanism for this product: a reversed battery is a classic installation error on boats (new boat, battery swap,
  tug with two banks). On pdm-4ch the user is told the board survives it, so the board is likely to be left powered for
  the 2 minutes. C31 is the first thing to fail. Outcome: venting electrolyte, heat and possibly a short on VS behind a
  fuse that may be sized for the loads, not for C31. That is a burn risk at a board that is installed in an enclosed box.
- Not the case on HC2: there the controllers are already destroyed by reversal (decision 40, README), and J10 is to be
  keyed. The capacitors add to the heat, but the README warning already says "do not".
- Fix (cheapest first):
  1. No part change. Withdraw the 4-ch reversal-survival claim from the README and design-notes §8 (or limit it to "the
     BTT6050 switches; C31 is not rated for reverse"), and key J10 on pdm-4ch the same way as on HC2 (decision 34,
     `/system mechanical`). The installer's battery fuse remains the protection.
  2. If survival is wanted: it needs a reverse-blocking element in front of the bulk capacitors (P-FET or ideal diode on
     VS). That adds a part to a 40–50 A path and is a decision for a later revision, as decision 40 already did for HC2.
     A bipolar or polymer capacitor does not remove the problem (polymer parts are polarised too).
- Why not a value change: no capacitor value helps, the issue is polarity.
- Door: one-way. Weakening a stated reverse-battery behaviour touches `safety`, and the keyed connector is a mechanical
  choice that the owner holds (decision 34 is confirmed). The owner decides whether the 4-ch board keeps its claim.

### MINOR

**E17 – system, README: the cable practice that the immunity design depends on is not in the README.**
- Evidence: README lines 30–64 cover fusing, dry contacts, 12 V cranking, reverse battery, HC2 breaker, USB service. They
  say nothing about the following, which the earlier review listed as README text and decision 28 (IEC 60945 as a design
  target) assumes:
  - the panel cable: one screened multicore, ≤ 10 m, drain at the PDM end only (J5.10), switch/LED/supply wires inside it;
  - battery + and − bundled, away from the VHF coax;
  - load return with its feed, back to the battery negative bus, not through the PDM ground;
  - a diode or TVS at inductive loads;
  - no PWM above 200 Hz on the 4-ch outputs; none on HC2;
  - N2K drop ≤ 6 m, shield not connected at the node.
- Mechanism: the filters at J5 and J11 are sized for these conditions (decision 17: LED sinks work to ≥ 10 m; the VHF
  attenuation figure assumes the screen is not carrying common-mode current into the board ground at the wrong end). A
  user who returns a motor load through the PDM ground sends freewheel current through the single J10 GND pole
  (E12), which the board is not rated for.
- Fix: add the "Installation guidance" section below to the README. Text only; no part, no cost.

## Layout rules (PCB phase)

The rules of the first review (1–13) stand. Changes and additions since the design moved:

1. **Protection at the connectors** (rule 1 unchanged). Add: D103/D203 (HC2) and the DNP D103–D403 (4-ch) next to the
   J11 terminals, return by a short wide path to J10.2, not through logic ground.
2. **Battery input.** C30 and D30 on the terminal copper (VBAT_IN) at J10. Then JP30 as a copper bridge as wide as the VS
   copper on both layers (it carries the whole load current). C31 right behind it. The loop J10 – C30 – C31 – first switch
   – D30 as small as possible. Keep C31 away from the heat of the switches (10 000 h at 105 °C assumes ≤ 65 °C in
   design-notes §8.1).
3. **HC2 controller pins** (design-notes §4a.1):
   - R114/R214 and C102/C202 at pin 20;
   - C108/C208 across pins 17/18 at the IC;
   - C111–C113 at their pins;
   - C107/C207 at the MMBT3904 with its emitter Kelvin to U11/U12 pin 6, not through the power ground;
   - the RSET (R102) and RISCP (R103) legs to the shunt as a Kelvin pair.
4. **Isolation barrier (changed).** The CA-IS3050G is a wide-body SOIC-8-WB. The datasheet gives CLR/CPG 8 mm (v1.10 §7.5,
   design-notes §8.5). Keep copper, vias and the GND/GND_CAN islands ≥ 8 mm apart across the body (the first review said
   4 mm for the narrow SOIC-8). No copper under the body between pins 1–4 and 5–8. C70 (DNP, 1206 pads) and FL1 are the
   only parts that bridge the gap. D9, D10, F3, FB2, D11, U6 and J4 on the GND_CAN side only.
5. **CMC FL1.** Check pad numbering against the JLCPCB footprint of C20624726 before it is fitted (design-notes §8.5): a
   swapped pair turns the choke into a differential element.
6. **Gate drive** (HC2): gate loops tiny and close to U11/U12; leave room for the gate-slew parts while Q-0049/Q-0050 are open.
7. **Creepage on the battery side**: ≥ 1.0 mm between VS/VBAT_IN and other nets on outer layers, conformal coating, copper
   edges ≥ 1 mm from the board edge. The 2 kV 1206 capacitors C50–C53 and C70 keep their pad spacing.
8. **Panel connector J5**: SW_SUPPLY and the returns together; D16–D19/D50–D54 first, then R, then C; D55 next to F4.
9. **Test points** as before (VS, 3V3, GND, buck SW, CANH/CANL).

All other earlier rules (ground plane without splits, buck hot loop, antenna keep-out, mounting holes) stand unchanged.

## Installation guidance (for the README)

- **Battery feed.** Fuse at the battery, sized to the wire. Run + and − as a twisted or tightly bundled pair, as short as
  possible, ≥ 0.5 m from the VHF antenna feed and the transmitter, crossing at 90°. **Check polarity before connecting**
  (E16): the bulk capacitors are polarised.
- **Alternator and load dump.** The PDM does not handle load dump (decision 12). Use an alternator protection device or a
  field-disconnecting battery switch. Never open the main battery switch while charging.
- **Loads.** Run each load's return with its feed (same cable, twisted) back to the battery negative bus. Never return load
  current through the PDM ground. Fuse each output wire.
- **Inductive loads** (solenoids, relays, horns, motors): a diode or TVS at the load.
- **PWM.** None above 200 Hz on pdm-4ch; none at all on pdm-hc2 until it is measured (decision 25).
- **Panel cable.** One screened multicore, ≤ 10 m, switch, LED and supply wires inside the same cable. Connect the drain only
  at the PDM end (J5.10). Dry contacts without a lamp across them. Do not share the cable with other loads.
- **NMEA 2000.** Drop cable ≤ 6 m, backbone grounded once at the power tap; the node has no shield pin, so do not connect the
  drain at the node. Keep the drop away from the VHF coax.
- **USB.** Service only, battery-powered laptop or isolator, unplug afterwards (already in the README).
- **Position.** Enclosed, vented box, as far from the VHF antenna and its coax as practical. The plastic box gives no
  shielding; the cables are the antenna, so cable practice matters more than box position.

## Not checked

- Anything on a PCB (none exists). All "layout" statements are rules, not checks.
- Reverse-voltage behaviour of C487384 (not in the datasheet; `UNVERIFIED`, E16).
- Capacitance and TLP data of SMAJ30CA, SMCJ30CA, SMAJ33CA, PESD2CAN (datasheets not read in this run); H5VL10B figures are
  taken from design-notes §8.3.
- Pad numbering of the FL1 footprint against JLCPCB (design-notes §8.5 already flags it).
- Whether the 0402 R114/R214 pulse rating is met by a 0.3 mJ hot-plug step (design-notes §4a.1 marks it `UNVERIFIED`).
- Actual emission, immunity and surge behaviour: nothing was measured; VHF numbers are field-strength estimates
  (E = √(30·P·G)/d). IEC 60945 and CISPR limits were recalled, not read.
- The F1/F3/F4 interrupt rating (open with the owner, design-notes §8.3).
- ESP32-S3 RF behaviour, Wi-Fi coexistence, ADC accuracy under RF.

<!-- findings:begin -->
```json
[
  {
    "id": "E16",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "system",
    "location": "root sheet: C31 100 uF/63 V on VS (C487384); hc_channel: C106/C206 (HC2); README reverse-battery bullet for pdm-4ch",
    "summary": "The VS bulk capacitors are polarised aluminium electrolytics with no reverse rating in their datasheet and nothing in front of them at J10, while the README says pdm-4ch survives a reversed battery of up to 28 V for 2 min; a reversed battery can overheat and vent C31.",
    "fix": "Withdraw or limit the 4-ch reversal claim in README and design-notes section 8 and key J10 on pdm-4ch like HC2 (decision 34, /system mechanical); a reverse-blocking element on VS only in a later revision.",
    "door": "one-way",
    "reason": "Policy item 3: weakens a stated safety behaviour (a part that can burn); the keyed connector is the owner's mechanical choice (decision 34).",
    "touches": ["safety", "connector", "mechanical"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E17",
    "kind": "finding",
    "severity": "MINOR",
    "board": "system",
    "location": "README.md: installation section",
    "summary": "The cable practice that the immunity design assumes (screened panel cable with drain at the PDM end, bundled battery pair away from VHF coax, load returns to the battery negative bus, diode at inductive loads, PWM limits, N2K drop length) is not in the README.",
    "fix": "Add the Installation guidance section of this report to the README; text only.",
    "door": "two-way",
    "reason": "Documentation, cheap to undo (policy: two-way, documentation); it adds no part and changes no decision.",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
