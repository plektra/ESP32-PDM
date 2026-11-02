# ESP32-PDM design notes

Status: schematic phase, 4-channel board (`hardware/pdm-4ch`). Last updated 2026-10-30.

These notes record the design decisions, the calculations behind them and what is still open.
Values marked *estimate* are engineering estimates, not measurements.

## 1. Goals and constraints

- Replace mechanical relays with solid-state outputs, switched both by ordinary panel switches
  and over NMEA 2000 (CAN); report switch and output state, current and faults on the bus.
- 12 V and 24 V systems; up to ~30 V while charging.
- Low cost is the guiding principle: JLCPCB PCBA, basic/preferred parts where possible,
  few unique extended parts.
- ESP32-S3 (NMEA 2000 / SensESP / Signal K ecosystem, Wi-Fi, OTA updates).
- Two boards, no relays (the point of the product is to replace them):
  - **4-channel** board, PROFET+24V per channel, fitted per build: BTT6050 (≈ 4 A) or BTT6010 (≈ 8 A).
  - **High-current** board (planned): smart high-side controller TPS48111-Q1 + external MOSFETs,
    ≈ 8–20 A per channel (bilge pumps 12 A, work lights, wipers; searchlight see §4).
- Installed in an enclosed location, in a vented 3D-printed enclosure. Two mounting styles:
  DIN rail (PCB perpendicular to the rail, 1–2 module widths) and flat (wall/ceiling).
- Engine-room ambient up to 40 °C.

## 2. Architecture

| Block | Sheet | Notes |
|---|---|---|
| Controller | root | ESP32-S3-MINI-1-N8, native USB (no USB-UART bridge) |
| Power | `power-usb` | LMR51610 buck (4–65 V in) → 3.3 V, diode-OR with USB VBUS, 60 V PTC, SMAJ30CA |
| NMEA 2000 | `can` | ISO1044 isolated CAN, L78M05 5 V linear regulator (DPAK) from NET-S (was TPS7B91, §8.3), SMAJ18CA, PESD2CAN |
| Panel inputs | `analog_sw` | Protected direct switch inputs, LED drivers |
| Output channels | `channel` (×4) | BTT6050-1ERA per channel |
| Battery input | root | J10, SMCJ30CA surge clamp |

Pin use (ESP32-S3, 4-channel): IN drive IO6–IO8 and IO11, current sense IO2–IO5 (ADC1), switch state IO14/IO15/IO16/IO21,
panel LED sinks IO38–IO41, VBAT_SENSE IO10 (ADC1), NTC IO9 (ADC1), DEN IO33, variant ID IO1 (ADC1), CAN IO17/IO18, USB IO19/IO20.

Variant ID (`MOD_ID`, IO1): 10 kΩ pull-up R29, variant resistor R42 to GND. 4-channel = 10 kΩ (1.65 V).
Proposed table: 1-channel 2.2 kΩ (0.59 V), 2-channel 4.7 kΩ (1.05 V), 4-channel 10 kΩ (1.65 V);
0 V and 3.3 V are treated as faults.

## 3. Output channel: BTT6050-1ERA / BTT6010-1ERA (PROFET+24V)

The BTT6050-1ERA, BTT6030-1ERA and BTT6010-1ERA are pin-compatible (same pin table, PG-TDSO-14, cooling
tab = VS; JLCPCB uses the same footprint for all three). Each channel is populated per build:

| Option | Part | RDS(on) | Datasheet IL(NOM) | Rating in our enclosure* | kILIS | Min. current limit | Price |
|---|---|---|---|---|---|---|---|
| Standard | BTT6050-1ERA (C534868) | 50 mΩ | 4.5 A | ≈ 4 A | 1500 | 38 A | 1.28 $ |
| High current | BTT6010-1ERA (C534858) | 10 mΩ | 9 A | ≈ 8 A | 3900 | 90 A | 3.19 $ |
| (not used) | BTT6030-1ERA (C534863) | 31 mΩ | 6 A | ≈ 5 A | 2200 | 60 A | 2.72 $ |

\* heat budget, 40 °C, vented, 2 oz; BTT6030 is dominated by BTT6010 (+0.47 $ for ~60 % more current).
RIS 680 Ω suits all parts (≈ 2.0 V at 4.5 A for BTT6050, ≈ 1.4 V at 8 A for BTT6010); the firmware
stores kILIS per channel. Values below are for the BTT6050 unless noted.

Source: Infineon BTT6050-1ERA datasheet Rev 1.00 (2019-03-09).

| Item | Value | Note |
|---|---|---|
| RDS(on) | 50 mΩ typ | 24 V-system part, VS max 48 V, load dump rated 65 V with RGND |
| Nominal load current | 4.5 A (TA = 85 °C) | |
| Current limit | 38–56 A, internal | **not adjustable**: wiring must be fused (see §8) |
| Current sense | IIS = IL / kILIS, kILIS ≈ 1500 (±25 % at 0.5 A) | RIS 680 Ω → ~0.45 V/A, 4.5 A ≈ 2.0 V |
| IS fault current | 6–40 mA | clamped by BAT54S to 3V3/GND behind RSENSE 10 kΩ |
| Logic thresholds | VIN(L) ≤ 0.8 V, VIN(H) ≥ 2 V (to device GND) | |
| Cooling tab | **VS** | shared VS copper area works as the common heatsink |
| JLCPCB | C534868, ~1.28 $ | footprint `ESP32-PDM:Infineon_PG-TDSO-14_ThermalVias` |

External parts per channel follow the datasheet application BOM: RIN = RDEN = RSENSE = 10 kΩ,
CSENSE 100 pF, COUT 10 nF, CVS 100 nF/100 V, ZGND = resistor + diode (22 Ω + DSK16 Schottky; the
datasheet uses 27 Ω + BAS21). The Schottky keeps the device ground shift at ≈ 0.35–0.5 V once the channel is on
(IGND 4.8 typ / 9 mA max, P_4.2.5).

**Hardware switch path margin at low voltage (T-0042, Q-0034; corrected 2026-11-02).** The earlier "~0.4 V margin" did
not hold at the bottom of the input range. Chain: SWIN → 10 k / 4.7 k divider (Thevenin 0.32 × SWIN behind 3.2 kΩ,
zener D20–D23) → BAT54C (≈ 0.15–0.2 V) → RIN R101 (IIN(H) ≤ 25 µA, P_8.4.5 → ≤ 0.25 V) → IN; thresholds VIN(H) ≥ 2.0 V,
VIN(L) ≤ 0.8 V to device GND (P_8.4.2). Worst-case figures (BAT54C 0.2 V, full IIN, ground shift 0.35–0.5 V):

| Case | Node | IN − GND before turn-on | IN − device GND once on | With RIN 4.7 k (fallback) |
|---|---|---|---|---|
| SWIN 10.5 V, 3V3 down (R30 into the IO14 ESD diode ≈ 0.5 V) | ≈ 2.67 V | ≈ 2.2 V (≥ 2.0: turns on) | ≈ 1.7–1.9 V (below VIN(H) min) | ≈ 2.35 V / ≈ 1.85–2.0 V |
| SWIN 10.5 V, 3V3 up (IO14 high-Z) | ≈ 3.2–3.35 V (zener knee, UNVERIFIED) | ≈ 2.8 V | ≥ ≈ 2.25 V (margin ≈ 0.25 V) | ≥ ≈ 2.4 V |
| Battery 10.5 V via D55 (SWIN 9.8–10.1 V), 3V3 down | ≈ 2.5–2.57 V | ≈ 2.05–2.1 V (margin ≈ 0.05 V) | ≈ 1.55–1.75 V | ≈ 2.17–2.24 V / ≈ 1.7–1.9 V |
| Battery 10.5 V via D55, 3V3 up | ≈ 3.13–3.23 V | ≈ 2.7 V | ≥ ≈ 2.18 V (margin ≈ 0.15 V) | ≥ ≈ 2.3 V |

So with the 3.3 V rail down the datasheet guarantees turn-on at SWIN ≥ 10.5 V (and at a 10.5 V battery behind D55,
thinly), but once the channel is on and its ground lifts, IN − device GND sits between VIN(L) max and VIN(H) min: the
datasheet does not guarantee that the channel stays on there. It probably does (the real threshold lies between 0.8 and
2 V, hysteresis ≈ 250 mV), but this is unproven. With the 3.3 V rail up the margin is ≈ 0.15–0.25 V. From 12 V upwards
the margin is ample. D55 (§5) is upstream of SWIN, so at a given SWIN nothing changes; it costs 0.3–0.7 V of battery
voltage (0.70 V is the 1 A maximum, the only VF limit in the DSK16 datasheet; ≈ 0.3–0.4 V typical at the ≈ 30–60 mA
panel current; the low-current VF is UNVERIFIED). Owner ruling Q-0034: no circuit change now; **measure IN − GND on the
prototype** at SWIN 10.5 V (3V3 removed and present, channel on, with and without D55's drop); if it is short, the
planned fix is RIN R101–R401 → 4.7 kΩ (halves the IIN drop). The other option (the shared divider) is an owner decision.
`UNVERIFIED`: the BZT52C3V3 knee below 1 mA.

The footprint is drawn from the datasheet package outline (Figure 53): lead pads 1.6 × 0.6 mm at
x = ±2.6 mm (0.47 mm clearance to the 2.65 × 6.4 mm exposed pad), 10 × 0.3 mm thermal vias,
bottom-side copper pad, 51 % paste coverage in six windows between the via rows (no paste over a via, T-0066).
Checked against the package drawing and the JLCPCB/EasyEDA footprint on 2026-11-02: see §8.4.

## 4. Heat budget

Run `tools/heat_budget.py` (see `--help`). Model: channel loss I²·RDS(on)(Tj), enclosure air rise
P_total · R_box, junction rise P_channel · RthJA, solved together.

Assumptions (*estimates* until a prototype is measured): vented enclosure with the PCB vertical
(chimney airflow), R_box 0.6 K/W (4-ch) / 0.9 K/W (2-ch, 1 module width), RthJA 40 K/W per switch
with 2 oz copper (50 K/W with 1 oz), 0.6 W for the ESP32/regulator/LEDs, RDS(on) at datasheet max
rising linearly to 150 °C.

**`--p-other` with the panel interface (T-0047, 2026-11-02).** The 0.6 W default covers the ESP32, regulators and status
LEDs only. On the 4-ch board at VS 30 V with all four panel switches closed and all four panel LEDs lit, the panel
interface (`analog_sw`, values after T-0068) adds ≈ 1.6 W:

| Part | Per line | × 4 |
|---|---|---|
| Switch loads R3/R4/R7/R8 4.7 k at SWIN ≈ 29.6 V (behind D55) | 0.19 W | 0.75 W |
| R34–R37 10 k + D20–D23 + R38–R41 (node ≈ 3.2 V, ≈ 2.6 mA) | 0.08 W | 0.31 W |
| LED sinks Q3–Q6 + R50–R53 + R19… (5 mA, (29.6 − 2 − 2.33) V across Q) | 0.14 W | 0.55 W |
| D55 (≈ 56 mA × ≈ 0.4 V) and F4 (≈ 56 mA² × 1.4 Ω) | – | 0.03 W |

Total **p_other ≈ 2.2 W** (the validator's estimate was 2.1 W). `tools/heat_budget.py --p-other 2.1` and `--p-other 2.2`
both give 4 × BTT6050 at 4 A → enclosure air 45.2–45.3 °C, **Tj ≈ 101 °C** (100 °C with 0.6 W): the 4 A rating stands.
Use `--p-other 2.2` for 24 V installations with a busy panel. The tool's default is unchanged (tools/ is outside this
package).

| Variant | Switch | Ambient | Copper | Continuous per channel (Tj ≤ ~110 °C) |
|---|---|---|---|---|
| 4-ch | BTT6050-1ERA | 40 °C | 2 oz | **4 A** (Tj ≈ 100 °C) |
| 4-ch | BTT6050-1ERA | 40 °C | 1 oz | 3.5 A (4 A → 120 °C) |
| 4-ch | BTT6050-1ERA | 50 °C | 2 oz | 3.5–4 A (4 A → 113 °C) |
| 2-ch | BTT6050-1ERA | 40 °C | 2 oz | **4 A** (Tj ≈ 99 °C) |
| 4-ch mixed | 2 × BTT6010 @ 8 A + 2 × BTT6050 @ 4 A | 40 °C | 2 oz | OK (Tj 89–101 °C) |
| 4-ch | 4 × BTT6010 @ 9 A | 40 °C | 2 oz | marginal (Tj 107–117 °C, 12 W total) |
| 4-ch | BTT6030 @ 6 A | 40 °C | 2 oz | too hot (Tj 135 °C) → ≈ 5 A |

Findings that drove the design:
- Spreading the heat over separate packages matters more than the lowest RDS(on): four single
  BTT6050s beat two dual BTT6030-2ERAs.
- A sealed printed box limits a 4-channel board to ~2.5–3 A per channel. Vents are required.
- A metal base plate was rejected: risk of bridging DC negative to a steel hull, and cost.
- Above ~8 A per channel: the high-current board (§4a). Very large loads (hydraulic backup pump, ~100 A)
  stay on their own contactor/breaker outside the PDM.
- At high total current the shared supply path dominates: 36 A through 4 mΩ is 5 W. Keep the battery
  terminal + VS copper ≤ 2 mΩ and rate the input terminal for ≈ 40 A; output terminals ≥ 10 A.

Layout rules from the budget: switches spread out and away from the ESP32; large VS copper on both
layers around the cooling tabs, stitched with vias; 2 oz copper; vents at bottom and top; continuous
current rating printed on the label; firmware warns or sheds load from measured current (and an NTC,
when an ADC pin is freed).

## 4a. High-current board `pdm-hc2` (2 channels)

Schematic: `hardware/pdm-hc2` (controller, power, CAN and input sheets shared with `pdm-4ch`; channel sheet
`hc_channel.kicad_sch` ×2). Variant ID R42 = 4.7 kΩ (1.05 V). Inputs 1–2 drive channels 1–2 in hardware; inputs 3–4
are sense-only (e.g. float-switch runs). IMON → IO2/IO3 (ADC1), FLT_I/FLT_T → IO34–IO37.

Per channel (source: TI TPS4811-Q1 datasheet SLUSEE5E):

| Part | Value | Purpose |
|---|---|---|
| TPS48110AQDGXRQ1 (C17556513) | – | controller: OV/UVLO, two-level overcurrent, IMON, remote temperature (DIODE), auto-retry |
| 2 × BSC030N08NS5 (C501507) | 80 V, 3 mΩ | back-to-back, common source: blocks back-feed (bilge float switch powering the pump while the channel is off) |
| RSNS | 1 mΩ 2512 3 W (C2903470) | 25 mV at 25 A; Kelvin-connect CS+/CS− at layout |
| RSET | 100 Ω | VS → CS+ |
| RIWRN | 47 kΩ | overcurrent (circuit breaker) ≈ 25 A: 11.9 × RSET / (RSNS × IOC) |
| RISCP + 1 nF | 4.7 kΩ | fast short-circuit ≈ 80 A: ISC × RSNS / 15.6 µA − 464 |
| CTMR | 10 µF | overcurrent time 82 µA·t/1.2 → ≈ 146 ms; auto-retry 22.7·10⁶ × CTMR ≈ 3.8 min |
| RIMON | 12 kΩ | gain 0.9 × RIMON / RSET = 108 → 25 A = 2.7 V; 10 kΩ + BAT54S clamp + 1 nF to the ADC |
| UVLO/OV divider | 1 MΩ / 100 kΩ / 39 kΩ | UVLO ≈ 9.7 V, OV cut-off ≈ 34.5 V |
| CBST | 1 µF / 50 V | > Qg(total) / 1 V = 152 nF |
| RG | 10 Ω | PU → gate (turn-on slew); PD drives the gate directly |
| MMBT3904 | – | temperature sensor between the MOSFETs (overtemperature → FLT_T, auto-retry 512 ms) |
| SS510B | 100 V 5 A | freewheel diode for motor loads |

Heat (`tools/heat_budget.py --part HC-2xBSC030 --rth-ja 20 --r-box 0.9`, estimate, 40 °C, vented):
2 × 12.5 A → Tj ≈ 71 °C; 2 × 15 A → 87 °C; 2 × 20 A → 137 °C (too hot). **Continuous rating ≈ 15 A per
channel.** The hardware breaker (25 A / 146 ms) allows motor starts; continuous protection comes from the
temperature sensor and the firmware soft fuse.

Notes and open points:
- **Searchlight 21 A** needs lower-RDS(on) MOSFETs (e.g. onsemi NTMFS5C612NL C348543, ≈ 1.5–2 mΩ; check
  that its SO-8FL land fits the TDSON-8-1 footprint) → estimated Tj ≈ 90–100 °C at 21 A.
- **Halogen inrush** (≈ 10–15× for tens of ms): the 80 A fast trip would stop a cold 500 W lamp. Options: an
  LED searchlight, or ISCP disabled (R_ISCP position fitted as 0 Ω to CS−) after verifying MOSFET pulse SOA and
  short-circuit energy with the 146 ms timer.
- Terminals for ≥ 25 A per output and ≈ 50 A battery input; 2 oz copper; footprint
  `Texas_DGX0019A` drawn from TI's land-pattern example (verify against JLCPCB before ordering).
- **Timing the user sees (T-0059, 2026-11-02; TPS4811-Q1 SLUSEE5E p. 8, 18, 23):**
  - *First switch-on after power-up* waits for the bootstrap capacitor: Eq. 1 TDRV_EN = CBST × V(BST_UVLOR) /
    I(charge pump) = 1 µF × 7.6 V / 100 µA ≈ **76 ms** (typ); with the minimum 80 µA charge-pump current ≈ 95 ms,
    and with CBST tolerance up to ≈ 100 ms. This applies to the hardware panel-switch path too (the controller,
    not the MCU, waits). Later switchings are immediate while VS stays up.
  - *Turn-on edge:* unchanged for now (RG 10 Ω, no slew control, sub-µs). Gate slew control (Q-0043) is on hold:
    the SOA check in the T-0070 report shows that 20 A into 1000 µF is outside the BSC030N08NS5 SOA (one-way
    question to the owner). The ramp time will be recorded here once the slew values are settled.
  - *Overcurrent/short-circuit retry:* Eq. 9 tRETRY = 22.7 × 10⁶ × CTMR = 22.7 × 10⁶ × 10 µF ≈ 227 s ≈
    **3.8 min** in auto-retry mode. The datasheet names toggling INP or EN/UVLO (or VS below POR) as the reset for
    latch-off mode (p. 24); that an INP toggle also cuts the auto-retry wait short is **not stated** in the
    facts read (UNVERIFIED) – check it on the prototype, then note the result here and in the README.
  - *No PWM on HC2 outputs* until switching loss and SOA are measured on the bench (owner ruling Q-0001).

## 5. Physical switch inputs and long leads

Per input (sheet `analog_sw`): SMAJ30CA at the connector → 4.7 kΩ 1206 load (contact wetting,
2.5 mA at 12 V / 6.4 mA at 30 V) → 10 kΩ 1206 series → node with 4.7 kΩ, BZT52C3V3 and 470 nF →
BAT54C diode-OR into the channel IN. The node sits at ~3.2 V for any input 10.5–30 V; the EN threshold
is ~7.5–8 V at the switch; τ ≈ 1.5 ms (3.2 kΩ × 470 nF; T-0012). The input works without the 3.3 V rail. 10 kΩ series resistors
feed the node to the ESP32 (limits back-feed into an unpowered ESP32 to ~0.3 mA).

Keeping long leads from acting as antennas:
- Filter every external line at the connector (TVS capacitance + series R + RC); no unfiltered line
  enters the board.
- Keep loops small: the switch supply and the switch return in the same cable (twisted pair or
  multicore). The panel connector J5 provides a fused switch supply SW_SUPPLY so the whole loop runs
  inside one cable (decision 17).

Panel connector J5 (decision 17), 10 poles:

| Pin | Signal | At the connector |
|---|---|---|
| 1–4 | SWIN1–4: switch from SW_SUPPLY | SMAJ30CA, 4.7 k load, 10 k + divider (above) |
| 5 | SW_SUPPLY = VS via PTC F4 (1812L050/60GR, same part as F1) and Schottky D55 (DSK16) | SMAJ30CA + 100 nF/100 V |
| 6–9 | LED_K1–4: panel LED cathode (anode to SW_SUPPLY) | SMAJ30CA, 100 Ω, 1 nF at the collector |
| 10 | GND (cable drain / spare) | – |

- LED sinks: GPIO (IO38–IO41) → 1 k → base, 10 k base pull-down, MMBT5551 (V_CEO 160 V, above the
  SMAJ30CA clamp of ≈ 48 V; BC817's 45 V was not), 470 Ω emitter. V_B ≈ 3.3 × 10/11 = 3.0 V,
  V_E ≈ 2.33 V → I_LED ≈ 5.0 mA independent of the supply (10.5–30 V), the LED colour and the cable length
  (≥ 10 m is fine; the panel has no LED resistor). Dissipation at 30 V ≈ (30 − 2 − 2.3) × 5 mA ≈ 0.13 W;
  R_θJA 416 K/W (JCET datasheet) → T_j ≈ 50 °C enclosure air + 54 K ≈ 104 °C (< 150 °C). LEDs are off
  when the 3.3 V rail is down. PWM: low frequency (100–200 Hz); the 1 nF collector capacitor slows edges.
- Switch-supply budget ≈ 50 mA (4 × 6.4 mA switch load at 30 V + 4 × 5 mA LEDs); F4 holds 500 mA.
- **Debounce (T-0012, Q-0006, 2026-11-02):** C14–C17 470 nF/10 V X5R 0402 (CL05A474KP5NNNC, C47339, preferred) on the
  node after R34–R37 (the node is held ≤ ≈ 3.3 V by the zener, so 10 V is ample). τ ≈ 3.2 kΩ × 470 nF ≈ 1.5 ms
  (corner ≈ 100 Hz), was 0.32 ms: contact bounce of a few ms no longer chatters the hardware path. The X5R
  capacitance at ≈ 3 V bias is lower than nominal (no bias curve in the Samsung catalogue: UNVERIFIED), so the real τ
  is somewhat below 1.5 ms. Turn-on and turn-off at the IN pin come ≈ 2–4 ms later than before; no effect on the
  loads. Cranking dips (100s of ms) are far longer than τ: the filter does not ride through them.
- **Switch supply diode D55 (T-0049, Q-0040, 2026-11-02):** DSK16 (C22466351, preferred, already on the BOM as D2/D3/D11,
  and on the 4-ch board also as D101–D401) in series after F4: F4.2 → anode, cathode → SW_SUPPLY (J5.5, D54, C54), so D54 still
  clamps the J5.5 line at the connector. Ratings (DSK16 datasheet, `docs/part-facts/C22466351.md`): VRRM 60 V,
  IF(AV) 1 A ≥ F4's I_trip 1.0 A (I_hold 0.5 A), IFSM 25 A (8.3 ms). Reverse stress: a reversed battery puts ≈ 24–30 V on
  it; a +48 V clamp on J5.5 with a normal battery ≤ 48 V. (A reversed battery *and* a simultaneous surge on the panel
  cable would exceed 60 V: double fault, not covered.) With the battery reversed the panel LEDs now see only the
  Schottky leakage (typ 10–20 µA, max 0.2 mA at 60 V, 25 °C) instead of ≈ 24–30 V reverse from a stiff source.
  Cost: 0.3–0.7 V less on SW_SUPPLY (≈ 0.3–0.4 V typical at the panel current; 0.70 V is the datasheet maximum at 1 A).
  The hardware ON threshold seen from the battery rises from ≈ 8 V to ≈ 8.3–8.7 V; the low-voltage margin is in §3.
  Dissipation ≤ 0.03 W.
- **Failure mode (safety), T-0012/T-0049:** navigation lights and the bilge forced-run can be panel-switched.
  - With the 470 nF: the hardware path reacts ≈ 2–4 ms later; there is no new failure mode. A shorted C14–C17 holds that
    input off, as a shorted 100 nF did before.
  - With D55, at low battery: panel inputs drop out ≈ 0.3–0.7 V earlier. On a 12 V boat the panel-switched outputs
    go off below ≈ 8.5 V at the battery during cranking (was ≈ 8 V); 24 V systems are not affected. At a 10.5 V battery the
    turn-on is still guaranteed by the datasheet but thinly, and staying on with the 3.3 V rail down is not
    guaranteed (§3: prototype measurement, RIN 4.7 k fallback).
  - D55 open: all panel switches and LEDs of the board dead, the same symptom as a tripped F4. The proposed SW_SUPPLY
    sense (decision 21) sits on the J5.5 side and would catch it too.
  - D55 shorted: back to the old behaviour (the panel works; the LEDs are unprotected against reversal).
  - A hard short in the panel cable drives the F4 fault current through D55 until F4 trips (≤ 0.15 s at 8 A). Whether
    D55 survives the highest fault currents (IFSM 25 A for 8.3 ms) is UNVERIFIED. A diode that fails open gives the
    "D55 open" case above.
  - A competent person must review this before installation.
- **Failure mode (safety):** a short in the panel cable (or at a panel switch) trips F4; all panel
  switches of that board then do nothing until the short is cleared, while NMEA 2000 control keeps
  working, but the panel LEDs go dark too. As drawn the firmware **cannot** tell a tripped F4 from "all
  switches off"; a sense line (SW_SUPPLY → 100 k/10 k divider → spare GPIO IO12, two basic resistors) would
  let it alert (decision 21, proposed). Outputs that must
  keep working from the panel (bilge forced run, navigation lights) need a competent person's review; an
  installer can also feed the switches from a separate fused supply (the inputs accept any 10.5–30 V).
- Panel LED behaviour (decision 20, open): LED on = output on, blinking = fault; alerts to Signal K where
  they can be acknowledged and muted. Details in `/system firmware`.
- Outputs: run each load's return with its feed; if outputs are PWM-dimmed, use a low frequency
  (100–200 Hz).
- Firmware: qualify inputs (e.g. 20 ms stable), average ADC readings.

## 6. Power modes

| Mode | Wi-Fi | CAN | Panel LEDs | DEN (diagnostics) | Wake |
|---|---|---|---|---|---|
| Active | on | on | full / dimmed | pulsed only while sampling IS (never held high) | – |
| Eco | power-save or off | on | dimmed / off | pulsed, slower sampling | immediate |
| Sleep | off | periodic listen window | off | off | local switch, timer, wake broadcast |

- Entered by a command over NMEA 2000 (or Signal K); local switches always work and can wake the node.
- In deep sleep the ESP32 cannot receive CAN or Wi-Fi; the node wakes every few seconds and listens
  briefly, and the central controller repeats its wake command for ~10 s.
- Output state is held through deep sleep with RTC GPIO hold (4-ch drives IO6–IO8 and IO11 are RTC GPIOs, IO0–IO21; the panel LED pins IO38–IO41 are not, so the LEDs are off in deep sleep). A full reset or
  OTA update drops outputs for ~0.3 s unless the physical switch is on.
- DEN low puts the BTT6050s in standby (µA range) – this saves more than the ESP32 sleep itself.

### 6.1 DEN policy and the IS sense resistor (T-0041/T-0052, Q-0033/Q-0041, 2026-11-02)

**Rule for `/system firmware` (owner ruling Q-0041):** DEN (IO33, shared by the four BTT6050s) is **not** held high in
Active mode. Firmware raises DEN only for the time needed to sample IS (ADC settling after DEN rise, then the
conversion), then drops it. If a sample reads full scale (IS clamped near 3V3, i.e. a fault current IIS(FAULT) is
flowing), DEN is dropped at once and the channel is reported as faulted/open load; DEN is not raised again for that
channel until the retry interval. DEN low is also the standby state (above). Firmware requirement list: see the end of
this section.

**Why (BTT6050 datasheet Rev 1.00 p. 30, Table 9, P_7.5.7):** with DEN high and a fault, IS sources
IIS(FAULT) = 6 / 15 / 40 mA (min/typ/max) into RIS. An unconnected output floats up in OFF and also reads as
open load in OFF (VOUT > VS − VOL(OFF), p. 27, 30).

| IIS(FAULT) | P in RIS 680 Ω (I²R) | 0603 (0.1 W) | 1206 (0.25 W) |
|---|---|---|---|
| 6 mA | 24 mW | ok | ok |
| 15 mA | 153 mW | **over** | ok (61 %) |
| 40 mA | 1.09 W | **over** | **over** |

Hardware: R103/R203/R303/R403 are now 680 Ω **1206**, 0.25 W, 1 %, C17975 (UNI-ROYAL 1206W4F6800T5E). No *basic* 1206
680 Ω exists at JLCPCB (all 25 parts are extended), so the cheapest extended one was taken; the 0603 C23228 is no
longer used on the board. The value is unchanged, so the sense scaling (≈ 0.45 V/A) is unchanged. The 1206 covers the
typical fault current continuously. The 40 mA maximum (1.09 W) is **not** covered by hardware – by ruling that case is
covered by the firmware rule above (IS is clamped at ≈ 3.3 V by D102, but the current still flows through RIS until DEN
is dropped). A 2 W part was not fitted (not asked for). If the owner wants the 40 mA case covered in hardware, RIS would need a rating of about 1.5–2 W (a larger, costlier part): open point.

**OUT pull-down, DNP (R106/R206/R306/R406, auto):** 47 kΩ 0603 (C25819, basic), OUT to GND, **not fitted**. Value from
BTT6050 datasheet §7.3.3.2 (p. 27) and the application BOM Table 11 (p. 47): "RPD can be used to pull VOUT to 0 V;
otherwise the OUT pin is floating", example 47 kΩ. The datasheet gives no RPD formula (the diagnostic pages carry
a "Target Data Sheet Rev. 0.11" header – recheck against the Infineon site before ordering). Checks: P at 30 V =
30² / 47 k = 19 mW (19 % of the 0603's 0.1 W; the part's voltage rating is 75 V); load of 0.64 mA from OUT when the
output is on at 30 V, irrelevant against the load; worst-case leakage IL(OFF)_150 21 µA × 47 k = 1.0 V, far below
VS − VOL(OFF) (≥ 4 V), so an unconnected output no longer reads as open load in OFF once fitted. Fit it only if
unconnected outputs must not be flagged; with it fitted open-load-in-OFF detection no longer works for a really open
load (the output is held at 0 V), open-load in ON is unaffected.

**Failure mode (RIS and DEN):** a lost or stuck-high DEN with a faulted channel only overheats RIS (one 1206
resistor, ≈ 1 W at the 40 mA maximum, a few seconds to hot) – it cannot switch an output on or off, so no output
fails to a hazardous state; a failed-open RIS reads as zero current (a fault would not be reported). These are not
safety outputs on their own, but the sense path is used for the bilge-pump jam detection, so a competent person
reviews this before installation.

**Firmware requirements (for `/system firmware`):**
1. DEN pulsed only while sampling IS, never held high in Active mode (Q-0041); in Eco sampled less often.
2. Drop DEN immediately on a full-scale IS reading (fault current flowing); report the channel; retry later.
3. Nothing else may hold DEN high (bootloader/reset state: IO33 pulls down; check at firmware design).
4. Allow the settling time after the DEN rise and after IN falls (tsIS(FAULT_OL_OFF), datasheet Fig. 26) before
   diagnosing open load in OFF.

## 7. Mechanics and connectors

- DIN: PCB perpendicular to the rail, ~85 × 55 mm, target **1 module width** (17.5 mm). Terminal rows
  run front-to-back along the top and bottom edges, so the pole count is set by depth, not width.
  Provisional rating 3.5 A per BTT6050 channel in 1 module width until a prototype is measured.
- Pluggable terminal blocks on the top and bottom edges. A 4-channel board needs ~20 poles
  (power 2, outputs 4, panel 9, CAN 4–5): ≈ 10–13 poles per edge at 3.81 mm pitch. Exact parts are
  chosen at the PCB stage.
- Flat mounting: same PCB and housing with a flat-mount foot instead of the DIN clip.
- Enclosure material: ASA (PETG softens at ~80 °C).

## 8. Protection and limitations

**Not protected against load dump.** Onboard TVS diodes clamp short transients (ESD, switching
spikes) only. A load dump (battery disconnected while an alternator is charging, or a BMS disconnect)
carries hundreds of joules and must be handled at system level: alternator protection device,
field-disconnect battery switch, or a BMS that signals the charge source before disconnecting. Like
most marine electronics, this device relies on that system-level protection.

- **Not a circuit breaker.** The BTT6050 protects itself (current limitation, thermal shutdown), but
  its limit is 38–56 A. Every output wire must be protected by a fuse or breaker sized to the wire
  (ABYC E-11 / ISO 10133). The firmware adds a programmable "soft fuse" from the current sense.
- MOSFET switches usually fail short (output stuck on). Current sensing lets the firmware detect
  "current while commanded off" and raise an alarm, but cannot switch the load off.
- Reverse battery (`pdm-4ch`, T-0050, 2026-11-02): the BTT6050 with its ground network (22 Ω + DSK16) is rated for a
  reverse supply only within VS(REV) ≤ 28 V, t < 2 min, RL ≥ 12 Ω (≤ ≈ 2.3 A at 28 V), TA 25 °C (datasheet P_4.1.2).
  Within those limits the switches survive. Heavier loads are not covered: at the 4 A rating the reverse current
  through the body diode dissipates ≈ 0.61 V × 4 A ≈ 2.4 W (VDS(REV), P_6.6.2), above PTOT 1.6 W (P_4.1.22), and the
  ground diode does not change that. There the battery fuse has to clear. The loads see reverse voltage in every case.
  The panel LEDs on J5 are protected by D55 in the SW_SUPPLY feed (§5, T-0049): with a reversed battery only the
  Schottky leakage (≤ 0.2 mA) reaches them.

### 8.1 Battery input J10: TVS, capacitors, ferrite position (decision 26, T-0064, 2026-11-01)

Root sheet, the same on both boards (controller part):

| Ref | Part | Net | Purpose |
|---|---|---|---|
| D30 | SMCJ30CA (C19077607, preferred) | VBAT_IN–GND | surge clamp at the terminal (unchanged part, now on the terminal side of FL30) |
| C30 | 1 µF/100 V X7R 1206, Samsung CL31B105KCHNNNE (C13832, extended) | VBAT_IN–GND | HF return at the terminals |
| FL30 | ferrite / CMC position, **DNP** | VBAT_IN–VS | decided at the pre-compliance scan (decision 28) |
| JP30 | copper bridge (net tie, no part) | VBAT_IN–VS | keeps VS connected while FL30 is not fitted; cut only when FL30 is fitted |
| C31 | 100 µF/63 V Al electrolytic, Ymin VKMD1001J101MV (C487384, extended) | VS–GND | bulk at J10 |

HC2 only (`hc_channel`, ×2): C106/C206, the same 100 µF/63 V at each channel's VS, so HC2 has 3 × 100 µF.
4-ch only (`channel`, ×4): C104–C404, the same 1 µF/100 V at each BTT6050 VS tab, next to C103 (100 nF).

Part facts:
- Ymin VKM series datasheet (catalogue pp. 178–180): −55…+105 °C, tan δ 0.14 at 63 V (120 Hz), life
  10 000 h at 105 °C for ≥ φ8, AEC-Q200. 100 µF/63 V = 8 × 10 mm, ripple 902 mA rms (105 °C, 100 kHz);
  frequency factor 0.50 at 120 Hz → 451 mA rms. ESR is not specified. From tan δ, ESR(120 Hz) ≤ 0.14/(2π·120·100 µF)
  ≈ 1.9 Ω; it is lower at 100 kHz, but the datasheet gives no figure. Body dimensions (B = C = 8.3, A = 3.4, H = 0.9,
  E = 3.1 mm) are the standard 8 × 10 size of KiCad `CP_Elec_8x10`. Check that footprint against the JLCPCB/EasyEDA
  footprint before ordering.
- Samsung CL31B105KCHNNNE: part-numbering code 31 = 1206, B = X7R, 105 = 1 µF, K = ±10 %, C = 100 V (Samsung MLCC
  catalogue, "Part Numbering System"). The capacitance drops under DC bias at 24–29 V, but this was not checked
  against a curve. JLCPCB has no soft-termination 1 µF/100 V part in stock.
- No basic or preferred SMD electrolytic ≥ 63 V and no basic or preferred 1–2.2 µF/100 V MLCC exist at JLCPCB
  (searched 2026-11-01). Both parts are extended: 2 new unique extended parts, each with a loading fee per order.

Why 63 V: D30 clamps at 48.4 V (below); 63 V leaves 30 % margin. 100 V for the ceramics (decision 30).

Energy at turn-off (estimate; cable 1 µH/m as in the Infineon VBAT(SC) set-up, 5 m loop → 5 µH):
- HC2 fast trip 80 A: E = ½·L·I² = 16 mJ. With only C31 (ideal C): √(28.8² + 2E/C) = 33.9 V. With 3 × 100 µF (HC2): 30.6 V.
- 4-ch, BTT6050 current limit up to 56 A: 7.8 mJ → 31.4 V with 100 µF.
- The ESR of the electrolytics (unspecified, ≤ 1.9 Ω at 120 Hz) means the first microseconds of an 80 A step are
  taken by C30, D30 and the VS-tab ceramics. The electrolytics take the slower part, so D30 conducts less often.
  Three electrolytics in parallel on HC2 also divide the ESR by three. That is the reason for the extra bulk on HC2 (EMC finding E3).

Ripple: no PWM on HC2 (decision 25). For 4-ch PWM at 100–200 Hz the battery cable (≈ 20 mΩ + j·6 mΩ)
has far lower impedance than 100 µF (8 Ω at 200 Hz), so C31 carries a small share. The 451 mA rms rating at 120 Hz is
not a limit.

Life: Arrhenius doubling per 10 K. At 65 °C board temperature (40 °C engine room + enclosure + switches nearby,
assumption) 10 000 h × 2⁴ ≈ 160 000 h (≈ 18 years continuous). The cheaper fallback, Semtech CS1J101M-CRG10
(C116430, 0.13 USD, 2000 h at 105 °C, 10 × 10.5 mm), gives ≈ 3.7 years at the same temperature, so it was not chosen.

Ferrite position: no 40–50 A ferrite or CMC footprint exists in the libraries (the KiCad Ferrite_THT bead has a
0.8 mm hole). FL30 therefore has no footprint yet. If the scan asks for it, a snap-on ferrite on the battery cable is the
first, board-free option. If a board part is needed, choose it and its footprint at the PCB phase. JP30 (net tie)
is a copper link that must be as wide as the VS copper on both layers. It is listed DNP because nothing is placed, but it
conducts. If FL30 is ever fitted, 4-ch output surges (OUT → PROFET body diode → VS) reach D30 only through FL30.
In that case reconsider fitting the output TVS footprints D103–D403.

Cost per board at 10 units (part prices at 1–49 pcs): 4-ch C31 0.22 + C30 0.065 + 4 × C104 0.26 = 0.54 USD;
HC2 C31 0.22 + C30 0.065 + 2 × C106 0.44 + 2 × SMAJ33CA 0.057 = 0.78 USD. On top of that comes the extended-part
loading fee (about 3 USD per unique part per order, check the quote) for C487384 and C13832, i.e. ≈ 0.6 USD per
board at 10 units. The bulk capacitor alone is 0.22 + 0.30 ≈ 0.52 USD per board, at the ~0.5 USD limit of the
work package.

**D30 vs the BTT6050 (T-0017, recorded, no change).** SMCJ30CA (hongjiacheng datasheet): VRWM 30 V, VBR
33.3–36.8 V at 1 mA, VC 48.4 V at IPP 31 A (10/1000 µs). BTT6050-1ERA: VS max 48 V (P_4.1.1), VS(LD) 65 V for load
dump with RI = 2 Ω, set up per ISO 7637-1 (P_4.1.3). D30 reaches 48.4 V only at its full rated pulse current, for the
duration of the pulse. That is 0.4 V over the static limit, but well inside VS(LD), so short clamp excursions are
covered. The new VS-side parts are rated above the clamp: C31 63 V, C30/C104 100 V.

### 8.2 Output surge protection (decision 27, T-0064)

**HC2: D103/D203 SMAJ33CA (C19077549, preferred, 0.028 USD) from each OUT to GND at J11.** Hongjiacheng datasheet:
VRWM 33 V, VBR 36.7–40.6 V at 1 mA, VC 53.3 V at IPP 7.5 A (10/1000 µs), 400 W, IR 1 µA at VRWM.
- Float-switch case: the float switch puts the battery (up to 28.8 V while charging, ≈ 30 V maximum per decision 3)
  on OUT while the channel is off. That is below VRWM 33 V (leakage ≤ 1 µA). SMAJ30CA (VRWM 30 V) would have no margin.
- Ratings on OUT: Q12/Q22 drain (BSC030N08NS5, VDS 80 V) and D102/D202 (SS510B, 100 V). The clamp of 53.3 V is
  below both. Negative surges are clamped first by the SS510B freewheel diode.
- With the channel on, a VS surge also appears on OUT. D30 (VBR from 33.3 V) breaks down before D103 (VBR from 36.7 V).
- PCB rule: TVS next to the J11 terminal, its GND return a short, wide path straight to J10.2 (not through the
  logic ground), as in EMC layout rule 2.

**Failure mode (bilge forced-run output).** A TVS fails short when it is overstressed (for example a load dump on the
pump wire, decision 12). With D103 shorted:
- PDM channel on: the TPS48110 breaker / fast trip turns the channel off and reports the fault; the output-wire fuse
  may blow.
- Float switch running the pump: the TVS sits **outside** the back-to-back MOSFETs, so the float circuit feeds back
  through the PDM output wire into the short. The float circuit keeps working (invariant 8) **only if the PDM leg
  has its own fuse, between J11 and the point where it joins the float circuit, that opens before the float-circuit
  fuse** (fuse selectivity: PDM-leg fuse clearly smaller than the float fuse, or a slower float fuse). This must go
  into the README installation rules next to the external breaker ≤ 15–18 A of decision 39.
- Open TVS: no function change, only the output surge protection is lost.
- A competent person must review this output and its fusing before installation.

**4-ch: D103–D403 SMAJ30CA (C19077548, preferred), DNP footprint per output at J11.** The outputs are protected by the
PROFET: a positive surge goes through the body diode to VS and D30. A negative surge is clamped at VS − VDS(AZ), with
VDS(AZ) 66/70/75 V (BTT6050 P_5.5.5); HBM 4 kV on OUT. VS copper from the switches to D30 must be wide.
Before fitting D103–D403: during inductive turn-off the PROFET drives OUT to VS − VDS(AZ), for example 24 − 66…75 =
−42…−51 V. The bidirectional SMAJ30CA (VBR 33.3–36.8 V) would then conduct and take the demagnetisation energy instead of
the PROFET clamp. For inductive loads, either check that energy against the TVS rating (400 W, 10/1000 µs) or fit a
unidirectional SMAJ30A (cathode to OUT), which freewheels the load instead.

### 8.3 Shared supply, USB and fuse parts (T-0065, decisions 30–32, 2026-11-02)

Shared sheets `power-usb`, `can` and `analog_sw`, the same on both boards.

**PTC interrupt rating (T-0018, Q-0011): check FAILED, nothing changed.** LUTE 1812L series datasheet (Rev. 2020, p. 3),
1812L050/60GR: I_hold 0.50 A, I_trip 1.00 A, V_max 60 V, **I_max 40 A** ("maximum fault current device can withstand
without damage at rated voltage"), R_min 0.150 Ω, R1max 1.4 Ω, trip ≤ 0.15 s at 8 A. Note 3 of the datasheet says the
part must not be used where I_max can be exceeded in a fault condition. Prospective current for a hard short directly
behind the PTC, with the ruling's formula: I = 30 V / (R_min + ≈ 10 mΩ cable) = 30 / 0.160 ≈ **188 A**, 4.7 × I_max.

| PTC | Fed from | Short location that reaches I_max | Comment |
|---|---|---|---|
| F1 | VS (battery) | D1/C1/U3 input on the board (cracked MLCC, failed TVS) | battery source, only the J10 cable in series |
| F3 | NET-S (J4.2) | D10/FB2 side on the board, or J4 terminals | N2K supply is 9–16 V and fused at the power tee; drop-cable resistance (≈ 0.1–0.3 Ω) usually limits the current well below 188 A, but this is not guaranteed |
| F4 | VS (battery) | J5.5 terminal or the first metres of the panel cable | **safety-relevant**: F4 feeds the panel switches (bilge forced run, navigation lights) |

Even 30 V across the PTC plus 0.3 Ω of wiring gives 30 / 0.46 ≈ 65 A > 40 A. JLCPCB has 1812 60 V PTCs listed with
I_max 100 A (TECHFUSE mSMD050-60V C70113, JDT ASMD1812-050-60V C427396: parametric listing only, datasheets not yet
read). They are better, but still below 188 A for a short right at the board. This is a protection problem, so it goes to the
owner (one-way). Options are listed in the T-0065 report: a 100 A-rated 1812 part plus a series resistance per PTC, or
accept and document the residual risk. **F2 was therefore not swapped to 1812L050/60GR** (the Q-0019 swap depended on this check).

Failure mode if I_max is exceeded: the PPTC can be damaged (cracking, arcing, charring) instead of tripping cleanly;
the datasheet warns of arcing or fire beyond the maximum ratings. A competent person must review the F1/F3/F4 protection
before installation.

**L3 swaps (T-0026, Q-0019).**

| Ref | Old | New | Check | Result |
|---|---|---|---|---|
| FB1, FB2 | BLM18AG601SN1D 0603 | Sunlord GZ2012D601TF 0805, C1017 (basic) | Sunlord GZ catalogue (rev. 2024-06-19) p. 3: 600 Ω ± 25 % at 100 MHz, DCR ≤ 0.30 Ω, I_r 500 mA. FB1 carries VBUS only when the board runs from USB: buck input ≈ 3.3 V × 0.47 A / (0.85 × 4.6 V) ≈ 0.40 A peak < 500 mA; drop ≤ 0.12 V. FB2 carries the CAN-side current (≤ 77 mA). | adopted |
| F2 | SMD0805B050TF | 1812L050/60GR | depends on the PTC I_max check above | **not adopted** |
| D4–D6 | DOWO PESD0402V05 (polymer, clamp 40 V at 8 kV contact, trigger 450 V, 0.05 pF; DOWO datasheet p. 2) | hongjiacheng H5VL10B, DFN1006-2L, C7420372 (preferred) | H5VL10B Rev 2.0: V_RWM 5 V, V_BR 5.6–8 V at 1 mA, V_C ≤ 8 V at 1 A and ≤ 10 V at 5 A (8/20 µs), C_J 15 pF typ / 18 pF max (0 V, 1 MHz), IEC 61000-4-2 ±25 kV contact/air, I_R ≤ 0.1 µA. 18 pF max is inside the ≤ 15–20 pF budget for a USB full-speed line. The clamp is far lower than the polymer part's 40 V and the ESD rating higher, so protection is stronger. D4 on VBUS: V_RWM 5.0 V against VBUS 5.25 V max (USB 2.0); V_BR min 5.6 V, so leakage stays small. | adopted, footprint `Diode_SMD:D_SOD-882` (1.0 × 0.6 mm, 0.65 mm pitch = DFN1006-2) |
| U6 | TPS7B91050 SOT-23-5 | ST L78M05ABDT-TR, DPAK, C58069 (basic) | see below | adopted, footprint `Package_TO_SOT_SMD:TO-252-2` |

L78M05ABDT (ST DS0425 Rev 24):
- V_I abs max 35 V (V_O 5–18 V). The SMAJ18CA D10 clamps NET-S at 29.2 V; 35 / 29.2 = 1.20 (5.8 V margin), and there is
  no operating voltage above 16 V on NMEA 2000.
- Pinout (Fig. 2, DPAK): 1 = INPUT, tab = GND, 3 = OUTPUT. This matches the KiCad `Regulator_Linear:L7805` symbol
  (1 IN, 2 GND, 3 OUT) and the `TO-252-2` footprint (pad 2 = tab). The symbol sits on the old U6 pin points: IN and GND
  nets unchanged, OUT now pin 3.
- I_d (quiescent) 6 mA max, ΔI_d ≤ 0.8 mA with line/load. **LEN:** ISO1044 I_CC2 (TI SLLSFB0A §6.9) 70 mA max bus dominant,
  9 mA recessive, 38 mA max at 1 Mbit/s 50 % square wave. NET-S current = I_CC2 + regulator ground current. Normal
  traffic: 38 → 44.8 mA, LEN 1 before and after. Continuous dominant (fault case): 70 → 76.8 mA, LEN 2 before and
  after. **The load class does not change**, but the margin to 50 mA in the normal-traffic case is only 5 mA. A different
  transceiver (T-0030 CA-IS3050G) must be rechecked against it.
- Dropout 2 V: NET-S minimum 9 V − D11 (≈ 0.4 V) − F3/FB2 (< 0.05 V) ≈ 8.5 V > 7 V needed. V_O 4.8–5.2 V over
  temperature (ISO1044 V_CC2 4.5–5.5 V).
- Capacitors: the datasheet's test circuit uses C_I 0.33 µF and C_O 0.1 µF. C13 was raised from 0.1 µF to **1 µF/50 V
  X7R 0805 (C28323, basic)**. C12 1 µF + C11 0.1 µF on the output are kept.
- Heat: (16 − 0.4 − 5) V × 45 mA ≈ 0.48 W normal traffic (same as the TPS7B91 plus 0.07 W from I_d). R_θJA 100 K/W (DPAK,
  Table 2) gives +48 K, so ≈ 98 °C at 50 °C enclosure air (T_J max 125 °C). Copper under the tab lowers that.
- **DPAK area:** body ≈ 6.6 × 6.1 mm plus leads, footprint ≈ 10.4 × 6.7 mm, against ≈ 3 × 3 mm for SOT-23-5. This is for
  `/system mechanical` (1-module DIN width).

**USB service port (T-0014, Q-0008).**
- README: USB-C is a service port only (battery-powered laptop or USB isolator).
- J3 shield is no longer tied to GND directly: new net `USB_SHIELD` → R13 1 MΩ 1206 (C17927, basic) ‖ C18 4.7 nF/1 kV
  X7R 1206 (Yageo CC1206KKX7RCBB472, C107198, extended; Yageo voltage code C = 1 kV) to GND, plus R14 0 Ω 0603 (C21189)
  **DNP** as the hard-tie option. Choice (auto): RC fitted, 0 Ω DNP. 1 MΩ bleeds static charge; 4.7 nF gives an RF/ESD
  return (Z ≈ 0.3 Ω at 100 MHz, ignoring ESL) but blocks the 50 Hz/DC loop to shore PE. No basic 4.7 nF part ≥ 250 V exists
  (searched 2026-11-02), so this is one new extended part. 1206 sizes keep creepage for ESD on the shield.
- TLP/clamp check of the ESD part left by step 2 (H5VL10B): **no TLP curve is published**. Clamp data are 8/20 µs only
  (≤ 8 V at 1 A, ≤ 10 V at 5 A, Fig. 4). Extrapolating the 0.5 Ω dynamic resistance to the 8 kV contact first peak (≈ 30 A)
  gives roughly 20–25 V for the first nanoseconds (estimate, not datasheet). That is far below the replaced part's 40 V.
  The remaining margin comes from the ESP32-S3's own pin ESD structures. If TLP data are wanted before ordering, a part with
  published TLP (e.g. a USBLC6-2 type) is the alternative.

**Buck (T-0011, Q-0005).** TI SLUSEY1B §8.2.2.6: C_IN ≥ 2.2 µF rated about twice V_IN, plus 0.1 µF close to the pins.
§7.3.5/8.2.2.7: C_BOOT 0.1 µF ≥ 16 V.
- C19 100 nF/100 V X7R 0805 (C28233, basic, same part as C54) from VIN to GND, next to C1. Place it at the VIN/GND pins.
- R43 0 Ω 0402 (C17168, basic) in series with C2 between CB and C2. Fitted as 0 Ω. If the scan shows SW-edge noise, a
  few-ohm value slows the high-side turn-on (check that the boot capacitor still recharges).
- R44 10 Ω 1206 (C17903) + C20 100 pF/100 V C0G 0603 (Samsung CL10C101JC8NNNC, C296717) from SW to GND, **both DNP**.
  Snubber loss if fitted: C·V²·f = 100 pF × 24² × 1.1 MHz ≈ 63 mW (≈ 0.1 W at 30 V), within the 0.25 W 1206 rating. Values are
  set at the pre-compliance scan from the measured ring frequency. LMR51610YDBVR is kept (decision 30).

**Capacitor ratings (T-0015, Q-0009).**
- C1 2.2 µF/50 V → **2.2 µF/100 V X7R 1206, Samsung CL31B225KCHSNNE (C170101, extended)**. No basic or preferred 2.2 µF
  ≥ 63 V exists (searched 2026-11-02), so this is one new extended part. Two C13832 (1 µF/100 V, already in the BOM) would
  give only 2 µF, below TI's 2.2 µF minimum. MLCC on a battery-derived net: keep it away from board edges and screws (a
  cracked MLCC is a short behind F1, see the PTC finding).
- C50–C53 1 nF 0402 50 V → **1 nF/2 kV X7R 1206, FH 1206B102K202NT (C9196, basic)**. A 100 V basic part does not exist in 1 nF;
  this is the only basic part ≥ 63 V. Larger footprint (1206).

**L1 second sources (T-0022, Q-0015).** All three have the same figures:

| Part | LCSC | L | DCR typ/max | I_sat | I_rms | Size / land (a, b, c) | Source |
|---|---|---|---|---|---|---|---|
| Sunlord SWPA6045S8R2MT (fitted) | C96963 | 8.2 µH ± 20 % | 0.043 / 0.056 Ω | 3.90 A | 2.60 A | 6.0 × 6.0 × 4.5 max; 2.8/1.7/5.7 | SWPA catalogue rev. 2025-05-08 pp. 2, 13 |
| Sunltech SLW6045S8R2MST | C47018494 | 8.2 µH ± 20 % | 0.043 ± 30 % (≤ 0.056) | 3.90 A | 2.60 A | 6.0 × 6.0 × 4.5 max; 2.8/1.7/5.7 | Sunltech SLW6045S Rev.02 pp. 1–2 |
| cjiang FNR6045S8R2MT | C168074 | 8.2 µH ± 20 % | 0.043 / 0.056 Ω | 3.90 A (4.30 typ) | 2.60 A (2.80 typ) | 6.0 × 6.0 × 4.5 max; 2.8/1.7/5.7 | FNR catalogue pp. 2, 16 |

Both alternates are approved, with the same footprint `Inductor_SMD:L_Sunlord_SWPA6045S`. SLW6045S8R2MST has no EasyEDA
footprint at JLCPCB (`has_easyeda_footprint` false), so map it to the SWPA land at order time. Stock on 2026-11-02:
SWPA 1231, SLW 1512, FNR 1677. Recheck before ordering.

**Cost (estimate, 1–49 pcs prices):** fitted parts added or changed: C1 0.133, C18 0.018, C19 0.016, R13 0.004,
R43 0.001, C13 0.042, C50–C53 4 × 0.023, FB1/FB2 2 × 0.020, D4–D6 3 × 0.0065 (was 3 × 0.0133), U6 0.207 (was 0.21).
That is roughly +0.3 USD per board in part price. Unique extended parts: −PESD0402V05, −TPS7B91 (and the ferrite, which had
no LCSC code before) removed; +C170101, +C107198 added. That is about one loading fee fewer per order (check the quote).

### 8.4 Custom footprints: TDSO-14 paste, LMR51610 on SOT-23-6 (T-0066, Q-0036/Q-0037, 2026-11-02)

**PG-TDSO-14 (`ESP32-PDM:Infineon_PG-TDSO-14_ThermalVias`, BTT6050/BTT6010).** The six 1.0 × 1.6 mm paste windows sat
on the ten open 0.3 mm thermal vias (x = ±0.6, y = 0/±1.2/±2.4), so paste would wick into the vias and leave voids under
the VS tab (validator 2026-10-30). Owner ruling Q-0036: move the paste between the vias, no plugged vias.

New paste: four windows 2.55 × 0.6 mm centred at y = ±0.6 and ±1.8 (between the via rows) and two 2.55 × 0.5 mm at
y = ±2.95 (beyond the outer rows, ending at the pad edge), corner ratio 0.1. Area 4 × 1.53 + 2 × 1.275 = 8.67 mm² of
the 2.65 × 6.4 = 16.96 mm² exposed pad = **51 %** (was 9.6 mm², 57 %, over the vias). Every window edge is ≥ 0.30 mm
from a via centre: 0.15 mm from the drill and 0.05 mm from the 0.5 mm via pad. The webs between windows are 0.6 mm (the via
rows). Checked by a scratch script (every window against every via) and a `kicad-cli fp export svg` plot. Across the 0.12 mm stencil,
area ratio = 1.53 / (6.3 × 0.12) ≈ 2.0, well above 0.66. 51 % is at the low end of the 50–70 % range; the vias set the
limit. If X-ray or first-article boards show a thin or voided tab joint, widen the windows to 2.65 mm (53 %) or
order plugged vias (owner's call, money).

Recheck against the Infineon package drawing (BTT6050-1ERA datasheet Rev 1.00, Fig. 53, PG-TDSO-14): body 3.9 × 8.65,
pitch 1.27, lead width 0.4 ± 0.05, span 6.0 ± 0.2, foot 0.67 ± 0.25, exposed pad 2.65 × 6.4 ± 0.1, pin 1 next to the
index mark, 1–7 on one side and 8–14 opposite. Lead pads 1.6 × 0.6 at x = ±2.6 cover x = 1.8…3.4; the foot lies within
1.98…3.1 at all tolerances, so the pads cover it with ≥ 0.18 mm heel and ≥ 0.3 mm toe; side overhang 0.1 mm; gap between pads
0.67 mm; clearance to the exposed pad 0.475 mm. The exposed pad copper is 1:1 with the package pad. **Drawing and pads
agree.**

JLCPCB/EasyEDA footprint of C534868 (`PG-TDSO-14_L8.6-W3.9-P1.27-LS6.0-BL-EP`, read from the EasyEDA API): lead pads
1.8 × 0.6 oval at ±3.0 (x = 2.1…3.9), exposed pad 6.4 × 2.65 (same), pin 1 at the same corner after a 90° rotation
(EasyEDA draws the package horizontally: expect a 90° rotation correction in the CPL at the first order). Their pads
reach 0.5 mm further out and start 0.3 mm further in from the heel; ours give a larger heel fillet and more clearance to the
exposed pad. Both cover the foot, so we keep ours.

**LMR51610 U3 (`power-usb`, both boards).** The custom `ESP32-PDM:LMR51610` (1.81 × 0.61 pads at ±1.15) is replaced
by the stock `Package_TO_SOT_SMD:SOT-23-6` (owner ruling Q-0037), checked first:

| Source | Pad (along × across) | Pad centre x | Pad extent x | Pitch | Pin order |
|---|---|---|---|---|---|
| TI DBV0006A land pattern (LMR51610 DS SLUSEY1B p. 33) | 1.1 × 0.6 | ±1.30 | 0.75…1.85 | 0.95 | 1–3 left top→bottom, 4–6 right bottom→top |
| KiCad `SOT-23-6` (KiCad 8 lib) | 1.325 × 0.6 | ±1.1375 | 0.475…1.80 | 0.95 | same |
| JLCPCB/EasyEDA C22427220 `SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL` | 1.072 × 0.532 | ±1.149 | 0.61…1.69 | 0.95 | same (drawn rotated 90°) |

Package (DBV0006A p. 32): span 2.6–3.0, foot 0.3–0.6, so the foot lies within 0.7…1.5 from the centre. All three lands cover it.
KiCad's pad ends 0.05 mm short of TI's toe and reaches 0.275 mm further under the body (IPC-7351 nominal; TI note 6
allows IPC-7351 variants). The JLCPCB pad lies entirely inside it. Pin numbering is the same as TI's: 1 CB, 2 GND, 3 FB,
4 EN, 5 VIN, 6 SW (Table 5-1). U3's footprint field (instance and cached symbol) and the library symbol default
(was the non-existent `ESP32-PDM-BASE:LMR51610`) now point to `Package_TO_SOT_SMD:SOT-23-6`. Nothing else used
`LMR51610.kicad_mod`, so it was removed from `lib/`. This also cleared U3's `lib_symbol_mismatch` warning on both boards.

## 9. Open items

- [x] Panel cable: fused switch-supply output, constant-current LED sinks, TVS on every line (§5, decision 17)
- [x] Battery-voltage measurement (IO10) and NTC near the switches (IO9) (decision 18)
- [ ] Failure modes and alert handling: LED blink codes, Signal K alerts with acknowledge/mute (decision 20)
- [ ] Terminal blocks and enclosure layout for DIN / flat mounting (§7)
- [x] Verify the PG-TDSO-14 footprint against the package drawing and the JLCPCB/EasyEDA footprint (§8.4, T-0066)
- [ ] Per-output fuse strategy (on board vs. in the installation)
- [x] Standard population: all four BTT6050 (Q-0032, T-0040); heavy loads go on HC2. BTT6010 only where > 4 A, mixed builds ordered together (§3, pdm-4ch STATUS/README)
- [ ] High-current board: MOSFET option for 21 A, halogen inrush decision, terminals (§4a)
- [ ] Bilge pumps (Vega: SEAFLO 01 Series 3500 GPH, 24 V model SFBP2-G3500-01: 8.0 A rated, 12.5 A max
      draw per the product page; current rises with pumping head; start-up and jammed-impeller current not
      given). BTT6010 at 8 A → Tj ≈ 86 °C, at 10 A ≈ 123 °C, at ≥ 11 A thermal shutdown: a pump working
      hard must not be cut off, so it goes on a high-current channel. Wiring per manual: float switch and
      manual switch in parallel to the pump; the PDM channel replaces the manual switch. Back-to-back
      MOSFETs block back-feed when the float switch runs the pump; an OUT voltage divider lets the PDM see
      float-driven runs. Timed overcurrent reports a jammed impeller instead of blowing a fuse.
      Previous note: owner reported 12 A per pump (2026-10-30), consistent with the 12.5 A max draw.
      Original analysis: too much for one PROFET channel
      (BTT6010 @ 12 A → Tj ≈ 186 °C) → high-current board. Automatic float-switch circuit wired directly
      (always on); manual forced run on a high-current channel (works without the ESP32 via the physical
      switch); run monitoring via an auxiliary sense input on the pump feed
- [ ] Auxiliary sense-only inputs (1-2, same protected input circuit, spare GPIO) for pump-running /
      float-switch state
- [ ] Load list with nameplate currents (VHF, FM radio, wipers incl. park circuit, bilge pumps, work lights)
- [ ] Update Symbols from Library in KiCad (USB-C symbols; LMR51610 done in T-0066; Q3–Q6 use the BC817 symbol with value
      MMBT5551 – same SOT-23 pinout 1 B / 2 E / 3 C – keep that when updating)
- [ ] Remaining checks from the BOM audit: Kangnex CAN connector footprint, PESD2CAN pinout
