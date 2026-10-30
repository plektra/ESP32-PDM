# Validation – pdm-4ch, schematic phase

Date: 2026-10-30. Task T-0003, unattended. Reviewer: validator (independent of the design sessions). Scope: `hardware/pdm-4ch`
(root, `power-usb`, `can`, `analog_sw`, `channel` ×4) and the `lib/` parts it uses. No PCB exists.

Read first: `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/decisions.md`, `docs/AUTONOMY.md`, `docs/design-notes.md`,
`hardware/pdm-4ch/STATUS.md`, `docs/reviews/2026-10-30-emc-system.md`, `docs/reviews/2026-10-30-cost-system.md`. I do not
repeat the EMC findings E1–E15 or the cost findings C1–C5 (missing `LCSC` fields, capacitor voltage ratings, J10 bulk capacitance
and so on). Where a finding here touches one of them, I say so.

**Method.** I ran `kicad-cli sch erc` and `kicad-cli sch export netlist --format kicadxml` into scratch and restored
`ESP32-PDM-4CH.kicad_prl` afterwards. Every net and pin quoted below comes from that netlist. I downloaded the datasheets with
curl, extracted them with pypdf in a temporary venv, and rendered the package drawing to PNG with `sips`.

**Primary sources used**
- Infineon BTT6050-1ERA datasheet Rev 1.00, 2019-03-09 (Farnell copy, 53 pages). In this copy chapter 7 (pp. 23–32) carries
  the footer "Target Data Sheet Rev 0.11, 2017-05-18". The diagnostic numbers below come from those pages.
- TI ISO1044 SLLSFB0A (July 2020).
- TI TPS7B91 SBVS439A (May 2025).
- TI LMR51606/LMR51610 SLUSEY1B (Dec 2023).
- Espressif ESP32-S3-MINI-1/1U datasheet v1.7.
- Espressif ESP32-S3 Series datasheet v2.2.
- Diodes Inc. BZT52C DS18004 Rev 38-2.
- JLCPCB part data (jlc_get_part) for ratings of the LCSC-fitted parts.

The LCSC-hosted PDFs (MMBT5551 JCET, BAT54S/BZT52 hongjiacheng, PESD2CAN UMW) and the Nexperia/onsemi PDFs could not be
downloaded; the HTML was returned instead. The items that depend on them are marked `UNVERIFIED`.

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| MAJOR | 1 |
| MINOR | 9 |
| INFO | 2 (+ 1 question) |

ERC: 0 errors, 6 warnings. All six are `lib_symbol_mismatch` (Q3–Q6 BC817, J3, U3), as STATUS says. The netlist has no
unintended single-pin nets. Every unused ESP32 pin and every BTT6050 NC pin carries a no-connect flag.

The most important result: the current-sense resistor (R103/R203/R303/R403, 680 Ω, 0603, 0.1 W) is overloaded whenever a channel
reports a fault while DEN is high. That includes an output that is simply not connected (V1).

## Findings

### CRITICAL

None.

### MAJOR

**V1 – channel ×4: RIS (R103/R203/R303/R403, 680 Ω 0603 0.1 W) is overloaded by the IS fault current while DEN is high.**

- **Evidence: fault current.** BTT6050-1ERA Table 9, P_7.5.7, gives IIS(FAULT) = 6 / 15 / 40 mA (min / typ / max). The IS
  voltage is limited only by the sense saturation, VS − VIS(RANGE) = 1–3.5 V (P_7.5.6). Into 680 Ω that gives:
  - 6 mA: 4.1 V, 24 mW.
  - 15 mA (typical): 10.2 V, 0.15 W.
  - 40 mA (maximum): about 27 V at VS = 28–30 V, about 1.1 W.

  The resistor is C23228 (UNI-ROYAL 0603WAF6800T5E), rated 100 mW (JLCPCB data). The typical case is already 1.5 × its rating.
- **Evidence: when the fault current flows.** Table 8 (p. 24) lists the states that give IIS(FAULT) with DEN high:
  - The **channel is OFF and the output is above VS − VOL(OFF)** (open load in OFF, 4–6 V).
  - Short to VS.
  - Inverse current.
  - Current limitation.
  - The overtemperature latch. Per §7.3.5 this one persists until IN toggles.

  An output terminal with nothing connected, or a load switched off at the far end, floats up to VS through IL(OFF) because the
  only path to ground is C102 (10 nF). With DEN high, that IS line then carries IIS(FAULT) continuously.
- **Evidence: DEN is high most of the time.** design-notes §6 keeps DEN "on" in Active mode. DEN is common to all four channels
  (IO33 → R102/R202/R302/R402), so one floating output overloads its RIS for as long as the board is active.
- **Side effects.**
  - The BTT6050 dissipates an extra (VS − VIS) × IIS ≈ 0.27 W (typical) per faulted channel.
  - Each faulted channel injects about 2.4 mA into +3V3 through R104 and the BAT54S. That part is fine.
- **Fix (one or more):**
  1. Firmware: enable DEN only for the measurement window, or turn it off once a channel reads full scale. Infineon's own
     application multiplexes DEN.
  2. Fit RIS in a package rated for the typical fault case, 1206 at ≥ 0.25 W. Same value; no change to the sense scaling.
  3. Fit a defined pull-down at each OUT (RPD, datasheet §7.3.3.2) so that an unconnected output does not read as open load.

  Option 1 needs a firmware rule; it belongs in `/system firmware` together with decision 20.

### MINOR

**V2 – analog_sw → channel IN: the ON margin at 10.5 V with the 3.3 V rail down is smaller than design-notes §3 claims.**

- design-notes §3 says the switch path clears VIN(H) "with ~0.4 V margin". Worst case at SWIN = 10.5 V when the 3.3 V rail is
  down (the condition that invariant 1 exists for):
  - The node source is 10.5 × 4.7/14.7 = 3.36 V behind 3.2 kΩ.
  - R30 (10 k) loads it into the ESD diode of an unpowered IO14 at about 0.5 V, which brings the node to ≈ 2.67 V. The zener is
    below its knee there (IR ≤ 5 µA at 1 V, ZZK 600 Ω at 1 mA; DS18004).
  - The BAT54C drops ≈ 0.15–0.2 V.
  - R101 drops up to 0.25 V (IIN(H) up to 25 µA, P_8.4.5).
  - IN therefore sits at ≈ 2.2–2.3 V against board ground.
  - Once the channel is on, IGND_1 (4.8 typ / 9 mA max, P_4.2.5) through D101 (DSK16) and R105 (22 Ω) lifts the device ground
    by ≈ 0.35–0.5 V. IN relative to device GND is then ≈ 1.8–2.0 V, against VIN(H) min 2.0 V (P_8.4.2) and VIN(L) max 0.8 V.
- It probably works: switch-on happens before the ground shift, the hysteresis is about 250 mV, and the actual threshold lies
  between 0.8 and 2 V. It is not guaranteed by the datasheet, though.
- With the ESP32 powered, the margin is ≈ 0.2–0.3 V at 10.5 V. From 12 V upwards it is fine.
- The EMC report (E8) covers cranking dips; this finding is about the static margin.
- Fix: correct the margin statement in design-notes §3. Measure IN−GND on the prototype at SWIN = 10.5 V with 3V3 removed. If it
  is short, options include R101 → 4.7 k (the IIN drop halves) or the switch input divider on the shared sheet (owner).
- `UNVERIFIED`: the BZT52C3V3 knee below 1 mA (no curve for this maker).

**V3 – root: the VBAT_SENSE full scale is 31.9 V, not 33 V (decision 18, design-notes).**

- The ESP32-S3 ADC calibrated range is 0–2900 mV at ATTEN3 (ESP32-S3 datasheet v2.2, Table 5-6), not 3.0–3.1 V.
- 2.9 V × 242/22 = 31.9 V. The 30 V charging maximum still reads (2.73 V), and 48 V transients inject ≤ 0.2 mA through R60, so
  nothing is at risk.
- The same 2.9 V limit sets the current-sense full scale: BTT6050 ≈ 6.4 A, BTT6010 ≈ 16.6 A with 680 Ω. Both are fine.
- Fix: correct the figure in decision 18 / design-notes ("≈ 32 V full scale").

**V4 – lib `Infineon_PG-TDSO-14_ThermalVias`: the paste apertures sit over open thermal vias.**

- The six paste windows (1.0 × 1.6 mm at y = 0, ±2) cover the vias at y = 0, ±1.2 and ±2.4 (0.3 mm drill, not tented). Solder
  will wick into the vias: voids under the tab and solder balls on the bottom pad.
- Fix: one of:
  - move the paste windows between the vias;
  - specify plugged/capped vias (a JLCPCB option, extra cost);
  - accept it and check by X-ray on the first batch.
- The geometry itself is correct; see Checked and OK.

**V5 – lib `LMR51610`: the pad geometry differs from TI's DBV0006A land pattern.**

- The footprint has 1.81 × 0.61 mm pads centred at x = ±1.15, so their inner edges reach x = ±0.25, under the body.
- TI's land pattern example (SLUSEY1B p. 33) uses 1.1 × 0.6 mm pads at ±1.3 (2.6 mm span).
- The pin numbering is correct (1 CB, 2 GND, 3 FB, 4 EN, 5 VIN, 6 SW; Table 5-1). The geometry looks like a converted EasyEDA
  part: solderable, but the long inner pads raise the bridging and tombstoning risk, and the copper sits under the body.
- Fix: use KiCad's `Package_TO_SOT_SMD:SOT-23-6` or redraw to the TI pattern. Compare with JLCPCB's footprint before ordering.

**V6 – analog_sw: the switch-load resistors R3/R4/R7/R8 (4.7 k, 1206, C17936) run at 77 % of rating at 30 V.**

- At 30 V: 30²/4.7 k = 0.19 W against 0.25 W. At a 48 V clamp that becomes 0.49 W for the transient.
- The four together add ≈ 0.77 W inside the box when all switches are on (see V7).
- Usual derating practice is ≤ 50–60 % for continuous duty in a 50 °C enclosure.
- Fix: two 1206 resistors in series (2.2 k + 2.4 k ≈ 4.6 k) or a 2010 part. Same function. This is a shared-sheet change.

**V7 – heat budget input `--p-other 0.6 W` leaves out the panel interface.**

- At 30 V with all switches and LEDs on, the panel interface adds about 1.5 W:
  - switch loads 4 × 0.19 W;
  - series resistors and zeners 4 × 0.08 W;
  - LED sinks 4 × 0.13 W.

  With the buck/ESP32, roughly 2.1 W in total.
- Rerunning `tools/heat_budget.py --p-other 2.1` gives 4 A per channel → Tj 101 °C (was 100 °C). The rating stands.
- Fix: update the `--p-other` default or its help text and the design-notes §4 assumption (documentation).

**V8 – can: ISO1044 TXD (IO17) has no external pull-up.**

- ISO1044 §8.3.3.4: the internal pull-ups "should not be relied upon by design".
- ESP32-S3 Table 2-2: GPIO17 has a 60 µs low-level glitch at power-up. While the ESP32 is in reset, the pin is an input.
- The result can be one short dominant pulse on the NMEA 2000 bus at each power-up or reset. It is well below tTXD_DTO
  (1.2–3.8 ms), but it can cause an error frame on a live bus.
- Fix: 10 k pull-up from TXD to +3V3 (shared `can` sheet, both boards). The glitch itself cannot be removed; the pull-up only
  defines the reset state.

**V9 – analog_sw / reverse battery: panel LEDs are reverse-biased by about the full battery voltage.**

- With J10 reversed, SW_SUPPLY sits at about −VS (F4 is bidirectional, and D54 SMAJ30CA does not conduct below its 33 V
  breakdown).
- Each LED cathode is held near 0 V by R19 and Q3's collector–base junction (forward from R17). Each panel LED therefore sees
  ≈ 24–30 V reverse; typical LED VR(max) is 5 V.
- design-notes §8 accepts that loads see reverse voltage, but the panel LEDs are not mentioned and they are part of this product.
- Fix: document it in the README (reverse polarity can destroy panel LEDs), or add a series diode in the SW_SUPPLY feed. The
  diode is a shared-sheet protection change, for the owner.
- `UNVERIFIED`: whether the LED survives reverse breakdown at the few mA that the inverse-mode transistor allows.

**V10 – design-notes §8: the reverse-battery survival claim needs its datasheet conditions.**

- design-notes §8 says: "the switches survive with the ground network".
- The datasheet rating VS(REV) = 28 V (P_4.1.2) holds only for t < 2 min, RL ≥ 12 Ω (≤ 2.3 A at 28 V) and TA = 25 °C.
- At the full 4 A rating the body diode dissipates VDS(REV) 0.61 V × 4 A ≈ 2.4 W (P_6.6.2). That is above PTOT 1.6 W (P_4.1.22),
  and the ground diode does not change it.
- Fix: qualify the claim in design-notes/README, e.g. "survives a reverse connection of < 2 min with loads ≥ 12 Ω; heavier
  loads need the battery fuse to clear".

### INFO

**V11 – IO3 (strapping pin, JTAG source select) is tied low through IS2's network (R204 10 k + R203 680 Ω).**
- This is harmless while EFUSE_STRAP_JTAG_SEL stays unburnt (module datasheet v1.7 §4).
- Firmware/production must never burn that eFuse.
- No hardware change.

**V12 – Question: the default DEN policy.** Should DEN be held high in Active mode (design-notes §6), or pulsed only while the
firmware samples IS? V1 depends on the answer.

## Checked and OK

- **BTT6050-1ERA symbol pins.** Cooling tab = VS (pad 15); 1, 2, 7, 8, 9, 13, 14 NC; 3 GND; 4 IN; 5 DEN; 6 IS; 10–12 OUT, all
  three tied to OUTx. Source: datasheet Table 2, p. 4.
- **BTT6050 voltage ratings.** VS abs max 48 V (P_4.1.1), VS(LD) 65 V, VDS 65 V, VIS ≤ VS, IN/DEN 6 V (7 V < 2 min). They meet
  30 V continuous / 48 V transients. The SMCJ30CA clamp against 48 V is EMC E13 and was not repeated.
- **BTT6050 external network.**
  - RIN = RDEN = RSENSE = 10 k, as recommended (§6.4, p. 19).
  - ZGND = resistor in series with a diode, as recommended (§6.1 and §6.4). D101 is oriented anode → device GND, cathode → board
    GND, which blocks reverse current.
  - RIS 680 Ω > 560 Ω minimum (§7.3, p. 25). CSENSE 100 pF (≤ 100 pF in the timing tests). COUT 10 nF, CVS 100 nF/100 V.
- **IN power-up state.**
  - IN floats low by its internal current sink when both BAT54C anodes are low (IIN(L) 1–25 µA; §8.1 "left opened").
  - The drive pins IO6/IO7/IO8/IO11 have 2.2 k pull-downs (R5, R6, R1, R2).
  - The power-up glitches on GPIO6–11 are low-level only (ESP32-S3 datasheet Table 2-2), so no output pulses on at boot.
- **Diode orientation.**
  - BAT54C diode-OR: pins 1/2 are the anodes (IO, SW node), pin 3 the common cathode → R101. Standard BAT54C pinout.
  - BAT54S clamp: pin 1 to GND, pin 2 to +3V3, pin 3 to IO2–IO5. Standard BAT54S pinout.
  - Maker PDFs not retrieved for either part (`UNVERIFIED` against the hongjiacheng sheet).
- **Current-sense scaling.** IS = IL/kILIS: kILIS 1500 (±8 % at 4 A, P_7.5.12) × 680 Ω → 2.04 V at 4.5 A. BTT6010 kILIS 3900
  typical (Infineon BTT6010-1ERA product summary) → 1.39 V at 8 A. Both are inside the 0–2.9 V ADC range.
- **BTT6010-1ERA.** Same JLCPCB/EasyEDA footprint UUID as the BTT6050 (C534858 vs C534868), which supports the pin-compatibility
  claim. Its full datasheet was not read (see Not checked).
- **PG-TDSO-14 footprint geometry against Figure 53 (p. 49):**
  - 1.27 mm pitch;
  - lead tips at 6.0 ± 0.2 mm, so the 0.67 mm feet sit at x = 2.33–3.0; the pads at 1.8–3.4 give 0.53 mm heel and 0.4 mm toe;
  - exposed pad 2.65 × 6.4 mm matches;
  - pad-to-EP clearance 0.47 mm;
  - pin 1 is top-left, counting anticlockwise;
  - paste coverage ≈ 57 %.
- **ESP32-S3-MINI-1 pins.** Every pin in the netlist (1, 2, 42, 43, 46–65 GND; 3 3V3; 4–25 IO0–IO21; 26 IO26 NC; 28 IO33; 34–37
  IO38–IO41; 45 EN) matches module datasheet v1.7, Table 3-1. IO26 is free on N8 (PSRAM only on N4R2). IO1–IO10 are ADC1
  (invariant 10). IO6–IO8 and IO11 are RTC GPIOs.
- **Strapping.**
  - IO0: 10 k pull-up + BOOT button.
  - IO45/IO46: NC, internal pull-downs, which is the default boot.
  - EN: 10 k / 1.1 µF RC.
  - Source: module datasheet Table 4-1.
- **LMR51610.**
  - Pins match Table 5-1. VIN abs max 70 V. EN tied to VIN is allowed.
  - VFB 0.8 V ± 1.5 %, so R9/R10 = 68 k/22 k → 3.27 V.
  - L1 = 8.2 µH and COUT ≥ 10 µF match Table 8-1 for 1.1 MHz / 3.3 V (C8 22 µF + C3 2.2 µF).
  - The UVLO of 3.82 V (rising) allows USB-only operation (VBUS − D3 ≈ 4.6 V).
  - tON(min) 80 ns: pulse-skipping above ≈ 37 V, which is harmless.
- **TPS7B91050DBVR.** Pins 1 IN, 2 GND, 3/4 NC (no EN pin, so leaving them open is correct), 5 OUT (SBVS439A Table 4-1). VIN abs
  max 42 V, above the SMAJ18CA clamp. COUT 1 µF nominal meets the ≥ 1 µF requirement (§5.3, with 50 % derating assumed by TI).
- **ISO1044BD.** Pins 1 VCC1, 2 TXD, 3 RXD, 4 GND1, 5 CANL, 6 CANH, 7 GND2, 8 VCC2 match SLLSFB0A Figure 5-1 and the netlist.
  VCC1 runs at 3.3 V and VCC2 at 5 V, both within range.
- **LED sinks.**
  - V_B = 3.0 V → I_LED ≈ 4.9 mA.
  - MMBT5551 (C2145, JCET) VCEO 160 V, Pd 300 mW (JLCPCB data). Dissipation 0.13 W at 30 V.
  - R17 pull-downs keep the LEDs off at boot.
  - SOT-23 1 B / 2 E / 3 C as wired; `UNVERIFIED` against the JCET PDF (not retrievable), but it is the standard MMBT5551 pinout.
- **Switch input at 30 V.**
  - R34 1206: 71 mW.
  - Zener ≈ 2 mA, 7 mW.
  - Current into the ESP32 through R30 ≤ 0.3 mA when the ESP32 is unpowered.
  - IN never exceeds 3.5 V (abs max 6 V).
- **Other analog inputs.**
  - MOD_ID: R29/R42 10 k/10 k → 1.65 V, as in decision 14.
  - NTC: R62 10 k + TH1 → 1.65 V at 25 °C; inside 2.9 V down to about −15 °C.
- **Heat budget, rerun at 40 °C (`tools/heat_budget.py`).**

  | Case | Result | Matches |
  |---|---|---|
  | 4 × BTT6050, 4 A | Tj 100 °C | ARCHITECTURE budget |
  | Mixed 2 × BTT6010 at 8 A + 2 × BTT6050 at 4 A | Tj 88 / 101 °C | ARCHITECTURE budget |
  | 1 module width, 1 oz (`--r-box 0.9 --rth-ja 50`), 3.5 A | Tj 98 °C | provisional 3.5 A rating |

  The tool's RDS(on) inputs (60 mΩ at 25 °C, 105 mΩ at 150 °C) are more pessimistic than the datasheet (50 typ, 100 max at
  150 °C; P_5.5.1/P_5.5.21), so they are conservative.
- **Supply wiring.**
  - VS feeds U11–U14 pin 15 and the buck via F1 → D2.
  - USB VBUS joins through F2 → FB1 → D3, so VS cannot back-feed VBUS.
  - CC1/CC2 have 5.1 k to GND each.
- **Invariants.**
  - 1: hardware switch path, with the margin caveat in V2.
  - 2: no relays.
  - 6: H1/H2 on no net.
  - 9: no +3V3 on J5. J5 carries only SWIN, SW_SUPPLY, LED_K and GND.
  - 10: all analog inputs on ADC1.
- **Decisions.**
  - 17: J5 pin-out 1–4 SWIN, 5 SW_SUPPLY, 6–9 LED_K, 10 GND; every line has a SMAJ30CA.
  - 18: IO9 NTC, IO10 VBAT, IO11 ch4, LEDs IO38–IO41.

## Not checked

- Maker datasheets for MMBT5551 (JCET), BAT54C/BAT54S/BZT52C3V3 (hongjiacheng), PESD2CAN (UMW, the "pin 3 = common" item in
  STATUS), SMAJ30CA/SMCJ30CA, PESD0402V05, DSK16 and the 1812L050/60GR PTC: the downloads failed (LCSC and Nexperia returned HTML).
  The USB VBUS ESD diode D4 (5 V stand-off on a 5.25 V rail) is therefore also unverified.
- The full BTT6010-1ERA datasheet (only the product-summary kILIS of 3900 was confirmed). Its IIS(FAULT) and VIS range, which
  matter for V1, are assumed to be similar.
- The ESP32-S3-MINI-1 footprint (`RF_Module:ESP32-S2-MINI-1`): KiCad's footprint references the S3-MINI-1 datasheet and has the
  same 15.4 × 20.5 mm body, but I did not compare its land pattern against Figure 11-1 pad by pad.
- The USB-C connector J3 (HRO TYPE-C-31-M-12 footprint vs the USB4145 symbol, which is a mismatched library symbol) and the
  Kangnex WJ15EDGVC on the Phoenix MCV footprint: STATUS items, no drawing read.
- J10, J11 and H1/H2 have no footprint yet, and J5 is a 2.54 mm header. Pending `/system mechanical`.
- The `pdm-hc2` board and the copies of the shared sheets in it.
- Anything on a PCB, and any measurement.

<!-- findings:begin -->
```json
[
  {
    "id": "V1",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-4ch",
    "location": "channel x4: R103/R203/R303/R403 (RIS 680 ohm 0603), DEN on IO33",
    "summary": "IS fault current (6/15/40 mA, P_7.5.7) into 680 ohm dissipates 0.15 W typ / ~1.1 W max in a 0.1 W 0603 whenever DEN is high and a channel is faulted, including an unconnected output floating up in OFF (open-load-in-OFF).",
    "fix": "Firmware enables DEN only for sampling or drops it on a full-scale IS; fit RIS as 1206 >= 0.25 W; optionally an OUT pull-down so open outputs do not flag a fault.",
    "class": "big",
    "reason": "The complete fix needs a firmware DEN policy (firmware architecture is big); the resistor package change alone would be small.",
    "touches": ["firmware"],
    "cost_delta_usd": 0.01
  },
  {
    "id": "V2",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "analog_sw SW1-4 node -> D12-D15 -> R101/R201/R301/R401 -> IN; design-notes section 3",
    "summary": "At SWIN 10.5 V with the 3.3 V rail down, IN minus device GND is about 1.8-2.0 V once ON, against VIN(H) min 2.0 V; the claimed 0.4 V margin does not hold (UNVERIFIED zener knee).",
    "fix": "Correct the margin claim and measure on the prototype; if short, consider RIN 4.7 k or a divider change on the shared sheet.",
    "class": "big",
    "reason": "Any circuit fix touches the shared analog_sw sheet and invariant 1 (hardware switch path).",
    "touches": ["shared-sheet", "invariant"]
  },
  {
    "id": "V3",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "root: R60/R61 VBAT_SENSE; decision 18 text",
    "summary": "ESP32-S3 ADC calibrated range is 0-2900 mV (datasheet v2.2 Table 5-6), so VBAT full scale is 31.9 V, not 33 V; 30 V still reads.",
    "fix": "Correct the figure in decision 18 and design-notes to about 32 V full scale.",
    "class": "big",
    "reason": "Documentation only, but the text is part of confirmed decision 18.",
    "touches": ["decision:18"]
  },
  {
    "id": "V4",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "lib/ESP32-PDM.pretty/Infineon_PG-TDSO-14_ThermalVias: paste windows vs thermal vias",
    "summary": "Paste apertures overlap the open 0.3 mm thermal vias, so solder wicks into the vias (voids under the VS tab).",
    "fix": "Move the paste windows between the vias, or order plugged/capped vias.",
    "class": "big",
    "reason": "Footprint correction, but it is in lib/, which the small policy excludes.",
    "touches": []
  },
  {
    "id": "V5",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "lib/ESP32-PDM.pretty/LMR51610 (U3)",
    "summary": "Pads are 1.81 x 0.61 mm at x = +/-1.15 (inner edges under the body) instead of TI DBV0006A 1.1 x 0.6 mm at +/-1.3; numbering is correct.",
    "fix": "Use Package_TO_SOT_SMD:SOT-23-6 or redraw to the TI land pattern; compare with the JLCPCB footprint.",
    "class": "big",
    "reason": "Footprint correction proven by the datasheet, but in lib/ (excluded from small).",
    "touches": []
  },
  {
    "id": "V6",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "analog_sw: R3/R4/R7/R8 4.7 k 1206 switch loads",
    "summary": "0.19 W continuous at 30 V in a 0.25 W part (77 %), 0.49 W during a 48 V clamp.",
    "fix": "Two 1206 resistors in series (2.2 k + 2.4 k) or a 2010 part, same value.",
    "class": "big",
    "reason": "Passive-only change, but on the shared analog_sw sheet.",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.02
  },
  {
    "id": "V7",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "tools/heat_budget.py --p-other default; design-notes section 4",
    "summary": "p_other 0.6 W omits about 1.5 W of panel-interface dissipation at 30 V (switch loads, dividers, LED sinks); Tj rises from 100 to 101 C at 4 A, so the rating stands.",
    "fix": "Raise the default or document about 2.1 W for the 4-ch board at 30 V with all panel lines on.",
    "class": "small",
    "reason": "Documentation and tool input only; no rating, decision or circuit change.",
    "touches": []
  },
  {
    "id": "V8",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "can: U5 TXD (IO17)",
    "summary": "No external pull-up on ISO1044 TXD; TI says not to rely on the internal one, and GPIO17 has a 60 us low glitch at power-up, which can put a dominant pulse on the N2K bus.",
    "fix": "10 k pull-up from TXD to +3V3 on the shared can sheet (both boards).",
    "class": "big",
    "reason": "A missing pull-up is small in kind, but the can sheet is shared.",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "V9",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "analog_sw: SW_SUPPLY/F4, LED_K1-4, Q3-Q6",
    "summary": "With reversed battery, the panel LEDs see about 24-30 V reverse (cathode held near 0 V by R19 and the Q collector-base junction); typical LED VR is 5 V.",
    "fix": "Document in the README, or add a series diode in the SW_SUPPLY feed (owner).",
    "class": "big",
    "reason": "A hardware fix changes protection on the shared sheet.",
    "touches": ["shared-sheet", "protection"]
  },
  {
    "id": "V10",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "design-notes section 8 (reverse battery)",
    "summary": "'Switches survive with the ground network' holds only for VS(REV) 28 V, t < 2 min, RL >= 12 ohm (P_4.1.2); at 4 A the body diode dissipates about 2.4 W > PTOT 1.6 W.",
    "fix": "Qualify the claim in design-notes/README with the datasheet conditions.",
    "class": "small",
    "reason": "Documentation only.",
    "touches": []
  },
  {
    "id": "V11",
    "kind": "finding",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "root: IO3 (strapping) on IS2 network R204/R203",
    "summary": "IO3 (JTAG source strap) is tied low through 10.7 k; harmless unless EFUSE_STRAP_JTAG_SEL is burnt.",
    "fix": "Note in the firmware/production docs: never burn EFUSE_STRAP_JTAG_SEL.",
    "class": "small",
    "reason": "Documentation only.",
    "touches": []
  },
  {
    "id": "V12",
    "kind": "question",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "DEN (IO33), design-notes section 6",
    "summary": "Should DEN be held high in Active mode, or pulsed only while sampling IS? V1 (RIS overload on fault or open output) depends on it.",
    "fix": "Owner decides the DEN policy in /system firmware.",
    "class": "big",
    "reason": "Firmware architecture question for the owner.",
    "touches": ["firmware"]
  }
]
```
<!-- findings:end -->
