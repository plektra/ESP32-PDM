# Validation pdm-4ch, re-check after agent fixes (T-0074, 2026-11-03)

Scope: `git diff 5cee70e79c0e -- hardware lib docs/design-notes.md`, board pdm-4ch only (shared sheets also affect pdm-hc2).
Method: netlist of the base commit and of HEAD compared part by part and pin by pin (scratch), ERC, part facts, datasheet page
rendered, heat budget rerun.

## Findings

### CRITICAL

**C1. U5 CA-IS3050G: TXD and RXD swapped (pins 2 and 3).** `lib/ESP32-PDM.kicad_sym` symbol `CA-IS3050G`, sheet `can`
(shared, so also pdm-hc2), design-notes §8.5 "Pinout" row.
- Datasheet: Chipanalog CA-IS305x v1.10, p. 5, Fig. 6-1 (rendered) and Table 6-1: for SOIC8-WB, **pin 2 = RXD, pin 3 = TXD**
  (pin 6 = CANL, 7 = CANH, 1 VCC1, 4 GND1, 5 GND2, 8 VCC2 are right). It is the CA-IS3052G that has 2 = TXD, 3 = RXD (p. 6, Table 6-2).
- Symbol and netlist: U5.2 = "TXD" on /IO17 (ESP32 CAN TX, U1.21, with the new pull-up R70), U5.3 = "RXD" on /IO18 (U1.22). Design-notes
  §8.5 quotes "Table 6-1: 2 TXD, 3 RXD", which is the 3052G order.
- Failure mechanism: the ESP32 drives its TX pin into the transceiver's RXD output (push-pull contention, GPIO against the isolator
  output), and the transceiver TXD input (pin 3) is driven by ESP32 RX (an input) and left to its weak internal pull-up. The node
  never transmits and no frame is received; the output contention can also stress both pins at power-up. NMEA 2000 dead. Found on the
  first prototype at best.
- Fix: in the symbol swap the two pin numbers (TXD → 3, RXD → 2, positions unchanged, or swap names/types), re-run netlist; correct
  §8.5. Cost 0. Same fix serves pdm-hc2 (shared sheet).

### MAJOR
None.

### MINOR
None with a concrete mechanism beyond what the STATUS pre-order checklist already lists.

## Checked and OK

- ERC pdm-4ch: 0 errors, 5 `lib_symbol_mismatch` warnings (Q3–Q6 BC817, J3), as stated (`tools/sch_query.py pdm-4ch erc`).
- Net/part diff 5cee70e → HEAD: every changed ref is covered by a fix report (T-0064/65/66/67/68/69/73): LCSC codes, C1, C13, C14–C17, C50–C53, FB1/2,
  D4–D6, U3/U5/U6 and the new parts; no unexplained net change (only VBAT_IN/VS split, USB_SHIELD, CANH/L_BUS/_XCVR, SW_SUPPLY via D55, boot CB via R43).
- U3 LMR51610YDBVR on `SOT-23-6`: 1 CB, 2 GND, 3 FB, 4 EN, 5 VIN, 6 SW matches TI SLUSEY1B p. 3 Table 5-1; VIN abs max 70 V; EN tied to VIN allowed
  (part-facts C22427220). Netlist matches. Boot resistor R43 0 Ω in series with C2: correct.
- U5 supplies: VCC1 +3V3 (2.5–5.5 V), VCC2 from U6 5 V (4.5–5.5 V), CANH/CANL ±58 V, bus side from NET-S (CA-IS305x p. 7 §7.1/7.3). Pins 1, 4, 5, 6, 7, 8 correct.
- U6 L78M05ABDT: abs max VI 35 V (ST DS0425 rev 24 p. 5), fed from NET-S ≤ 16 V via F3/FB2/D11, clamped by D10 SMAJ18CA; C13 1 µF/50 V (C28323, basic); lead pads 1 = IN,
  3 = OUT, tab = GND match the `TO-252-2` footprint (pad 1 and 3 leads, 2 tab) and the datasheet orientation (Fig. 2 unnumbered, so pin numbers UNVERIFIED in the maker text; consistent with the usual DPAK order and the EasyEDA symbol).
  Dissipation at 0.5–0.9 W with 100 K/W: Tj ≤ 130 °C only at the 16 V / 73 mA corner, ≈ 95 °C typical; accepted.
- PG-TDSO-14 footprint paste (T-0066): 4 × 2.55 × 0.6 + 2 × 2.55 × 0.5 = 8.67 mm² of 16.96 mm² = 51 %; all windows ≥ 0.15 mm from via drills (vias at y 0, ±1.2, ±2.4, x ±0.6, drill 0.3), checked from the .kicad_mod.
- D12–D15 BAT54C C22466350: pins 1/2 anode, 3 common cathode (part-facts, datasheet p. 1), netlist wires 1 = IO6 side, 2 = SW, 3 = SW_IN; Vr 30 V, only ≤ 3.3 V across it.
- D55 DSK16 (C22466351, 60 V, K at J5 side) in series after F4: polarity blocks reverse battery to the panel LEDs; margin at SWIN 10.5 V is documented in design-notes §3 and has a prototype test (T-0042).
- C14–C17 470 nF: τ = 3.2 kΩ × 470 nF ≈ 1.5 ms as stated; C47339 on a 3.3 V node.
- R103–R403 680 Ω 1206 C17975 (0.25 W, 1 %), DNP pull-downs R106–R406 47 k C25819: value unchanged, sense scaling unchanged; heat budget `--p-other 2.2`: 4 A/ch Tj 101 °C at 40 °C, as stated.
- LCSC codes added in T-0073 checked by value/voltage/package: C28233 100 nF/100 V 0805, C15849 1 µF/50 V 0603, C52923 1 µF/25 V 0402 (on 5 V), C19666 4.7 µF/16 V 0603 (USB 5 V), C170101 2.2 µF/100 V 1206, C28323 1 µF/50 V 0805, H5VL10B C7420372 (5 V, bidirectional, DFN1006).
- Unique-part growth reported in the fix reports is consistent with the netlist (C23228 → C17975 swap, new C13832/C487384/C170101/C107198 extended).

## Not checked

- Datasheet pinouts of unchanged parts; HC2 channels; H5VL10B pinout beyond "bidirectional" (no pin issue); L78M05 pin numbers in ST text (figure unnumbered).
- KiCad footprints `D_SOD-882`, `TO-252-2`, `L_0805`, `SOIC-8_7.5x5.85`, `CP_Elec_8x10` against JLCPCB footprints (listed in STATUS pre-order checklist).
- JP30 as a 2 mm net-tie for 40 A (STATUS says the PCB bridge is drawn later); no PCB exists.
- The F1/F3/F4 PTC I_max question (open owner question already).

<!-- findings:begin -->
```json
[
  {
    "id": "V1",
    "kind": "finding",
    "severity": "CRITICAL",
    "board": "pdm-4ch",
    "location": "can sheet, U5 CA-IS3050G symbol (lib/ESP32-PDM.kicad_sym), design-notes §8.5",
    "summary": "U5 pins 2 and 3 are swapped: datasheet (CA-IS305x v1.10 p. 5 Fig. 6-1/Table 6-1) has pin 2 = RXD, pin 3 = TXD; symbol and netlist have 2 = TXD on IO17 and 3 = RXD on IO18, so ESP32 TX drives the isolator's RXD output and CAN cannot work.",
    "fix": "Swap the pin numbers of TXD and RXD in the ESP32-PDM:CA-IS3050G symbol (TXD = 3, RXD = 2), update symbols on both boards, re-run ERC and netlist, correct the Pinout row in design-notes §8.5.",
    "door": "two-way",
    "reason": "Symbol edit, one git commit, no PCB and no order yet; the orchestrator treats CRITICAL as one-way regardless.",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
