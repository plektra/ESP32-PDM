# EMC review – system (pdm-4ch and pdm-hc2), schematic phase

Date: 2026-10-30. Task T-0001, unattended. Reviewer: emc-reviewer. No PCB exists, so there is no `layout` check.

Sources read: `CLAUDE.md`, `docs/ARCHITECTURE.md` (invariant 4), `docs/decisions.md`, `docs/design-notes.md` (§5),
`docs/AUTONOMY.md`, both STATUS files. There were no earlier EMC reports. Netlists were exported with
`kicad-cli sch export netlist --format kicadxml` into scratch (`$CLAUDE_JOB_DIR/tmp`); every net below comes from them.

Datasheets read:
- Infineon BTT6050-1ERA Rev 1.00 (excerpt), and BTT6050-2ERA Rev 1.00 for the family tables.
- TI TPS4811-Q1 SLUSEE5E.
- TI ISO1044 SLLSFB0A.
- TI LMR51610.
- JLCPCB parametric data for the TVS and ESD parts.

The LCSC-hosted datasheets of the SMAJ30CA, SMCJ30CA, PESD0402V05, PESD2CAN and BLM18AG601SN1D could not be downloaded.
Their capacitance and dynamic clamp figures are `UNVERIFIED`.

Standards are used only as a guide: IEC 60945 (marine), IEC 61000-4-2/-4-4/-4-5 and ISO 7637. Levels are quoted from memory.

## Summary

The inputs are well done:
- The panel switch inputs have a very good RF path.
- The LED sinks are fine.
- The N2K supply and bus lines are well clamped.

The gaps are mostly on the power side:

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| MAJOR | 7 |
| MINOR | 5 |
| INFO | 1 finding, 2 questions |

What I found that matters most:
1. `pdm-hc2` turns its MOSFETs on and off at a gate speed that is not slew-limited (E2). A PROFET switches at 0.3–1.4 V/µs.
   Expect switching clicks in the VHF radio and a harder-to-pass emission test.
2. There is no bulk or HF capacitance at the battery input J10 on either board (E3).
3. The HC2 sense, UVLO/OV and VS pins have none of the filtering that TI lists for EMI/EMC (E1, E4).
4. HC2 outputs have no clamp at J11 apart from the freewheel diode, which clamps only negative voltage (E5).
5. The isolated CAN side has no high-frequency return across the barrier (E6).
6. The buck sits in the 156–165 MHz band that IEC 60945 limits tightly (E7).

## Findings

### Passes (checked, no finding)

- **Panel switch input RF path (`analog_sw`, R34–R37 and C14–C17).**
  - Source impedance at the node is 10 k ‖ 4.7 k, which gives τ = 0.32 ms (corner ≈ 500 Hz).
  - A 100 nF 0402 is inductive above its self-resonance (≈ 15 MHz). Its impedance at 160 MHz is about 1 Ω.
  - A 1206 body capacitance of about 0.3 pF (`UNVERIFIED`, typical) bypasses the 10 k with roughly 3 kΩ at 160 MHz.
  - Attenuation at VHF is therefore about −70 dB. A 10 V RF pickup on a resonant cable leaves a few mV at the node.
  - The Schottky BAT54C and the ESP32 input see only that.
- **LED sinks (Q3–Q6).**
  - The TVS is at the connector. R19 (100 Ω) and C50 (1 nF) form a divider of about 100:1 at 160 MHz ahead of the transistor.
  - Collector–base capacitance (a few pF) cannot rectify a significant RF level.
  - The 5 mA current is set by the base divider. LED PWM at 100–200 Hz with a 1 nF collector capacitor is quiet.
- **Switch ON threshold margin.**
  - At SWIN = 10.5 V the node is about 3.1–3.3 V.
  - After the BAT54C drop (≈ 0.2 V) and the ground shift (≈ 0.3 V), the IN level is about 2.6–2.8 V against VIN(H) ≤ 2 V.
  - This is `UNVERIFIED` without a measurement, but the margin is ≥ 0.4 V as in design-notes §3.
- **N2K lines.**
  - PESD2CAN (25 pF, Vrwm 24 V, Vc 41 V at 6 A) is far below the ISO1044 bus rating of ±58 V.
  - ISO1044 passes 8 kV contact ESD on its own (datasheet §9.2). The 25 pF per line is irrelevant at 250 kbit/s.
  - NET-S: F3 → SMAJ18CA (Vc 29.2 V, typical) → FB2 (600 Ω at 100 MHz) → D11 → TPS7B91. Good RF and surge chain.
- **Output edges, 4-ch.** BTT6050 slew is 0.3 / 0.8 / 1.4 V/µs (min / typ / max, P_5.5.11). 10–90 % takes about 28 µs and
  the spectrum corner is about 12 kHz. Together with 10 nF at the output there is no VHF content, and PWM at ≤ 200 Hz is fine.
- **Mounting holes** (H1, H2) are not on any net, which agrees with invariant 6.
- **Current paths of the clamps.**
  - Every TVS on the battery side returns to the `GND` net, and `GND` is tied to J10.2 only.
  - The load returns do not pass through the PDM (they go to the battery negative bus), so board ground carries logic
    current, TVS surge current and, on HC2, motor freewheel current.
  - The CAN TVS returns to `GND_CAN`.

### CRITICAL

None. No part is operated beyond its absolute maximum by a plausible event that is not already declared system-level
(decision 12). See E13 for the closest case.

### MAJOR

**E1 – pdm-hc2, U11/U12 VS pin: no RVS/CVS (hc_channel).**
- Problem: pin 20 of both controllers is wired straight to the `VS` net with 100 nF (C102/C202) next to it.
- Evidence: TPS4811-Q1 Table 9-3 recommends RVS 100 Ω + CVS 0.1–10 µF, and says the VS pin "must be maintained above
  V(VS_PORR) during noisy line transients".
- Evidence: Absolute-maximum table: "voltage slew rate on drain side input pins (VS, CS+, CS−, ISCP) 60 V/µs".
- Evidence: A fast short-circuit trip (80 A) into 1–5 µH of battery cable, or a hot-plug, can exceed 60 V/µs at the pin
  before the TVS and 100 nF act. Not measurable now (`UNVERIFIED`).
- Fix: add RVS = 100 Ω and CVS = 1 µF/100 V in the VS supply of each controller. Check IVS in the datasheet so the
  drop in RVS stays under about 0.3 V.

**E2 – pdm-hc2, gate drive speed (RG = 10 Ω in the PU path, PD direct).**
- Problem: the MOSFET turn-on and turn-off are not slew-limited. The PROFET channels of the 4-ch board switch at
  ≈ 0.8 V/µs; HC2 does not.
- Evidence: PU can source 3.7 A and PD can sink 4 A. With 12 V BST–SRC and about 5 V at the Miller plateau, the gate
  current is ≈ 0.7 A through 10 Ω.
- Evidence: Miller charge of 2 × BSC030N08NS5 is assumed at 2 × 10–20 nC (`UNVERIFIED`; I did not check the MOSFET
  datasheet). That gives a transition of about 30–60 ns for 24 V, so roughly 400–800 V/µs. Turn-off through PD is faster.
- Evidence: Pulsed into an unfiltered load cable of several metres (no output capacitor on HC2), this excites cable
  resonances in the VHF band. Expect clicks in the VHF receiver and AIS/NMEA each time a channel switches, and
  emission-test failures if a channel is ever PWM-dimmed.
- Fix: TI §8.3.2.1 and Table 9-3 allow RGATE_PU / RGATE_PD, or R1/C1 slew control with PD direct (the PD-direct path
  keeps fast protection turn-off). Fit RG_PU ≈ 100–220 Ω as a starting point, add a series RGATE_PD footprint (0 Ω to
  ≈ 22 Ω), and tune on the bench. Check MOSFET switching loss and the fast short-circuit response afterwards (heat budget).
  Until then, no PWM on HC2 outputs.

**E3 – system, J10 battery input: only an SMCJ30CA, no bulk or HF capacitance (root sheet).**
- Evidence: the `VS` net carries 100 nF per channel (4-ch), one 100 nF (HC2) and 2.2 µF at the buck behind F1 and D2.
- Problem: the Infineon short-circuit specification VBAT(SC) 36 V assumes ECU 20 mΩ and cable 16 mΩ/m, 1 µH/m with
  l = 0 or 5 m, i.e. a cable that has a large reservoir behind it. The HC2 80 A trip opens 80 A into the cable
  inductance. Without local energy storage the VS node takes the whole L·di/dt through the TVS, and the clamp voltage
  rises with current.
- Problem: a switched-current step of 4–25 A per channel also goes straight onto the battery cable (conducted emission).
- Problem: there is no filter or HF return, so every RF component on the cable reaches the board rails.
- Fix: at J10, fit an aluminium-polymer or electrolytic capacitor of about 100 µF/50 V (HC2: more) plus 1–2.2 µF/100 V
  ceramic, both directly at the terminals. On 4-ch also a 1 µF/100 V ceramic close to each BTT6050 VS tab.
- Fix: leave a footprint for a series ferrite or common-mode choke, decided at pre-compliance.
- Cost: bulk capacitor ≈ 0.20–0.30 USD per board; check whether a basic electrolytic exists before adding an extended part.

**E4 – pdm-hc2, sense and threshold pins have no EMI filtering (hc_channel).**
- Problem: the following pins have no filtering of their own:
  - CS+ / CS−: RSET 100 Ω from VS to CS+, with CS− on the drain side of the shunt. The full-scale signal is 25 mV at 25 A.
  - EN/UVLO (node impedance ≈ 120 kΩ).
  - OVSET (≈ 100 kΩ).
  - DIODE (the MMBT3904 remote sensor, µA signals).
  - IWRN, IMON (IMON has 1 nF).
- Evidence: TI §9.4 and Table 9-3: "X and Y capacitors are most effective" for CS+/CS−; ferrite beads and 10 pF–100 nF
  on the other pins "for better immunity during EMI/EMC testing".
- Evidence: 25 W VHF at 1 m gives ≈ 35 V/m (E = √(30·P·G)/d, G = 1.6), and 100 V/m at 0.3 m. The IEC 60945 test level
  of 10 V/m is therefore not an upper bound. RF rectified in a sense amplifier input appears as an offset of a few mV.
  Against the 25 mV breaker threshold and the 80 mV short-circuit threshold, that is a trip or IMON error under
  transmission, on a safety-relevant output (bilge pump).
- Fix: footprints (tune in test):
  - CS+/CS− X capacitor ≈ 1 nF, plus Y capacitors (≈ 100 pF) on each pin to SRC/GND.
  - 10 nF on EN/UVLO and on OVSET.
  - 1 nF on DIODE.
  - 100 pF on IWRN.
- Fix: layout rule 6 gives the Kelvin and routing part.

**E5 – pdm-hc2, J11 outputs: no surge or ESD clamp (hc_channel, OUT1/OUT2).**
- Problem: invariant 4 says every external line is protected at the connector. OUT has only the freewheel diode
  (SS510B), which clamps negative voltages, and the MOSFET itself.
- Problem: with back-to-back MOSFETs a positive surge on OUT is **not** diverted to VS (the blocking body diode points
  the wrong way), so D30 at J10 never sees it. The first limit is the 80 V avalanche of Q12.
- Evidence: the 4-ch PROFET has the body diode to VS and an HBM 4 kV rating on OUT (datasheet P_4.1.32).
- Evidence: the 8/20 µs and burst energy that a long load cable can couple (IEC 61000-4-4/-5) reaches Q12's drain and
  its Cds.
- Fix: a SMAJ30CA (already on the BOM, no new extended part) from each OUT to GND at J11. Check the stand-off against the
  float-switch case: a pump fed through a float switch from a 28.8 V charging system sits at the TVS stand-off of 30 V.
- Fix: put the TVS next to the terminal and take its ground return straight to J10.2.
- Note: this does not replace system-level load-dump protection (decision 12).

**E6 – system, `can` sheet: no high-frequency return across the isolation barrier, no CMC option.**
- Problem: GND_CAN is an isolated island. The only connection to GND is the barrier (CIO ≈ 1 pF, ISO1044 datasheet).
  Common-mode noise from the logic side (buck, ESP32) and the island's stray capacitance push CM current onto the N2K
  cable, which is the best antenna on the board.
- Problem: in the other direction, ESD or EFT clamped by D9/D10 to GND_CAN lifts the whole island relative to GND until
  it leaks through the barrier. The barrier is rated 3 kV_RMS / 5 kV_peak surge (SOIC-8) and ESD ±12 kV (bus to GND1),
  so it survives, but only if there is no copper bridge.
- Problem: there is no CMC option. TI notes that a CMC needs a TVS to still pass 8 kV (§9.2), and the TVS is there.
- Evidence: the antenna effect is `UNVERIFIED` until a pre-compliance scan; it is the usual failure mode of isolated CAN nodes.
- Fix: a footprint for a Y-class capacitor (1–2.2 nF, ≥ 1 kV, 1206) from GND_CAN to GND and a 4-pin footprint for a CMC
  (e.g. ACT45B-class, fitted or DNP) in series with CANH/CANL. Layout rule 9 keeps the barrier clear otherwise.
- Question E15 asks for the shield strategy.

**E7 – system, `power-usb` sheet: buck EMI in the marine VHF band, light-load PFM and CIN.**
- Problem: LMR51610**Y**DBVR is the 1100 kHz PFM variant (datasheet ordering table). At light load (ESP32 idle, sleep
  mode) it drops into PFM, so the switching frequency falls into 150–350 kHz. IEC 60945 limits that band tightly
  (conducted) and the Wi-Fi/DC bus is shared.
- Problem: the datasheet recommends "2.2 µF or higher" **and** a separate 0.1 µF "as close as possible to the device
  pins", and a rating of twice the maximum input voltage (§8.2.2.6). The schematic has only C1 = 2.2 µF/50 V (0805,
  roughly half the capacitance at 24 V bias) and no 0.1 µF at VIN.
- Problem: IEC 60945 limits radiated emission in 156–165 MHz far lower than elsewhere (about 30 dB). The 142nd–150th
  harmonic of 1.1 MHz and the SW node ringing of a SOT-23-6 buck fall in or near that band. `UNVERIFIED` without a
  scan, but it is the usual way a small buck fails.
- Fix: add a 100 nF/100 V directly at VIN–GND. Leave footprints for an RC snubber at SW and for a 0–10 Ω in series with
  the boot capacitor (C2). Layout rule 5 sets the hot loop.
- Fix: consider the LMR51610**YF** (fixed-PWM variant) if PFM noise shows in the scan; it is a different part number
  (cost and extended-part check needed, see lever L1).

### MINOR

**E8 – system, `analog_sw`: switch path has no debounce; ON threshold ≈ 8 V; lit switches.**
- Problem: τ = 0.32 ms, so contact bounce of ms length makes the output chatter, which gives repeated flyback on
  inductive loads. The MCU copy is debounced in firmware, but the hardware path is raw.
- Problem: the ON threshold at the switch is ≈ 2.55 V × 14.7/4.7 ≈ 8 V (calculation, `UNVERIFIED` against a
  measurement). In a 12 V system the battery sags to 6–9 V while cranking, so panel-switched outputs (navigation lights)
  drop out at that moment, although the PROFET works down to 5 V. 24 V systems are not affected.
- Problem: a switch with a lamp or LED across its contacts leaks. About 1.4 mA across the 3.6 kΩ source impedance
  reaches the threshold. The 4.7 kΩ bleeder (R3–R8) tolerates less than that.
- Fix: C14–C17 to 470 nF–1 µF (τ ≈ 1.5–3 ms) is enough to remove most bounce. Document in the README: use dry contacts
  without a parallel lamp, and note the cranking behaviour for 12 V boats.

**E9 – pdm-4ch, outputs J11: protection relies on the PROFET and D30.**
- Evidence: OUT has only 10 nF (C102, C202, C302, C402). Positive surges go through the PROFET body diode to VS and are
  clamped by D30. Negative surges are clamped by the device at VS − VDS(AZ) (65–75 V). HBM 4 kV on OUT.
- Problem: this is a deliberate design that satisfies the intent of invariant 4 but not the wording, and it makes D30 and
  the VS copper the path for output surges (D30 is at J10, the outputs at J11).
- Fix: write the OUT protection rule into `docs/ARCHITECTURE.md` invariant 4, and leave a DNP footprint for a SMAJ30CA per
  output. Layout rules 1 and 2 keep the path short.

**E10 – system, USB: shield to GND, and the ESD diode clamp figure.**
- Problem: J3.SH is tied to `GND` (battery negative). A laptop on shore power connects the boat's DC negative to
  shore PE through the USB cable (ground loop, galvanic path). The port is for service.
- Problem: PESD0402V05 is listed with a clamp of 40 V (JLCPCB data; test condition unknown). The ESP32-S3 pins are
  rated about 3.6 V. If 40 V is the clamp at the 8 kV contact level, the IC would be the weak link. `UNVERIFIED`:
  get the TLP/dynamic data of the DOWO part.
- Fix: README: "service only, unplug afterwards, use a battery-powered laptop or a USB isolator". Check the TLP data
  before ordering. Consider an RC (1 MΩ ‖ 4.7 nF) from shield to GND (a design change; owner decision).

**E11 – system, `analog_sw`, `power-usb`: capacitor voltage ratings against the clamp.**
- Problem: SMAJ30CA clamps at 48.4 V at 8.3 A (JLCPCB data) and more at higher current. C50–C53 (1 nF, C1523) are
  on the collector after R19. C1 (2.2 µF/50 V) is on the buck input.
- Evidence: the voltage rating of C1523 is not in the schematic (`UNVERIFIED`; commonly 50 V). TI recommends twice the maximum
  VIN for the input capacitor (§8.2.2.6).
- Fix: use ≥ 100 V parts for C50–C53 if the 1 nF 0402 is available at 100 V (check JLCPCB basic stock), and a 100 V
  (or 63 V) part for C1.

**E12 – system, J10 GND pole: current rating of the single ground terminal.**
- Problem: board GND is connected to the battery negative through one terminal pole. On HC2 it carries motor
  freewheel current (up to 25 A per channel for tens of ms) and TVS surge current. A 3.81 mm terminal is typically
  rated about 8–12 A (`UNVERIFIED`).
- Fix: `/system mechanical` should size the GND pole, or give two poles, in line with the VS input.

### INFO

**E13 – SMCJ30CA clamp against the BTT6050 absolute maximum.**
- The SMCJ30CA clamps at 48.4 V at 31 A (10/1000 µs, JLCPCB data), and more above that current. The BTT6050 VS limit is
  48 V (P_4.1.1), with a load-dump rating VS(LD) = 65 V (RI = 2 Ω, ISO 7637-1). That agrees, because short pulses
  between 48 and 65 V are covered by the load-dump entry. No action; recorded so the validator does not repeat it.

## Layout rules (PCB phase)

1. **Protection at the connectors.**
   - D30 sits between the J10 pins with its pads on the same copper as the terminal. J5 TVS (D16–D19, D50–D54) and J4
     TVS (D9, D10) sit within 3–5 mm of the connector pins.
   - Order on each line: connector → TVS → series R / filter → circuit. No trace between the pin and the TVS that is
     not also the signal path (stub-free, "flow-through" routing).
   - TVS ground return goes by the shortest path (several vias) into the ground plane under the TVS.
2. **Surge current paths.**
   - VS and GND copper between J10, D30 and the switches is wide (2 oz). The output surge path (4-ch: OUT → PROFET → VS →
     D30; HC2: OUT TVS → GND → J10.2) must be a low-impedance route on the plane, not a trace.
   - Do not route the clamp current through signal-ground areas of the ESP32 or the ISO1044.
3. **Layers and ground.** Use at least 4 layers if the cost target allows (top signal, solid GND, VS power, bottom signal).
   - ISO1044 §11.1 asks for a 4-layer stack for low EMI. On a 2-layer board, make the bottom layer a continuous GND plane
     and route VS and signals on top.
   - No splits or slots in GND under the ESP32, the buck, the panel inputs or the PROFET/MOSFET gate and sense routes.
4. **Loops.**
   - The battery cable's + and − terminals are adjacent. Keep the VS–GND loop of J10, C-bulk, the first switch and D30 as
     small as possible.
   - The panel connector J5 puts SW_SUPPLY on pin 5 and the returns on pins 1–4 and 6–9: keep their routes together.
5. **Buck hot loop.**
   - C1, the new 100 nF, VIN and GND (pins 5/2) in the smallest loop, on the top layer, with no vias in the loop.
   - SW node short, with minimum copper area. L1 right next to it and the keep-out under L1 on the plane free of
     unrelated traces. Footprints for the SW snubber and the boot resistor placed at the pins.
   - The feedback divider (R9/R10) close to the FB pin, away from SW and L1. Keep the buck at the end of the board
     away from the NTC TH1, the ADC lines and the CAN connector.
6. **HC2 sense routing.** Kelvin connection from the 1 mΩ shunt pads to CS+/CS−, as a differential pair of short
   traces, with the X and Y capacitor pads at the controller pins. No gate or SW trace crosses them. The MMBT3904 sensor
   routes (DIODE, ground) are a short pair with a guard ground, away from the gate nets.
7. **Gate drive.** Gate loops (PU/PD → RG → gates → SRC) tiny and close to the controller. Space between the two MOSFETs
   and the OUT copper; OUT copper area as small as the current allows (it is a radiating plane at fast edges).
8. **Switch and LED input filters.** R34–R37 and C14–C17 sit at J5, before anything else; the C14–C17 ground leg short.
   Place D16–D19 first, then R, then C. The LED line has D50–D53 → R19/R22/R25/R28 → C50–C53 → transistor.
9. **Isolation barrier.**
   - No copper (pour, trace, via, silkscreen aside) under the ISO1044 between pins 1–4 and 5–8.
   - Keep the GND and GND_CAN islands ≥ 4 mm apart around the body (the SOIC-8 creepage, in line with its datasheet
     rating). Only the Y capacitor (E6) crosses the gap, with its own pads.
   - D9, D10, F3, FB2, D11 and the TPS7B91 are all on the GND_CAN side; U5 pins 1–4 on the GND side.
10. **Creepage and clearance on the battery side** (`UNVERIFIED` against the standard text; from IPC-2221B Table 6-1,
    B2 external uncoated, below 3050 m).
    - 0.6 mm minimum for 31–100 V between VS (clamp 48 V) and anything else on outer layers.
    - Aim for ≥ 1.0 mm because of condensation and salt on a boat, and apply conformal coating after assembly.
    - Terminal pitch of 3.81 mm is fine. Keep the J10/J11 pads' copper edges clear of the board edge by ≥ 1 mm.
11. **ESP32.** The antenna keep-out of the module as per its datasheet, and no copper or components below it. Keep power
    switches (heat and edges) away from the module. USB D+/D− as a short differential pair; the ESD diodes first.
12. **Mounting.** Mounting holes unplated or isolated from every net (invariant 6, H1/H2 are on no net).
13. **Test points.** Add test points for VS, 3V3, GND, SW node of the buck, and CAN H/L to allow the pre-compliance
    measurements without soldering.

## Installation guidance (for the README)

- **Battery feed.** Fuse at the battery. Run + and − as a twisted or tightly bundled pair, as short as possible. Do not
  run them next to the VHF antenna coax; keep ≥ 0.5 m from the antenna feed and the transmitter, and cross at 90°.
- **Alternator and load dump.** The PDM does not handle load dump (decision 12). Use an alternator protection device or a
  field-disconnecting battery switch. Never open the main battery switch while charging.
- **Loads.** Run each load's return with its feed (same cable, twisted) back to the battery negative bus. Do not return
  load currents through the PDM ground. Fuse each output wire. No PWM above 200 Hz; on HC2 no PWM until the gate
  slew is limited (E2).
- **Inductive loads** (solenoids, relays, horns, motors) get a diode or TVS at the load. The HC2 freewheel diodes
  take only what the wiring leaves.
- **Panel cable.** One screened multicore, ≤ 10 m, with the switch, LED and supply wires inside the same cable. Connect the
  drain/shield only at the PDM end (J5.10). Use dry-contact switches **without** a lamp across the contacts (E8).
  Do not share the cable with other loads.
- **NMEA 2000.** Drop cables ≤ 6 m, the backbone grounded once at the power tap. The device has no shield pin, so do not
  connect the drain at the node. Keep the drop away from the VHF coax.
- **USB.** Service only. Unplug afterwards. Use a battery-powered laptop or a USB isolator, so the boat's DC negative is not
  tied to shore PE (E10).
- **Position.** Enclosed, vented box (decision 10) as far from the VHF antenna and its coax as practical. The plastic box
  provides no shielding; the cables are the antenna, so cable practice matters more than box position.
- **12 V boats.** Panel-switched outputs can drop out when cranking pulls the battery below ≈ 8 V (E8).

## Not checked

- Anything on a PCB (none exists). All "layout" statements are rules, not checks.
- Capacitance, dynamic clamping and TLP data of SMAJ30CA, SMCJ30CA, PESD0402V05 and PESD2CAN (datasheets not retrievable
  here), and the voltage rating of C1523.
- The ferrite BLM18AG601SN1D rated current and impedance at 156 MHz.
- MOSFET BSC030N08NS5 gate charge and avalanche data (the figures in E2 are assumptions).
- Actual emission, immunity and surge behaviour: nothing was measured. The VHF numbers are field-strength estimates.
- ESP32-S3 module RF behaviour, Wi-Fi coexistence, ADC accuracy under RF.
- Interrupt rating of the 1812L050/60GR PTCs against the prospective current of a battery short (see question E14).
- The PROFET reverse-battery and inductive-load energy limits (validator scope), the Kangnex CAN connector, the USB-C
  connector.
- IEC 60945 and CISPR limits themselves were recalled, not read.

<!-- findings:begin -->
```json
[
  {
    "id": "E1",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-hc2",
    "location": "hc_channel: U11/U12 pin 20 (VS), C102/C202",
    "summary": "TPS48110A VS pin wired straight to VS; TI recommends RVS 100 ohm + CVS 0.1-10 uF and gives 60 V/us as abs-max slew on VS/CS+/CS-/ISCP.",
    "fix": "Add RVS 100 ohm and CVS 1 uF/100 V in the VS supply of each controller after checking IVS.",
    "class": "small",
    "reason": "Passive decoupling on one board, no function or topology change, below CRITICAL.",
    "touches": [],
    "cost_delta_usd": 0.03
  },
  {
    "id": "E2",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-hc2",
    "location": "hc_channel: R104/R204 (RG 10 ohm), GATE/PU/PD",
    "summary": "MOSFET gate drive is not slew-limited (about 400-800 V/us estimated, PD direct), so switching clicks reach the VHF receiver and cable emissions rise; PROFET channels switch at 0.8 V/us.",
    "fix": "RG_PU about 100-220 ohm plus an RGATE_PD footprint, tune on the bench, then recheck switching loss, SOA and the fast short-circuit response.",
    "class": "big",
    "reason": "Changes switching and protection timing of a safety-relevant output (bilge pump) and the heat budget.",
    "touches": ["safety"],
    "cost_delta_usd": 0.02
  },
  {
    "id": "E3",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "system",
    "location": "root sheet: J10 battery input, D30, net VS",
    "summary": "Battery input has only an SMCJ30CA: no bulk or HF capacitance and no filter, so short-circuit turn-off spikes, switched-current steps and RF go straight onto the cable and the rails.",
    "fix": "Add about 100 uF/50 V bulk plus 1-2.2 uF/100 V ceramic at J10 (more on HC2), 1 uF/100 V at each BTT6050 VS tab, and a ferrite/CMC footprint.",
    "class": "big",
    "reason": "Shared root sheet, new part type, cost about 0.2-0.3 USD per board.",
    "touches": ["shared-sheet", "budget"],
    "cost_delta_usd": 0.3
  },
  {
    "id": "E4",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-hc2",
    "location": "hc_channel: CS+/CS- (R102/R101), EN/UVLO (R105/R106), OVSET (R107), DIODE (Q13), IWRN (R113)",
    "summary": "Current-sense, UVLO/OV and DIODE pins have no EMI filtering; 35-100 V/m near a 25 W VHF set can offset the 25 mV breaker and 80 mV short-circuit comparators or chatter UV/OV on a safety-relevant output.",
    "fix": "Footprints per TI Table 9-3: about 1 nF X cap and 100 pF Y caps on CS+/CS-, 10 nF on EN/UVLO and OVSET, 1 nF on DIODE, 100 pF on IWRN; tune in test.",
    "class": "small",
    "reason": "Passive filter footprints on one board, function unchanged, no new unique part.",
    "touches": [],
    "cost_delta_usd": 0.05
  },
  {
    "id": "E5",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-hc2",
    "location": "hc_channel: OUT1/OUT2 at J11, D102/D202",
    "summary": "HC2 outputs have no surge/ESD clamp at the connector (invariant 4); the back-to-back MOSFETs also stop positive surges from reaching D30, so only the 80 V avalanche limits them.",
    "fix": "Add SMAJ30CA (already on the BOM) from each OUT to GND at J11 with a short return to J10.2; check float-switch case at 28.8 V.",
    "class": "big",
    "reason": "New protection element on output lines (protection topology) of safety-relevant outputs.",
    "touches": ["protection", "invariant", "safety"],
    "cost_delta_usd": 0.08
  },
  {
    "id": "E6",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "system",
    "location": "can: GND_CAN island, U5 ISO1044, D9, D10, J4",
    "summary": "No high-frequency return across the isolation barrier (CIO about 1 pF) and no CMC option, so the N2K cable can radiate logic-ground noise and ESD lifts the whole island; not measured.",
    "fix": "Add a footprint for a 1-2.2 nF/1 kV Y-class capacitor GND_CAN-GND and a CMC footprint in series with CANH/CANL; confirm with a pre-compliance scan.",
    "class": "big",
    "reason": "Shared can sheet, protection and grounding topology change.",
    "touches": ["shared-sheet", "protection"],
    "cost_delta_usd": 0.05
  },
  {
    "id": "E7",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "system",
    "location": "power-usb: U3 LMR51610YDBVR, C1, C2, L1",
    "summary": "Buck is the 1.1 MHz PFM variant; PFM drops into the 150-350 kHz band at light load, the datasheet's separate 0.1 uF at VIN is missing, C1 is only 50 V, and SW ringing can land in the tightly limited 156-165 MHz band.",
    "fix": "Add 100 nF/100 V at VIN, footprints for an SW RC snubber and a boot resistor, and consider the LMR51610YF (FPWM) if the scan shows PFM noise.",
    "class": "big",
    "reason": "Shared power-usb sheet; the FPWM option would be a different extended part.",
    "touches": ["shared-sheet", "new-extended-part"],
    "cost_delta_usd": 0.05
  },
  {
    "id": "E8",
    "kind": "finding",
    "severity": "MINOR",
    "board": "system",
    "location": "analog_sw: R34-R37, C14-C17, R3-R8",
    "summary": "Hardware switch path has tau 0.32 ms (no real debounce), turns the output off below about 8 V at the switch (12 V cranking), and a lamp across the switch contacts above about 1.4 mA turns it on.",
    "fix": "Raise C14-C17 to 470 nF-1 uF; document dry contacts and the cranking behaviour in the README.",
    "class": "big",
    "reason": "Shared analog_sw sheet and the invariant 1 signal path.",
    "touches": ["shared-sheet", "invariant"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E9",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "channel: OUT1-OUT4 at J11, C102/C202/C302/C402",
    "summary": "4-ch outputs rely on the PROFET (body diode to VS, clamp, 4 kV HBM) and D30 at J10; this meets the intent of invariant 4 but not its wording, and D30 is far from J11.",
    "fix": "Document the output rule in invariant 4 and leave a DNP SMAJ30CA footprint per output; keep the VS copper to D30 wide.",
    "class": "big",
    "reason": "Touches an invariant and the protection scheme.",
    "touches": ["invariant", "protection"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E10",
    "kind": "finding",
    "severity": "MINOR",
    "board": "system",
    "location": "power-usb: J3 shield, D4-D6 PESD0402V05",
    "summary": "USB shield is tied to battery negative (shore PE loop via a laptop) and the ESD diode is listed with a 40 V clamp against 3.6 V ESP32 pins (unverified).",
    "fix": "README: service only, battery-powered laptop or USB isolator; check the TLP data of the DOWO part before ordering; consider an RC shield-to-GND.",
    "class": "big",
    "reason": "Shared power-usb sheet; a shield change is a design decision.",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E11",
    "kind": "finding",
    "severity": "MINOR",
    "board": "system",
    "location": "analog_sw: C50-C53 (C1523); power-usb: C1",
    "summary": "1 nF collector capacitors and the 2.2 uF buck input capacitor are probably 50 V parts against a 48.4 V TVS clamp; TI advises twice VIN for CIN.",
    "fix": "Use 100 V (or 63 V) parts for C50-C53 and C1 if available as basic parts.",
    "class": "big",
    "reason": "Shared sheets (analog_sw, power-usb); part change needs the stock check.",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.02
  },
  {
    "id": "E12",
    "kind": "finding",
    "severity": "MINOR",
    "board": "system",
    "location": "root sheet: J10.2 (GND), D102/D202 return path on HC2",
    "summary": "Board ground reaches the battery negative through one terminal pole that carries TVS surge current and, on HC2, motor freewheel current (up to 25 A per channel); its rating is not defined.",
    "fix": "Size the GND pole (or use two poles) in /system mechanical to match the VS input; wide GND copper to J10.2.",
    "class": "big",
    "reason": "Terminal and pole count decision.",
    "touches": ["connector", "mechanical"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E13",
    "kind": "finding",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "root sheet: D30 SMCJ30CA vs U11-U14 VS",
    "summary": "SMCJ30CA clamps at 48.4 V at 31 A, the BTT6050 absolute maximum is 48 V, but VS(LD) is 65 V (ISO 7637-1), so short clamp excursions are covered; recorded only.",
    "fix": "None.",
    "class": "small",
    "reason": "Documentation only.",
    "touches": [],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E14",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "F1, F3, F4 (1812L050/60GR)",
    "summary": "Is the interrupt rating (Imax at 60 V) of the 1812L050/60GR PTC enough for the prospective current of a direct battery short at J5.5 (F4 is fed from VS) or on NET-S? I could not read the datasheet.",
    "fix": "Validator to check Imax and minimum resistance against 30 V / (cable + PTC resistance).",
    "class": "big",
    "reason": "Question for the owner or validator, not a design change.",
    "touches": [],
    "cost_delta_usd": 0.0
  },
  {
    "id": "E15",
    "kind": "question",
    "severity": "INFO",
    "board": "system",
    "location": "can: J4 (4 poles, no shield pin), project goal",
    "summary": "Is IEC 60945 (marine) compliance a goal or only good practice, is a pre-compliance scan planned, and may the N2K shield stay unconnected at the node (4-pole J4)? This sets how far E3-E7 must go.",
    "fix": "Owner ruling on the compliance target and the shield strategy.",
    "class": "big",
    "reason": "Only the owner can answer; shared sheet and connector.",
    "touches": ["shared-sheet", "connector"],
    "cost_delta_usd": 0.0
  },
  {
    "id": "L1",
    "kind": "lever",
    "severity": "INFO",
    "board": "system",
    "location": "power-usb: U3",
    "summary": "LMR51610YF (FPWM, same 1.1 MHz) would avoid PFM noise below 350 kHz; E7 asks for a scan first.",
    "fix": "Swap only if the pre-compliance scan shows PFM noise; check price and stock.",
    "class": "big",
    "reason": "New extended part on a shared sheet.",
    "touches": ["shared-sheet", "new-extended-part"],
    "cost_delta_usd": 0.1
  }
]
```
<!-- findings:end -->
