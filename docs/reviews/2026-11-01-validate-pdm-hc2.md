# Validation – pdm-hc2, schematic phase

Date: 2026-11-01. Task T-0004, unattended. Reviewer: validator, independent of the design sessions. Scope: `hardware/pdm-hc2`
(root, `power-usb`, `can`, `analog_sw`, `hc_channel` ×2) and the `lib/` parts it uses. No PCB exists.

Read first: `CLAUDE.md`, `docs/ARCHITECTURE.md`, `docs/decisions.md`, `docs/AUTONOMY.md`, `docs/design-notes.md`,
`hardware/pdm-hc2/STATUS.md`, `docs/reviews/2026-10-30-validate-pdm-4ch.md`, `docs/reviews/2026-10-30-emc-system.md` and
`docs/OWNER-INBOX.md`.

This report does not repeat:

- EMC findings E1–E5 for HC2: VS RC filter and the 60 V/µs slew limit, gate slew for EMC, J10 bulk capacitance, sense-pin
  filtering and the output clamp.
- Validator findings V2, V3, V6, V8 and V9 on the shared sheets. They apply to HC2 unchanged, because the sheets are
  identical (see Method).

Where a finding here builds on one of them, it says so.

**Method.**

- I ran `kicad-cli sch erc` and `kicad-cli sch export netlist --format kicadxml` into scratch. No `*.kicad_prl` file was
  created or changed. Every net and pin quoted below comes from that netlist.
- The shared sheets `power-usb`, `can` and `analog_sw` are the same in both boards, apart from UUIDs and the project name
  (`diff`).
- I downloaded the datasheets with curl and extracted them with pypdf in a temporary venv. I rendered the pin diagram, the
  package outline and the land pattern to PNG with pypdf and `sips`.

**Primary sources**

- TI TPS4811-Q1 datasheet SLUSEE5E (January 2022, revised April 2026), 50 pages.
- Infineon BSC030N08NS5 Final Data Sheet Rev. 2.3, 2019-10-31. This is the JLCPCB/LCSC copy, because the direct Infineon
  download returned HTML.
- Espressif ESP32-S3-MINI-1/1U datasheet v1.7.
- JLCPCB part data (jlc_get_part): C17556513, C501507, C2903470, C7420368, C96446, C15849.
- `tools/heat_budget.py`, rerun.

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| MAJOR | 3 |
| MINOR | 3 |
| INFO | 2 (+ 2 questions) |

**ERC:** 0 errors and 6 warnings. All six are `lib_symbol_mismatch` (Q3–Q6 BC817, J3, U3), as STATUS says.

**Netlist:**
- The only single-pin nets are intended no-connects: spare ESP32 pins, J3 SBU, U6 NC and U11/U12 pin 11 (N.C.).
- There are no global labels, so the ERC exclusion "global label only appears once" hides nothing.

**Main result.** The controller wiring, the pin numbers, the custom footprint and the protection equations are all
correct. The three MAJOR findings are about behaviour that the current values allow:

1. Between the continuous rating (≈ 15 A) and the hardware breaker (≈ 25 A), no hardware protection acts. In that band the
   MOSFETs exceed their 150 °C limit before the remote over-temperature trip (H1).
2. An ordinary capacitive load will probably trip the 80 A / 4 µs short-circuit protection at switch-on, and the channel
   then stays off for 3.8 min (H2).
3. A reversed battery puts about −28 V on controller pins rated −1 V (H3).

## Findings

### CRITICAL

None.

### MAJOR

**H1 – hc_channel ×2: no hardware protection between ≈ 18 A and the 24–26 A breaker, and the over-temperature trip sits
above the MOSFET's Tj max.**

- **Evidence: breaker threshold.** R113/R213 RIWRN = 47 kΩ. Eq. 6 gives VSNS = 11.9 × 100 / 47 k = 25.3 mV, so IOC ≈ 25 A
  with RSNS 1 mΩ.
  - The spec spread at 30 mV is −4.6/+2.9 % (V(SNS_WRN) 29.2/30.6/31.5 mV, §6.5).
  - Together with the 1 % shunt that gives ≈ 24–26 A. The spread at 25 mV is extrapolated, so it is `UNVERIFIED`.
- **Evidence: breaker timer.** Above IOC the device turns off only after tOC = CTMR × 1.2 V / 82 µA = 146 ms (Eq. 7). Below
  IOC it never turns off on current.
- **Evidence: heat budget.** Rerun at 40 °C (`--channels 2 --part HC-2xBSC030 --rth-ja 20 --r-box 0.9 --r-path 0.002`):

  | Current | Tj (tool input) | Tj (datasheet max RDS(on), H5) |
  |---|---|---|
  | 15 A | 87 °C | 88 °C |
  | 18 A | 113 °C | 117 °C |
  | 20 A | 137 °C | 143 °C |
  | 22 A | 169 °C | – |

  BSC030N08NS5 Tj max is **150 °C** (Table 2, "Operating and storage temperature −55…150 °C").
- **Evidence: over-temperature trip.** It acts at T(DIODE_TSD_rising) = 140/150/160 °C at the MMBT3904 (§6.5, §8.3.6). The
  sensor sits on the PCB between the MOSFETs, so the junctions are at or above the sensor temperature when it trips. Between
  ≈ 20 A and ≈ 24 A the MOSFETs can run continuously above their rated Tj, and nothing in hardware turns them off.
  - The copper around them, the FR-4 and the ASA enclosure (decision 10) also run hot. Their limits are not in the design
    documents (`UNVERIFIED`).
- **Why it matters.**
  - design-notes §4a says that "continuous protection comes from the temperature sensor and the firmware soft fuse". The
    sensor does not protect in this band, so only the firmware soft fuse does.
  - Invariant 1 exists precisely for the case where the ESP32 is not running. On the HC2 the outputs are bilge forced-run
    and the searchlight, which are safety-relevant (decision 15, CLAUDE.md §7).
  - The installation fuse does not close the gap either: a wire fuse sized near 15–20 A carries 20–24 A for minutes.
- **Fix (owner):**
  - (a) Lower IOC towards the continuous rating, e.g. RIWRN 68 kΩ (E12) → IOC ≈ 17.5 A, Tj ≈ 110 °C steady. The 146 ms timer
    still passes motor starts. This needs the start current of the bilge pump (SEAFLO, not published) or a measurement.
  - (b) Keep 25 A and state in the README and on the label that every HC2 output needs a breaker that trips at ≤ 15–18 A
    within minutes.
  - (c) Both of the above, plus a firmware soft fuse.

  This changes the HC2 budget in `docs/ARCHITECTURE.md` ("breaker 25 A / 146 ms") and touches decision 8.

**H2 – hc_channel ×2: capacitive loads will probably trip the 80 A fast short-circuit protection at switch-on, and the
channel then stays off for 3.8 min.**

- **Evidence: gate drive.** PU drives the gate through 10 Ω (R104/R204) from the 12 V bootstrap. PD goes direct (§8.3.1;
  PU peak 3.75 A). The gate is referenced to SRC, so VGS reaches 10–12 V in well under a microsecond and the MOSFETs
  switch fully on. A capacitive load is then charged through the loop resistance and inductance only.
- **Evidence: short-circuit threshold and retry.**
  - ISC = 15.6 µA × (4.7 k + 464) / 1 mΩ = 80 A; 70.7–90.9 A with I(ISCP) 13.7–17.6 µA (Eq. 11, §6.5).
  - Response time tSC is 4–5 µs (TPS48110, §6.6).
  - After a short-circuit trip the TMR auto-retry runs: tRETRY = 22.7·10⁶ × 10 µF ≈ 3.8 min (Eq. 9, §8.3.3.3).
- **Estimate (`UNVERIFIED`, needs a bench test).** Assume a 3 m load cable (loop ≈ 3 µH, ≈ 50–80 mΩ including the
  MOSFETs, the shunt and the capacitor ESR):
  - 100 µF of load input capacitance gives Z0 = √(L/C) ≈ 0.17 Ω.
  - The damped peak current is ≈ 90–100 A, reached after ≈ 25 µs. That is above the threshold for longer than tSC.
  - From about 50 µF upwards the trip is likely.

  LED searchlights and work lights with drivers, VHF/radio sets and inverters commonly have 100 µF to several mF at their
  input (`UNVERIFIED` per load).
- **Not already covered.**
  - design-notes §4a and decision 19 cover only halogen inrush.
  - EMC E2 asks for RG_PU 100–220 Ω for EMC. That slows the edges to a few µs, but it does not limit the inrush of a
    capacitive load over the needed 0.1–1 ms.
- **Fix (owner):** TI §8.3.2.1, gate slew-rate control.
  - R1 in the PU path and C1 + R2 (≈ 10 Ω) at the gate, so that IINRUSH = 0.63 × 12 V × CLOAD / (R1·C1) (Eq. 3). Example:
    R1 = 100 k and C1 = 3.9 nF give ≈ 20 A into 1000 µF.
  - PD stays direct, so protective turn-off stays fast.
  - CBST must exceed Qg(total) + 10·C1 = 152 nC + 39 nC (Eq. 4). C103 = 1 µF is enough.
  - The MOSFET energy during the ramp (≈ ½·C·V², 0.4 J for 1000 µF at 28 V over ≈ 1–2 ms) has to be checked against SOA
    Diagram 3.

  Alternatively, state a maximum load capacitance per output. Combine this with E2.

**H3 – hc_channel ×2 / root J10: reversed battery puts about −12…−30 V on TPS48110 pins rated −1 V.**

- **Evidence: ratings.** Absolute maximum ratings (§6.1):
  - VS, CS+, CS− and ISCP to GND: **−1 V** min.
  - OV, EN/UVLO and INP to GND: −1 V.
  - Reverse polarity protection is specified only for the **output** ("down to −30 V", Features, §8.3.7).
- **Evidence: wiring (netlist).**
  - VS (U11/U12 pin 20) is on the battery net `VS` directly.
  - CS− is on `SNS` (shunt to drain), and CS+ connects through only 100 Ω.
  - The only battery-input protection is D30 SMCJ30CA. It is **bidirectional** and does not conduct below its ≈ 33 V
    breakdown.
  - With J10 reversed, both controllers see the full battery voltage negative on VS/CS±/ISCP against their GND. EN/UVLO and
    OV see ≈ −3.4 V and −1.0 V through the 1 MΩ ladder, which is current-limited.
- **Consequence (`UNVERIFIED` mechanism).** Any internal ESD or substrate path from GND to VS would then carry battery
  current, with no limit on the board. The likely result is that both controllers are destroyed. The MOSFETs block the
  loads (back-to-back), and the buck is protected by D2.
- **Not already covered.** design-notes §8 says "the switches survive with the ground network". That statement is about the
  PROFETs of the 4-ch board (V10). It is not true for HC2, and HC2 has no ground network.
- **Fix (owner, protection and shared root sheet):**
  - (a) Reverse-polarity protection at J10 for ≈ 50 A: an ideal-diode controller with a MOSFET, a new part type.
  - (b) A crowbar diode from GND to VS, rated to blow the required battery fuse. For example, make D30 unidirectional
    (SMCJ30A) if its forward surge rating suffices, which needs checking.
  - (c) A keyed/polarized J10 plus a README warning that reverse connection destroys the HC2.

  (c) is the minimum; (a) or (b) are hardware.

### MINOR

**H4 – hc_channel: no 1 nF across the MMBT3904 remote sensor (Q13/Q23), which TI makes mandatory.**
- TPS4811-Q1 §9.6.1: "a small 1000 pF bypass capacitor **must** be placed in parallel with the MMBT3904 to reduce the
  effects of noise". The `DIODE` net has only Q13 B/C and U11 pin 10 (netlist).
- EMC E4 lists "1 nF on DIODE" as a footprint to tune in test. The datasheet makes it a fixed part of the circuit,
  independent of EMC tuning.
- A noisy DIODE reading can give a false over-temperature trip (FLT_T, 512 ms off) or a missed one.
- Fix: C 1 nF 0402 (C1523, already on the BOM) from DIODE to GND at each MMBT3904, with the emitter Kelvin-connected to the
  controller GND (§9.6.1).

**H5 – tools/heat_budget.py: HC-2xBSC030 RDS(on) at 150 °C is 11.2 mΩ; the datasheet maximum gives 11.7 mΩ.**
- BSC030N08NS5 Diagram 9 (p. 8, ID = 50 A, VGS = 10 V): max 3.0 mΩ at 25 °C and ≈ 5.35 mΩ at 150 °C. The path is
  2 × 5.35 + 1 (shunt) = 11.7 mΩ. The 25 °C value (7.0 mΩ) is right.
- With 11.7 mΩ (scratch copy of the tool): 15 A → 88 °C (was 87), 18 A → 117 (113), 20 A → 143 (137). With
  `--p-other 1.9` (panel interface at 30 V, see V7), 15 A → 90 °C.
- The 15 A rating stands, but the margin to the hot band of H1 is smaller.
- Fix: set `'HC-2xBSC030': (0.0070, 0.0117)` and add the source in a comment.

**H6 – design-notes: two statements do not match the HC2 schematic.**
- §1 still names the "TPS48111-Q1" and "≈ 8–20 A per channel". The board uses the TPS48110A-Q1 (decision 8) at ≈ 15 A.
- §9 (bilge pumps) says "an OUT voltage divider lets the PDM see float-driven runs". The schematic has no OUT divider:
  `OUT1` = D102 K, J11.1, Q12 D only. IMON cannot see a float-driven run either, because that current does not pass the
  shunt.
- In the current design only the sense-only inputs SW3/SW4 on J5 (§4a) can see a float run, and only if the installer wires
  the pump feed to them.
- Fix: correct §1 and §9 to the as-drawn design. Whether an OUT divider is wanted (spare ADC1 pins IO4/IO5 exist) is a
  question for the owner (Q2).

### INFO

**H7 – first switch-on after power-up waits for the bootstrap charge; overcurrent retry is long.**
- TDRV_EN = CBST × 7.6 V / 100 µA = 76 ms nominal (Eq. 1). With 0603 X5R DC-bias loss it is shorter; at the minimum pump
  current (80 µA) and V(BST_UVLOR) 8.1 V it is up to ≈ 100 ms.
- This applies to the hardware switch path too, so a panel switch that is already on when the battery is connected acts
  after ≈ 0.1 s.
- After a breaker or short-circuit trip the channel retries after ≈ 3.8 min. Toggling INP resets the counter (§8.3.3.2,
  Figure 9-12), so a user can retry by switching off and on.
- Fix: none needed; record both times in design-notes §4a and in the user documentation.

**H8 – IO3 (JTAG source strapping pin) is held low by IMON2's network (R212 10 k, R211 12 k).**
- This is the same as V11 on the 4-ch board and is harmless while EFUSE_STRAP_JTAG_SEL is not burnt (module datasheet v1.7
  §4). Production must not burn that eFuse.

### Questions

- **Q1 (for H2):** Which loads with input capacitance above ≈ 50 µF go on HC2 outputs? Examples: LED searchlight or work-light
  drivers, radios, an inverter. This sets whether gate slew control is needed and what inrush target to use.
- **Q2 (for H1/H6):** Should the hardware breaker sit near the continuous rating (≈ 17.5 A), or stay at 25 A with a
  documented requirement for an external breaker? And is an OUT voltage divider wanted for float-run detection, or are the
  SW3/SW4 inputs enough?

## Checked and OK

- **TPS48110A-Q1 symbol (lib and embedded) and netlist.** All pins match SLUSEE5E Figure 5-1 / Table 5-1 (p. 5–6):
  - 1 EN/UVLO, 2 OV, 3 INP, 4 FLT_T, 5 FLT_I, 6 GND, 7 IMON, 8 IWRN, 9 TMR, 10 DIODE;
  - 11 N.C. (no-connect pin, flagged), 12 BST, 13 SRC, 14 PD, 15 PU;
  - pin 16 absent, 17 CS−, 18 CS+, 19 ISCP, 20 VS.
- **Orderable part.** TPS48110AQDGXRQ1 is listed as Active in the package addendum (p. 43). The TPS48110 variant has OV and
  over-temperature auto-retry (512 ms) (Table 4). JLCPCB C17556513 is that part, 3.5–80 V.
- **Footprint `Texas_DGX0019A_VSSOP-19_3x5.1mm_P0.5mm`** against the DGX0019A outline and land pattern (4226944/A, p. 47–48):
  - pads 1.45 × 0.3 mm, 0.5 mm pitch, rows at ±2.2 mm (4.4 mm span);
  - pin 1 top-left, 10 bottom-left, 11 bottom-right, 20 top-right;
  - position 16 (right column, y = −0.25) omitted;
  - lead tips at ±2.35–2.55 mm and feet 0.4–0.7 mm lie inside the pads;
  - body 3.0 × 5.1 mm on F.Fab;
  - no thermal pad, as in TI's land pattern.

  The comparison with the JLCPCB footprint is still open (STATUS item 3).
- **BSC030N08NS5** (Rev 2.3, p. 1, 3–4):
  - SuperSO8 pins 1–3 S, 4 G, 5–8 D. The symbol has S 1–3, G 4 and D 5.
  - KiCad `TDSON-8-1` uses pad 5 as one 4.55 × 4.41 mm drain pad covering leads 5–8, so the single D pin is complete.
  - VDS 80 V (≥ 48 V transients), VGS ±20 V against BST–SRC ≤ 13 V, ID,pulse 400 A, EAS 250 mJ.
  - RDS(on) max 3.0 mΩ at 10 V.
  - Qg max 76 nC, so CBST 1 µF/50 V (C15849) is far more than 2 × 76 nC / 1 V (Eq. 20), and above the 0.1 µF minimum (§6.2).
- **Power-path topology** (netlist; §8.3.3, Figure 8-12, Figure 9-14):
  - VS → R101 1 mΩ → SNS = CS− → Q11 drain;
  - Q11/Q12 common source = SRC (U pin 13, C103 to BST);
  - Q12 drain = OUT;
  - RSET R102 100 Ω VS → CS+ (inside the 50–100 Ω range);
  - RISCP R103 from ISCP to CS−, with C101 1 nF across ISCP–CS− as TI recommends (§9.2.2.4);
  - PD direct to both gates, PU via R104 10 Ω.
- **Back-feed blocking.** With the channel off and OUT driven to 28.8 V by a float switch, Q12's body diode is reverse-biased.
  VS/CS± to SRC stays within −60…100 V, and SRC to GND within −30…100 V (§6.1).
- **Voltage ratings at 30 V / 48 V.**
  - VS, CS± and ISCP: 100 V.
  - EN/UVLO = 48 × 139/1139 = 5.9 V (abs max 20 V, recommended ≤ 15 V); OV = 1.6 V.
  - TMR, IWRN and DIODE stay below 5.5 V.
  - C102 100 nF/100 V is above the 22 nF VS minimum.
  - C105 10 µF/25 V X5R (C96446) on TMR at ≤ 1.3 V.
  - SS510B 100 V / 5 A, IFSM 120 A (C7420368).
- **UVLO/OV.** 1 MΩ / 100 kΩ / 39 kΩ give:
  - UVLO 9.67 V rising and 9.10 V falling;
  - OV 34.5 V rising (33.9–35.0 V over V(OVR) 1.16–1.20 V) and 32.4 V falling.

  These are above the 30 V charging maximum (decision 3) and below the 48 V transient. Ladder current ≈ 21 µA at 24 V, more
  than 20 × the 0.3 µA pin leakage (§9.2.2.8).
- **Breaker and timers.**
  - IOC ≈ 25 A (Eq. 6, above).
  - tOC 146 ms (Eq. 7; 122–178 ms over the current and threshold spread, before the ±20 % capacitor tolerance).
  - FLT_I warning 134 ms (Eq. 8).
  - Retry 3.8 min (Eq. 9).
  - ISC 80 A (71–91 A, Eq. 11).

  These match design-notes §4a and ARCHITECTURE.
- **Fault energy.** In the 25–80 A band each MOSFET sees ≈ 26 W for ≤ 178 ms. ZthJC ≈ 0.9 K/W at 0.1 s (Diagram 4) gives a
  junction-to-case rise of ≈ 25 K, so it survives. A hard short reaches ≈ 150–200 A before the 4–5 µs trip, which is inside
  the 400 A pulse rating.
- **IMON.**
  - Gain 0.9 × 12 k / 100 = 108 (Eq. 13), i.e. 0.108 V/A, so 25 A gives 2.7 V. The ESP32 calibrated full scale (2.9 V, see
    V3) is ≈ 26.9 A.
  - In a short IMON clamps at 6.5 V typical (abs max 7.5 V). R112 10 k + BAT54S then limit the current into +3V3 to
    ≈ 0.3 mA.
  - The offset of ±0.2 mV means ±0.2 A at low current.
- **INP and the power-up state.**
  - INP has an internal pull-down (Table 5-1).
  - IO6/IO7 are pulled down (R5/R6 2.2 k), and the SW1/SW2 nodes by R38/R39 4.7 k.
  - Every output is off at power-up.
  - The hardware path SW node → BAT54C → R108 10 k → INP needs V(INP_H) ≤ 2.0 V. That gives ≈ 2.45 V with the 3.3 V rail down
    at SWIN 10.5 V (node 2.67 V per V2, minus ≈ 0.2 V diode drop). The controller GND is board GND, so there is no
    ground-shift penalty as on the 4-ch board. The INP pull-down current is not specified, so the R108 drop is
    `UNVERIFIED`.
- **FLT_I/FLT_T.** These are open-drain with 10 k pull-ups to +3V3 (0.33 mA, below the 10 mA limit). They go to IO34, IO35,
  IO36 and IO37 on module pins 29, 31, 32 and 33. Those pins are free on the -N8 module, which has quad flash and no PSRAM
  (MINI-1 datasheet v1.7, pin table and ordering table).
- **MMBT3904 sensor.** Q_NPN_BEC on SOT-23: pin 1 B and pin 3 C go to DIODE, pin 2 E to GND, as §8.3.6 requires.
- **Variant ID.** R29 10 k / R42 4.7 k → 1.05 V (decision 14).
- **Pin map against ARCHITECTURE.**
  - IO2/IO3 IMON1/2, IO6/IO7 drive, IO8/IO11 pull-downs only.
  - IO9 NTC, IO10 VBAT, IO14–16/IO21 switch states, IO17/18 CAN.
  - IO33–IO37 as listed, IO38–41 LED sinks.
  - Invariant 10 holds: all analog inputs are on ADC1.
- **Shared sheets.** `power-usb`, `can` and `analog_sw` are identical to `pdm-4ch`. The pdm-4ch report's "Checked and OK" for
  those sheets (LMR51610, TPS7B91, ISO1044, LED sinks, switch inputs) therefore carries over, and so do its findings V2, V3,
  V6, V8 and V9.
- **Heat budget.**
  - 2 × 12.5 A → 71 °C, 2 × 15 A → 87 °C, 2 × 20 A → 137 °C, matching design-notes §4a.
  - The shunt at 15 A dissipates 0.23 W of its 3 W rating (C2903470, Milliohm HoJLR2512-3W-1mR-1 %).
  - The TPS48110 itself dissipates ≈ 20 mW (IQ 613 µA × 28 V).
- **Invariants.**
  - 1: the hardware path holds, with the start-up delay in H7.
  - 2: no relays.
  - 9: no 3.3 V on J5.
  - 10: all analog inputs on ADC1.

## Not checked

- The JLCPCB/EasyEDA footprints of C17556513 (DGX), C501507 (TDSON-8) and C2903470 (2512 shunt) against the KiCad ones. The
  shunt's Kelvin land and pulse/overload rating are part of this.
- Maker datasheets for SS510B, MMBT3904 and BAT54S (hongjiacheng). I used only JLCPCB attributes and the standard SOT-23
  pinouts.
- The TPS48110 INP pull-down value and the internal structure between GND and VS (H3 mechanism).
- The tolerance of V(SNS_WRN) at 25 mV, which the datasheet does not give.
- The BSC030N08NS5 package drawing against KiCad's TDSON-8-1 pad by pad. KiCad's footprint is Infineon-referenced.
- The bilge pump start current and real load capacitances (Q1).
- J10, J11 and H1/H2 have no footprints, and J5 is a 2.54 mm header. These wait for `/system mechanical`.
- Anything on a PCB, and any measurement.

<!-- findings:begin -->
```json
[
  {
    "id": "H1",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-hc2",
    "location": "hc_channel x2: R113/R213 RIWRN 47k, C105/C205 CTMR, Q13/Q23 OT sensor; ARCHITECTURE HC2 budget",
    "summary": "Hardware breaker at about 24-26 A (146 ms) and OT trip at 140-160 C at the sensor leave about 18-24 A unprotected in hardware; heat budget gives Tj 137-143 C at 20 A and 169 C at 22 A against MOSFET Tj max 150 C, so only firmware protects when the ESP32 runs.",
    "fix": "Lower IOC towards the rating (RIWRN 68k -> about 17.5 A, check bilge pump start current) and/or require a documented external breaker <= 15-18 A per output plus a firmware soft fuse.",
    "class": "big",
    "reason": "Changes channel protection and the ARCHITECTURE HC2 budget; affects safety-relevant outputs (bilge forced run).",
    "touches": ["protection", "budget", "decision:8", "safety"]
  },
  {
    "id": "H2",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-hc2",
    "location": "hc_channel x2: R104/R204 (PU 10 ohm), PD direct, R103/R203 RISCP 4.7k",
    "summary": "MOSFETs switch fully on in under 1 us, so a load with more than about 50-100 uF input capacitance probably exceeds the 71-91 A short-circuit threshold for longer than 4-5 us; the channel then stays off for 3.8 min (estimate, UNVERIFIED).",
    "fix": "Gate slew control per TPS4811-Q1 section 8.3.2.1 (R1 in PU path, C1 + 10 ohm at the gate, PD direct; e.g. 100k/3.9nF for about 20 A into 1000 uF), check MOSFET SOA; or state a maximum load capacitance. Combine with EMC E2.",
    "class": "big",
    "reason": "Changes gate drive and protection behaviour of the channel; new circuit function.",
    "touches": ["protection"]
  },
  {
    "id": "H3",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-hc2",
    "location": "root J10/D30 and hc_channel U11/U12 pins 20 (VS), 17/18 (CS-/CS+), 19 (ISCP)",
    "summary": "Reversed battery puts about -12...-30 V on TPS48110 VS/CS+/CS-/ISCP (abs max -1 V to GND); D30 SMCJ30CA is bidirectional and HC2 has no reverse protection; design-notes section 8 survival claim does not apply to HC2.",
    "fix": "Owner choice: reverse-polarity protection at J10 (ideal-diode + MOSFET), or a crowbar diode that blows the battery fuse (e.g. unidirectional D30 if its forward surge suffices), at minimum a keyed J10 plus README warning and corrected design-notes section 8.",
    "class": "big",
    "reason": "Protection topology change on the shared root sheet (battery input) or a new part.",
    "touches": ["protection", "shared-sheet", "connector"]
  },
  {
    "id": "H4",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-hc2",
    "location": "hc_channel x2: net DIODE (Q13/Q23, U11/U12 pin 10)",
    "summary": "No 1 nF bypass across the MMBT3904 remote sensor; TPS4811-Q1 section 9.6.1 says it must be placed (EMC E4 lists it only as a tune-in-test footprint).",
    "fix": "Add 1 nF 0402 (C1523, already on the BOM) from DIODE to GND at each MMBT3904; Kelvin emitter return to controller GND.",
    "class": "small",
    "reason": "Missing decoupling required by the datasheet on a board-only sheet; no new part, cost < 0.01 USD.",
    "touches": [],
    "cost_delta_usd": 0.01
  },
  {
    "id": "H5",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-hc2",
    "location": "tools/heat_budget.py PARTS['HC-2xBSC030']",
    "summary": "RDS(on) at 150 C is 11.2 mOhm in the tool; BSC030N08NS5 Diagram 9 max (5.35 mOhm) gives 2 x 5.35 + 1 = 11.7 mOhm; 15 A rises from 87 to 88 C, 20 A from 137 to 143 C; rating stands.",
    "fix": "Set (0.0070, 0.0117) with the datasheet reference in a comment.",
    "class": "small",
    "reason": "Tool input correction proven by the datasheet; no rating or decision change.",
    "touches": []
  },
  {
    "id": "H6",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-hc2",
    "location": "docs/design-notes.md sections 1 and 9",
    "summary": "Section 1 still names TPS48111-Q1 and 8-20 A; section 9 says an OUT voltage divider lets the PDM see float-driven runs, but no such divider exists and IMON cannot see that current.",
    "fix": "Correct both sections to the as-drawn design (TPS48110A-Q1, about 15 A; float runs only visible via SW3/SW4 if wired); OUT divider decision goes to Q2.",
    "class": "small",
    "reason": "Documentation only.",
    "touches": []
  },
  {
    "id": "H7",
    "kind": "finding",
    "severity": "INFO",
    "board": "pdm-hc2",
    "location": "hc_channel x2: C103/C203 CBST, C105/C205 CTMR",
    "summary": "First switch-on after power-up waits about 76-100 ms for the bootstrap (Eq. 1), also on the hardware switch path; overcurrent/short retry is about 3.8 min, reset by toggling INP.",
    "fix": "Record both times in design-notes section 4a and user documentation.",
    "class": "small",
    "reason": "Documentation only.",
    "touches": []
  },
  {
    "id": "H8",
    "kind": "finding",
    "severity": "INFO",
    "board": "pdm-hc2",
    "location": "root: IO3 (IMON2 via R212/R211)",
    "summary": "IO3 strapping pin is held low by the IMON2 network; harmless while EFUSE_STRAP_JTAG_SEL is not burnt (same as V11 on pdm-4ch).",
    "fix": "No hardware change; production must not burn that eFuse.",
    "class": "small",
    "reason": "Documentation only.",
    "touches": []
  },
  {
    "id": "Q1",
    "kind": "question",
    "severity": "INFO",
    "board": "pdm-hc2",
    "location": "hc_channel x2 (H2)",
    "summary": "Which HC2 loads have more than about 50 uF input capacitance (LED searchlight/work-light drivers, radios, inverter)? Sets whether gate slew control is needed and its inrush target.",
    "fix": "Owner lists the intended HC2 loads and their input capacitance or inrush.",
    "class": "big",
    "reason": "Only the owner knows the loads.",
    "touches": ["protection"]
  },
  {
    "id": "Q2",
    "kind": "question",
    "severity": "INFO",
    "board": "pdm-hc2",
    "location": "hc_channel x2 (H1, H6)",
    "summary": "Should the HC2 hardware breaker sit near the continuous rating (about 17.5 A) or stay at 25 A with a documented external breaker requirement? Is an OUT voltage divider (spare IO4/IO5) wanted for float-run detection, or are SW3/SW4 enough?",
    "fix": "Owner rules on breaker level and float-run sensing.",
    "class": "big",
    "reason": "Channel rating, safety-relevant output and possible pin-map change.",
    "touches": ["protection", "safety", "pin-map", "decision:8"]
  }
]
```
<!-- findings:end -->
