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
  - **High-current** board `pdm-hc2`: smart high-side controller TPS48110A-Q1 + back-to-back MOSFETs
    (BSC030N08NS5), ≈ 15 A continuous per channel, built-in breaker ≈ 17.5 A (bilge pumps 12 A, work lights,
    wipers).
- Installed in an enclosed location, in a vented 3D-printed enclosure. Two mounting styles:
  DIN rail (PCB perpendicular to the rail, 1–2 module widths) and flat (wall/ceiling).
- Engine-room ambient up to 40 °C.

## 2. Architecture

| Block | Sheet | Notes |
|---|---|---|
| Controller | root | ESP32-S3-MINI-1-N8, native USB (no USB-UART bridge) |
| Power | `power-usb` | LMR51610 buck (4–65 V in) → 3.3 V, diode-OR with USB VBUS, 60 V PTC, SMAJ30CA |
| NMEA 2000 | `can` | CA-IS3050G isolated CAN (was ISO1044, §8.5), L78M05 5 V linear regulator (DPAK) from NET-S (was TPS7B91, §8.3), SMAJ18CA, PESD2CAN; DNP CMC FL1 (0 Ω bridges R71/R72) and DNP Y-cap C70 |
| Panel inputs | `analog_sw` | Protected direct switch inputs, LED drivers |
| Output channels | `channel` (×4) | BTT6050-1ERA per channel |
| Battery input | root | J10, SMCJ30CA surge clamp |

Pin use (ESP32-S3, 4-channel): IN drive IO6–IO8 and IO11, current sense IO2–IO5 (ADC1), switch state IO14/IO15/IO16/IO21,
panel LED sinks IO38–IO41, VBAT_SENSE IO10 (ADC1), NTC IO9 (ADC1), DEN IO33, variant ID IO1 (ADC1), CAN IO17/IO18, USB IO19/IO20.

VBAT_SENSE full scale (decision 18 as amended by decision 38, T-0043): divider R60 220 k / R61 22 k (+ C60 100 nF),
ratio 22/242 = 1/11. The ESP32-S3 ADC is calibrated only for 0–2900 mV at 12 dB attenuation (datasheet v2.2,
Table 5-6), so full scale is 2.9 V × 11 ≈ **31.9 V, about 32 V** (not 33 V). 30 V still reads (2.73 V at the pin).

IO3 strapping pin (T-0051, T-0060): IO3 selects the JTAG source only when eFuse `EFUSE_STRAP_JTAG_SEL` is burnt. On
both boards IO3 is held low by the channel-2 current-sense network – pdm-4ch: IS2 via R204 10 k + RIS R203 ‖ R207 (2 × 1 kΩ = 500 Ω)
(≈ 10.5 k to GND); pdm-hc2: IMON2 via R212 10 k + R211 12 k (22 k to GND). With the eFuse unburnt (default) this is
harmless. **Firmware and production rule: never burn `EFUSE_STRAP_JTAG_SEL`.** JTAG stays on the built-in USB-Serial/JTAG.

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
RIS 500 Ω (2 × 1 kΩ, T-0107; see §6.1) suits all parts (≈ 1.5 V at 4.5 A for BTT6050, ≈ 1.0 V at 8 A for BTT6010); the firmware
stores kILIS per channel. Values below are for the BTT6050 unless noted.

Source: Infineon BTT6050-1ERA datasheet Rev 1.00 (2019-03-09).

| Item | Value | Note |
|---|---|---|
| RDS(on) | 50 mΩ typ | 24 V-system part, VS max 48 V, load dump rated 65 V with RGND |
| Nominal load current | 4.5 A (TA = 85 °C) | |
| Current limit | 38–56 A, internal | **not adjustable**: wiring must be fused (see §8) |
| Current sense | IIS = IL / kILIS, kILIS ≈ 1500 (±25 % at 0.5 A) | RIS 500 Ω → ~0.33 V/A, 4.5 A ≈ 1.5 V |
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

*Recheck with the 2 k + 2 k switch load (T-0105, Q-0048/decision 74, 2026-11-03).* The load R3+R45 … R8+R48 sits from
SWIN to GND, in parallel with the divider, so it does not enter the divider ratio or the thresholds above; it only adds
current through the source. At SWIN 10.5 V the load current rises from 2.23 mA (4.7 k) to 2.63 mA (4.0 k), +0.4 mA per
closed line, +1.6 mA with all four. Through F4 (≈ 1.4 Ω), D55 (ΔVF ≈ 0.04 V × ln(34/32) ≈ 2 mV) and ≈ 1.4 Ω of 10 m panel
cable (assumed 0.25 mm², supply and return) that costs ≤ ≈ 6 mV at SWIN, ≤ ≈ 2 mV at IN (× 0.32). The table stands: the
thinnest case (battery 10.5 V via D55, 3V3 down) stays ≈ 2.05 V before turn-on, ≥ VIN(H) 2.0 V.

The footprint is drawn from the datasheet package outline (Figure 53): lead pads 1.6 × 0.6 mm at
x = ±2.6 mm (0.47 mm clearance to the 2.65 × 6.4 mm exposed pad), 10 × 0.3 mm thermal vias,
bottom-side copper pad, 51 % paste coverage in six windows between the via rows (no paste over a via, T-0066).
Checked against the package drawing and the JLCPCB/EasyEDA footprint on 2026-11-02: see §8.4.

## 4. Heat budget

Run `tools/heat_budget.py` (see `--help`). Model: channel loss I²·RDS(on)(Tj), enclosure air rise
P_total · R_box, junction rise P_channel · RthJA, solved together.

Assumptions (*estimates* until a prototype is measured): vented enclosure with the PCB vertical
(chimney airflow), R_box 0.6 K/W (4-ch) / 0.9 K/W (2-ch, 1 module width), RthJA 40 K/W per switch
with 2 oz copper (50 K/W with 1 oz), 2.3 W `--p-other` default (ESP32/regulators/LEDs 0.6 W plus the panel interface, see below), RDS(on) at datasheet max
rising linearly to 150 °C.

**`--p-other` with the panel interface (T-0047, 2026-11-02).** The 0.6 W default covers the ESP32, regulators and status
LEDs only. On the 4-ch board at VS 30 V with all four panel switches closed and all four panel LEDs lit, the panel
interface (`analog_sw`, values after T-0068) adds ≈ 1.6 W (≈ 1.7 W with the T-0105 loads):

| Part | Per line | × 4 |
|---|---|---|
| Switch loads R3+R45 … R8+R48, 2 k + 2 k at SWIN ≈ 29.6 V (behind D55; T-0105, was 4.7 k: 0.19 W / 0.75 W) | 0.22 W (0.11 W per part) | 0.88 W |
| R34–R37 10 k + D20–D23 + R38–R41 (node ≈ 3.2 V, ≈ 2.6 mA) | 0.08 W | 0.31 W |
| LED sinks Q3–Q6 + R50–R53 + R19… (5 mA, (29.6 − 2 − 2.33) V across Q) | 0.14 W | 0.55 W |
| D55 (≈ 60 mA × ≈ 0.4 V) and F4 + R56 (≈ 60 mA² × 1.2 Ω, T-0118) | – | 0.03 W |

Total **p_other ≈ 2.2 W** (the validator's estimate was 2.1 W); **≈ 2.3 W since T-0105** (2 k + 2 k loads, +0.13 W):
`--p-other 2.3` gives 4 × BTT6050 at 4 A → enclosure air 45.4 °C, Tj ≈ 101 °C – the 4 A rating stands (run 2026-11-03).
The tool default is 2.3 W since T-0141. The table plus the 0.6 W base sums to 2.37 W; `--p-other 2.37` gives the same Tj ≈ 101 °C (run 2026-11-04). `tools/heat_budget.py --p-other 2.1` and `--p-other 2.2`
both give 4 × BTT6050 at 4 A → enclosure air 45.2–45.3 °C, **Tj ≈ 101 °C** (100 °C with 0.6 W): the 4 A rating stands.
The default covers 24 V installations with a busy panel (0.6 W until T-0085, 2.2 W until T-0141); give
`--p-other 0.6` for the controller alone.

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
- At high total current the shared supply path dominates. Since T-0121 pdm-4ch adds the reverse-battery blocker Q30 to this
  path (§8.6), since T-0158 AGM601LL (≤ 1.6 mΩ at 25 °C, ≈ 2.1 mΩ at its 16 A temperature, 2.9 mΩ at 150 °C). 16 A (decision
  103) through `--r-path 0.0069` = the 4 mΩ default + 2.9 mΩ is 1.8 W, and 4 × 4 A stays at Tj 102 °C. Keep the battery
  terminal + VS copper ≤ 2 mΩ and rate the input terminal for 16 A (decisions 103, 104; J10 is 30 A UL / 32 A IEC, §7);
  output terminals ≥ 10 A.

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
| RIWRN | 68 kΩ (C36871) | overcurrent (circuit breaker) ≈ 17.5 A: 11.9 × RSET / (RSNS × IOC) (§4a.2, decision 39) |
| RISCP + 1 nF | 4.7 kΩ | fast short-circuit ≈ 80 A: ISC × RSNS / 15.6 µA − 464 |
| CTMR | 10 µF | overcurrent time 82 µA·t/1.2 → ≈ 146 ms; auto-retry 22.7·10⁶ × CTMR ≈ 3.8 min |
| RIMON | 12 kΩ | gain 0.9 × RIMON / RSET = 108 → 25 A = 2.7 V; 10 kΩ + BAT54S clamp + 1 nF to the ADC |
| UVLO/OV divider | 1 MΩ / 100 kΩ / 39 kΩ | UVLO ≈ 9.7 V, OV cut-off ≈ 34.5 V |
| CBST | 1 µF / 50 V | > Qg(total) / 1 V = 152 nF |
| R1 (RG_PU) | 10 kΩ (C25744) | PU → gate, gate slew (§4a.3, T-0106) |
| C1 + R2 | 1 nF/2 kV 1206 (C9196) + 10 Ω (C25077) | gate → GND, sets the output ramp ≈ 0.7 V/µs (§4a.3) |
| RGATE_PD | 0 Ω (C17168) | PD → gate directly (footprint for a later turn-off resistor, decision 25) |
| MMBT3904 | – | temperature sensor between the MOSFETs (overtemperature → FLT_T, auto-retry 512 ms) |
| SS510B | 100 V 5 A | freewheel diode for motor loads |

Heat (`tools/heat_budget.py --channels 2 --part HC-2xBSC030 --rth-ja 20 --r-box 0.9 --r-path 0.002`, estimate,
40 °C, vented; RDS(on) path 11.7 mΩ at 150 °C per BSC030N08NS5 Diagram 9, T-0057):
2 × 12.5 A → Tj ≈ 73 °C; 2 × 15 A → 90 °C; 2 × 20 A → 145 °C (too hot; rerun 2026-11-03 with the then 2.2 W `--p-other` default, T-0106; the same Tj with 2.3 W, run 2026-11-04). **Continuous rating ≈ 15 A per
channel.** The hardware breaker (≈ 17.5 A / 146 ms, §4a.2) allows short motor starts; between 15 A and the breaker,
protection comes from the required external breaker (≤ 15–18 A) and the firmware soft fuse. The temperature sensor
(140–160 °C at the MMBT3904) is a backstop, not a continuous protection.

Notes and open points:
- Keyed plugs: J11 30 A UL / 32 A IEC, J10 for the 36 A battery input (decisions 95, 98); 2 oz copper; footprint
  `Texas_DGX0019A` drawn from TI's land-pattern example (verify against JLCPCB before ordering).
- **Timing the user sees (T-0059, 2026-11-02; TPS4811-Q1 SLUSEE5E p. 8, 18, 23):**
  - *First switch-on after power-up* waits for the bootstrap capacitor: Eq. 1 TDRV_EN = CBST × V(BST_UVLOR) /
    I(charge pump) = 1 µF × 7.6 V / 100 µA ≈ **76 ms** (typ); with the minimum 80 µA charge-pump current ≈ 95 ms,
    and with CBST tolerance up to ≈ 100 ms. This applies to the hardware panel-switch path too (the controller,
    not the MCU, waits). Later switchings are immediate while VS stays up.
  - *Turn-on edge (T-0106, §4a.3):* ≈ 50 µs gate delay, then the output ramps at ≈ 0.5–0.75 V/µs (≈ 40–57 µs
    for 0–30 V); not noticeable to the user.
  - *Overcurrent/short-circuit retry:* Eq. 9 tRETRY = 22.7 × 10⁶ × CTMR = 22.7 × 10⁶ × 10 µF ≈ 227 s ≈
    **3.8 min** in auto-retry mode. The datasheet names toggling INP or EN/UVLO (or VS below POR) as the reset for
    latch-off mode (p. 24); that an INP toggle also cuts the auto-retry wait short is **not stated** in the
    facts read (UNVERIFIED) – check it on the prototype, then note the result here and in the README.
  - *No PWM on HC2 outputs* until switching loss and SOA are measured on the bench (owner ruling Q-0001).

**1 oz copper, examined and not chosen (2026-11-06).** `tools/heat_budget.py --channels 2 --part HC-2xBSC030 --rth-ja 25 --r-box 0.9 --r-path 0.004`, assuming 25 K/W and double the path resistance, both channels loaded, 40 °C: 13 A → Tj 87 °C, 14 A → 96 °C, 15 A → 106 °C, 16 A → 118 °C, 17.5 A → 139 °C, 19.7 A → 182 °C. The 50 µF hot-start margin of 1.03 at 90 °C (§4a.3) would hold at about 13 A; scaling k gives about 0.93 at 14 A and 0.75 at 15 A. The breaker would also need RIWRN about 75 k: 15.9 A nominal, about 13.8–17.9 A scaled from the 68 k spread (UNVERIFIED). `pdm-4ch` on 1 oz: 4 × 3.5 A → 97 °C. The first-order saving is only about 71 $ with U1 machine-placed (decision 100). PCB quotes for 5 pieces at 100 × 65 and 100 × 75 mm: €36.43 with 2 oz and €4.72 with 1 oz. Economic PCBA is offered only on 1 oz (decision 99).

### 4a.1 Controller pin filtering (T-0071: T-0056, T-0005, T-0008; 2026-11-03, auto)

Source: TPS4811-Q1 SLUSEE5E, facts file `docs/part-facts/C17556513.md` (p. 7–10, 16, 37–40, Table 9-3, Fig. 9-18).
Refs are channel 1 / channel 2 (same sheet `hc_channel` ×2). All new fitted parts are already on the BOM; the
orchestrator adds no unique part.

| Ref | Value / LCSC | Node | Check |
|---|---|---|---|
| C107/C207 | 1 nF 0402 C1523, fitted | DIODE–GND, across MMBT3904 | 9.6.1 (p. 40): "a small 1000pF bypass capacitor **must** be placed in parallel with the MMBT3904". I(DIODE) 10/160 µA into the BJT (r_e ≈ 2.6 kΩ at 10 µA) → τ ≈ 3 µs, negligible for a thermal sensor |
| R114/R214 | RVS 100 Ω 0402 C25076, fitted | VS → VS_CTRL (U11/U12 pin 20) | Table 9-3: 100 Ω. I(Q) 613/700 µA typ/max (p. 8, GND-pin current; no separate IVS row, the charge pump current 80–126 µA is drawn from VS inside I(Q) – stated test condition EN = 2 V, so assumed) → drop **61/70 mV**, < 0.3 V. Even at a 6 V crank dip VS pin ≈ 5.9 V ≫ V(VS_PORR) 3.2 V max. The gate-drive peak (PU 3.75 A) comes from CBST, not VS. P = 49 µW |
| C102/C202 | CVS 2.2 µF/100 V X7R 1206 C170101 (T-0107, cost lever L8; was 1 µF C13832, before that 100 nF C28233 on VS), fitted | VS_CTRL–GND | Table 9-3 (p. 39): RVS 100 Ω, CVS 0.1–10 µF; no upper limit stated (facts file C17556513, §9.5). τ = 100 Ω × 2.2 µF = 220 µs (f_c 0.72 kHz; DC bias at 24–30 V leaves ≈ 1–1.5 µF, τ ≈ 0.1–0.15 ms), so the pin's 60 V/µs dV/dt limit cannot be reached through RVS. The DC drop (61/70 mV) does not depend on CVS. At power-up VS_CTRL follows VS with ≈ 0.2 ms delay, short against the EN/UVLO and CTMR times; on a fast VS dip the larger CVS holds VS_CTRL up longer (the purpose of Table 9-3's filter). Part already on the BOM (C1, C30), so pdm-hc2 no longer needs C13832 |
| C108/C208 | X cap 1 nF 0402 C1523, fitted | CS+ (CSP) – CS− (SNS) | CS+ is fed through RSET 100 Ω, CS− sits on the shunt: differential τ = 100 Ω × 1 nF = **0.1 µs** = 2.5 % of tSC 4 µs typ (5 µs max) and ≪ tOC 146 ms. Voltage across it ≤ 0.3 V (abs. max CS+–CS−) |
| C109/C209, C110/C210 | Y caps 100 pF/100 V C0G 0603 C296717, **DNP** | CS+–GND, CS−–GND | Timing passes (100 Ω × 100 pF = 10 ns), but they are **not matched in effect**: CS− has no series impedance (on the shunt), so C110 does nothing and C109 alone turns common-mode VS noise into a differential error of C_Y/(C_X+C_Y) ≈ 9 %. Fig. 9-18 uses them only with FB1/FB2 in both lines. DC offset from the caps is zero (ceramic, no DC current; V(OS_SET) ±200 µV unchanged). Fit them only together with balanced ferrites, at the pre-compliance scan (Q-0012) |
| C111/C211 | 1 nF 0402 C1523, fitted | EN/UVLO–GND | Table 9-3 CEN 1–1000 nF. Divider 1 MΩ/100 kΩ/39 kΩ; see the time table below |
| C112/C212 | 1 nF 0402 C1523, fitted | OV–GND | see below |
| C113/C213 | 1 nF 0402 C1523, fitted | IWRN–GND | Table 9-3 CIWRN 10 pF–100 nF. 47 kΩ × 1 nF = 47 µs vs tOC 146 ms (CTMR 10 µF): 0.03 %. Does not touch the short-circuit comparator (ISCP/CS−). 1 nF instead of the suggested 100 pF to reuse C1523; if CTMR is ever removed (tOC 25 µs), drop it to 100 pF |

UV/OV response (numeric step simulation of the RC ladder, both caps equal, threshold 1.18 V):

| Event | 1 nF (fitted) | 10 nF (rejected) |
|---|---|---|
| OV, VS step 24 → 48 V (TVS clamp) | 0.10 ms | 1.0 ms |
| OV, VS step 24 → 36 V | 0.30 ms | 3.0 ms |
| OV, VS step 12 → 36 V | 0.40 ms | 4.0 ms |
| UV, VS step 24 → 6 V | 0.21 ms | 2.1 ms |
| EN delay at power-up 0 → 24 V | 0.07 ms | 0.66 ms |

Criterion: the OV cut-off (34.5 V) must act well inside the shortest ISO 16750-2 load-dump pulse (40 ms). 1 nF keeps it
≤ 1 % (0.4 ms); 10 nF reaches 10 % (4 ms) – no clear margin, so 1 nF is fitted. 1 nF (≈ 1 Ω at 156 MHz) already
shorts VHF pick-up, which is what the EMC finding was about. Plus tPD(OV_OFF) 4 µs / tPD(UVLO_OFF) 6 µs max (p. 10).
Short ISO 7637 spikes (< 100 µs) no longer reach OV; they are clamped by D30 and the 300 µF on VS.

RVS pulse load: VS carries ≈ 300 µF of bulk (C31, C106, C206) and the SMCJ30CA, so its slew is slow; RVS sees at
most a fraction of a volt during transients. A full 24 V step would put ½ C ΔV² ≈ 0.3 mJ into the 0402 – UNVERIFIED
against the resistor's pulse rating, not expected in practice.

Layout (PCB phase): C107/C207 right at Q13/Q23, MMBT3904 emitter Kelvin-routed to U11/U12 GND (pin 6), not via the
power ground; C102/C202 and R114/R214 next to pin 20; C108/C208 across pins 17/18 at the IC; C111–C113 at their pins.

**Failure mode (safety; these filters sit on the breaker, short-circuit and UV/OV sensing of the bilge and navigation
outputs):** the 80 A short-circuit trip is slowed by ≈ 0.1 µs (C108) and the 25 A breaker by ≤ 47 µs on a 146 ms timer
– both inside the datasheet response. A shorted C108 (CS+ = CS−) blinds both current comparators: the channel keeps
running without breaker or short-circuit protection; only the fuse upstream and the temperature trip remain. A
shorted C111 holds EN low (channel off, fails safe-off – for the bilge pump this means **no pump**); a shorted C112 keeps
OV inactive (no over-voltage cut-off). A shorted C113 puts IWRN at GND = overcurrent protection off. A shorted
C102 or open R114 removes the controller supply (channel off). An open C107 only makes the temperature reading noisier.
Use X7R/C0G from the BOM only, no flex-sensitive placement near board edges or mounting holes. A competent person must
review these protection circuits before installation.

### 4a.2 Breaker level and OUT sense (T-0072: T-0053, T-0062; Q-0042/Q-0046, decision 39; 2026-11-03)

**Breaker (R113/R213 RIWRN 47 k → 68 k, 0402 1 % C36871, preferred).** TPS4811-Q1 SLUSEE5E Eq. 6 (p. 22–23):
RIWRN = 11.9 × RSET / (RSNS × IOC + V(OS_SET)), V(OS_SET) = 0 ± 0.2 mV (p. 9, p. 26). With RSET 100 Ω, RSNS 1 mΩ:
VSNS = 1190 / 68 k = 17.5 mV → **IOC ≈ 17.5 A** (nominal).
- Spread: the datasheet gives V(SNS_WRN) only at two settings (p. 9): 29.2/30.6/31.5 mV (39.7 k) and 8/10/12 mV
  (120 k). Interpolating the absolute error between them gives about −1.8/+1.6 mV at 17.5 mV (−10/+9 %,
  `UNVERIFIED`, no table row at 68 k). With 1 % RSET, RIWRN and RSNS: **IOC ≈ 15.2–19.7 A**.
- Timer unchanged: Eq. 7 tOC = CTMR × 1.2 V / 82 µA = 10 µF × 1.2 / 82 µA ≈ **146 ms** (C105/C205). Fast trip
  unchanged (≈ 80 A, 4–5 µs).
- Heat (`tools/heat_budget.py`, RDS(on)-path 11.7 mΩ at 150 °C, BSC030N08NS5 Diagram 9;
  `--channels 2 --part HC-2xBSC030 --rth-ja 20 --r-box 0.9 --r-path 0.002 --p-other 0.6` – the default before T-0085 –,
  40 °C, both channels loaded):
  15 A → Tj 88 °C, 17.5 A → 111 °C, 18 A → 117 °C, 18.5 A → 123 °C, 19.7 A (upper IOC) → 139 °C; with
  `--p-other 1.9` 17.5 A → 113 °C, 18 A → 118 °C. All below the MOSFET Tj max 150 °C (Table 2), so the hardware
  breaker now closes the gap that the 25 A setting left (Tj 169 °C at 22 A).
- Motor starts: a start current above IOC is passed only if it falls below IOC within ≈ 122 ms (lower end of tOC).
  The SEAFLO SFBP2-G3500-01 start current is not published: **measure it on or after the first working prototype, before a board runs a pump in service** (decision 100, `docs/pump-start-current-test.md`).
  At the lower tolerance end (≈ 15.2 A) a pump drawing 12.5 A max still has ≈ 20 % margin in steady state.
- Required outside the board (README, label): an external breaker ≤ 15–18 A per output, and a **firmware soft fuse**
  on IMON (for `/system firmware`: e.g. I²t against the 15 A rating, alarm and switch-off above it while the ESP32 runs).
- Failure mode (bilge forced run, safety-relevant): a lower IOC means a stalled or hard-working pump above ≈ 15–20 A
  is switched off after 146 ms and retried after ≈ 3.8 min instead of running on. That only affects the manual forced
  run; the float-switch circuit stays wired to the battery (decision 15, invariant 8). The trip is reported (FLT_I).
  A competent person reviews the bilge wiring and breaker sizes before installation.

**OUT sense (R63/R64/C62 OUT1 → IO4, R65/R66/C63 OUT2 → IO5; HC2 root sheet).** Same parts as VBAT_SENSE
(220 k C25767, 22 k C25768, 100 nF C307331, all already on the BOM); the no-connects on IO4/IO5 are removed. The shared
controller sheet parts are unchanged; only the HC2 root pin use differs (pin map, decision 39).
- IO4 = ADC1_CH3, IO5 = ADC1_CH4 (ESP32-S3-MINI-1 datasheet v1.7 Table 3-1; invariant 10). Ratio 22/242; ATTEN3
  calibrated range 0–2.9 V (chip datasheet Table 5-6) → full scale ≈ 31.9 V; 28.8 V → 2.62 V. τ = (220 k ‖ 22 k) ×
  100 nF = 2 ms.
- Float-switch run with the PDM unpowered (3V3 off): the divider's Thevenin source is 2.62 V / 20 k, so the pin never
  sees more than 2.62 V and at most (28.8 − 0.5) / 220 k ≈ 0.13 mA flows into the pin's ESD path. Espressif states no
  injection-current limit and nothing about back-powering (part facts C2913206, `UNVERIFIED`); the current is the same
  order as the accepted VBAT_SENSE divider. At the D103 clamp (53 V, transient) ≤ 0.24 mA.
- Freewheel (OUT −0.5 V via D102): pin −45 mV, inside V_IL min −0.3 V. Reverse/negative OUT (e.g. −30 V): the pin's
  ESD diode to GND clamps, current ≤ 30 V / 220 k ≈ 0.14 mA.
- Failure mode (invariant 8): the divider is a passive 242 k load on the pump feed (≈ 0.12 mA at 28.8 V); a shorted
  lower resistor or capacitor raises it to 28.8 V / 220 k ≈ 0.13 mA; a shorted 220 k puts OUT straight on IO4/IO5,
  which may destroy that ESP32 pin, but the fault current is then limited by the pin and the PDM-leg breaker, not by
  the float circuit, which stays wired to the battery and works without the PDM. A float-driven run is now seen as
  "OUT high while the channel is off". A competent person reviews the bilge wiring before installation.

### 4a.3 Gate slew and maximum load capacitance (T-0106: T-0054, T-0006, T-0061, T-0053; Q-0049–Q-0051, Q-0053; decisions 25, 72; 2026-11-03)

**Circuit** (TPS4811-Q1 SLUSEE5E §8.3.2.1, Fig. 8-6; part facts C17556513), per channel:
R104/R204 = R1 10 kΩ (C25744) PU → GATE; R115/R215 10 Ω (C25077) + C114/C214 1 nF (C9196) from GATE to GND;
PD → R116/R216 0 Ω (C17168) → GATE (PD direct, decision 25). All four parts were already on the BOM (+6 parts,
+0 unique). C1 returns to GND (the ground symbol of Fig. 8-6; on SRC it would not slow the source-follower ramp). C1
sees VS + V(BST–SRC) ≈ 41 V in normal use and ≈ 60 V with VS at the ≈ 48 V clamp, so it is the 1 nF/2 kV X7R 1206
C9196 (§8.3), not the 50 V C1523.

**Ramp.** The FET source follows the gate: dVOUT/dt = (V(BST–SRC) − VGS) / (R1 × C1), Eq. 3 form 0.63 × 12 V /
(10 k × 1 nF) = 0.76 V/µs; nominal (11.7 V, VGS ≈ 4.6 V) ≈ 0.66 V/µs; range 0.53–0.77 V/µs (V(BST–SRC) 11–12.3 V,
p. 8; C1 ±10 %). 0 → 30 V in **≈ 40–57 µs**. Before that the gate charges R1 × (C1 + Ciss of both FETs ≈ 9.5 nF,
Diagram 11) to ≈ 4.5 V in ≈ 50 µs. Before T-0106 the edge was estimated at 400–800 V/µs (EMC report 2026-10-30, E2);
it is now of the order of the PROFET channels (0.8 V/µs).

**Inrush and fast trip (a).** I = CLOAD × dV/dt: 50 µF → ≤ 38 A, plus a 15 A resistive load → **≤ 53 A worst case**
against the lowest ISCP threshold ≈ 71 A (RISCP 4.7 k, I(ISCP) 13.7 µA min, Eq. 11): ≥ 25 % margin. 68 µF → 66 A
(no margin); 100 µF → 88 A (trips).

**Eq. 4 (e).** CBST > Qg(total) + 10 × C1 = 2 × 76 nC + 10 nC = 162 nC ≪ 1 µF (C103/C203; holds with X5R DC-bias loss).

**SOA method (b, c).** Q11/Q21 (input side) carries VS − VOUT. BSC030N08NS5 SOA Diagram 3, 30 V, Tc 25 °C, single
pulse, re-digitised in T-0106 (part facts C501507, ±10 %): 1 µs 400 A, 10 µs 190 A, 100 µs 16.6 A, 1 ms 1.56 A (lines
∝ VDS⁻², the thermal-instability region). The power profile is computed in 0.05 µs steps and compared as an
equivalent rectangle at peak power (t_eq = E / Ppeak) with the SOA at 30 V for the whole pulse (conservative: VDS
falls during the ramp), log-log interpolated and derated linearly to zero at 150 °C: k = (150 − Tstart) / 125.
Start temperatures from `tools/heat_budget.py` (2 × 15 A, 40 °C): idle board 47 °C (k 0.82); hot start right after
running at 15 A, Tj 90 °C (k 0.48). Zth j-c max (Diagram 4) superposition gives Tj as a cross-check. Short at
turn-on: zero-impedance short, 30 V across Q11, current from transfer Diagram 7 (envelope of the 25/150 °C curves),
gate R1 × (C1 + 9 nF) from 0 V, until ISCP plus tSC 5 µs (p. 10). Script: `docs/reviews/2026-11-03-fix-pdm-hc2-T-0106.md`.

Results for 10 k / 1 nF (worst case V(BST–SRC) 12.3 V, C1 −10 %); margin = allowed / actual peak power:

| Case | Ipeak | E in Q11 | Ppeak | t_eq | margin idle (k 0.82) | margin hot (k 0.48) | Tj hot (Zth) |
|---|---|---|---|---|---|---|---|
| 50 µF + 15 A, turn-on | 53 A | 25 mJ | 1.18 kW | 22 µs | 1.76 | **1.03** | 124 °C |
| 68 µF + 15 A | 66 A | 34 mJ | 1.56 kW | 22 µs | 1.34 | 0.78 ✗ | 135 °C |
| 100 µF + 15 A | 88 A (trips) | 48 mJ | 2.2 kW | 22 µs | 0.93 ✗ | 0.54 ✗ | 154 °C |
| Turn-on into a short, ISC 71 A | 111 A | 26 mJ | 3.3 kW | 8 µs | 1.52 | 0.89 ✗ | – |
| Turn-on into a short, ISC 91 A | 139 A | 36 mJ | 4.2 kW | 9 µs | **1.18** | 0.69 ✗ | – |

Other pairs (sweep R1 1–47 k × C1 1–47 nF): slower ramps (10 k/2.2 nF, 2.2 k/10 nF, 4.7 k/4.7 nF ≈ 0.34 V/µs) put
more energy into Q11 (the resistive load share grows) and fail the hot 50 µF case (0.88–0.89); a larger C1 with a
smaller R1 fails the short case even from idle (the current climbs further during tSC); no pair passes 100 µF even
from idle. T-0070's 100 k / 3.9 nF fails all cases with this MOSFET.

**Rating: at most ≈ 50 µF load input capacitance per HC2 output** (30 V, with up to 15 A resistive load in
parallel; decision 72 range 50–100 µF, lower end). The prototype measures the real loads (Q-0045) and confirms it.

**Turn-on into a short** passes from an idle board (start ≤ 63 °C at the worst-case 91 A threshold, margin 1.18),
but not straight after the channel ran at 15 A (0.69–0.89). No R1/C1 in the sweep passes that corner. It is a bounding
model: the old 10 Ω hard turn-on would, in the same model, drive > 400 A (ID,pulse) through Q11 because the gate is
fully open within a microsecond; real shorts have wiring inductance that limits di/dt and VDS. Prototype test (STATUS).

**Turn-off (f)** unchanged: PD direct through R116/R216 0 Ω, tSC 4–5 µs, 4 A PD sink; C1 discharges through R2
10 Ω (≈ 12 nC). A short while the output is on (gate fully on) is cleared as before. While on, the gate sits at
SRC + 12 V through R1 (C1 has no DC load); a fast VS step of ΔV lowers VGS by C1 / (C1 + Cgs) ≈ 10 % of ΔV.
Heat budget unchanged (2 × 15 A → Tj 90 °C, 40 °C).

**Failure mode (bilge forced run and other safety-relevant HC2 outputs):**
- The slew does not delay the fast trip of a short while the output is on (PD direct, tSC unchanged).
- A load with more than ≈ 50 µF input capacitance can trip the fast short-circuit protection at switch-on. The output
  then stays off for ≈ 3.8 min and retries, also on the hardware forced-run path. The float switch stays independent
  (invariant 8). Measure every intended load on the prototype; split LED work-light groups that trip.
- Switching a channel that just carried 15 A on into a short is outside the calculated SOA. If Q11/Q21 then fails
  short, the output cannot be switched off any more (the output-side MOSFET's body diode conducts), and only the
  required external breaker (≤ 15–18 A, decision 39) clears a fault – as for any MOSFET failure.
- A competent person reviews the bilge outputs before installation.

**T-0053 (Q-0053):** no change. R113/R213 stay 68 k C36871 (decision 39, T-0072). Decision 19 and the ≈ 21 A load
option are withdrawn by the owner (2026-11-03).

**Use of the rating (decision 94, amends decision 72; 2026-11-04).** Plan on one LED work light per output. Several lights on
one output are allowed only for loads with little capacitance, such as plain LED strips without their own driver (expected, not
measured), or once the prototype shows that group switches on cleanly from warm. A strip with its own driver, dimmer or
controller box counts as a capacitive load. Allowing a few hundred µF would take a pre-charge path: TPS48111-Q1 (pin 11 = G,
N.C on the TPS48110; part facts C17556513) plus a pre-charge MOSFET and resistor on each channel, with gate slew, short-circuit timing
(tSC 1.2 µs instead of 4 µs) and SOA rechecked and a new validator round. Cost and TPS48111-Q1 stock are not checked. Not done now;
it is the planned fix for the next HC2 revision if the prototype shows real loads need it.

## 5. Physical switch inputs and long leads

Per input (sheet `analog_sw`): SMAJ30CA at the connector → 4.0 kΩ load, two 2 kΩ 1206 in series (R3+R45, R4+R46,
R7+R47, R8+R48; contact wetting 3.0 mA at 12 V / 7.5 mA at 30 V) → 10 kΩ 1206 series → node with 4.7 kΩ, BZT52C3V3 and 470 nF →
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
| 1–4 | SWIN1–4: switch from SW_SUPPLY | SMAJ30CA, 2 × 2 k load, 10 k + divider (above) |
| 5 | SW_SUPPLY = VS via PTC F4 (mSMD050-60V C70113, same part as F1) + 0.2 Ω R56 (T-0118, decision 81) and Schottky D55 (DSK16) | SMAJ30CA + 100 nF/100 V |
| 6–9 | LED_K1–4: panel LED cathode (anode to SW_SUPPLY) | SMAJ30CA, 100 Ω, 1 nF at the collector |
| 10 | GND (cable drain / spare) | – |

- LED sinks: GPIO (IO38–IO41) → 1 k → base, 10 k base pull-down, MMBT5551 (V_CEO 160 V, above the
  SMAJ30CA clamp of ≈ 48 V; BC817's 45 V was not), 470 Ω emitter. V_B ≈ 3.3 × 10/11 = 3.0 V,
  V_E ≈ 2.33 V → I_LED ≈ 5.0 mA independent of the supply (10.5–30 V), the LED colour and the cable length
  (≥ 10 m is fine; the panel has no LED resistor). Dissipation at 30 V ≈ (30 − 2 − 2.3) × 5 mA ≈ 0.13 W;
  R_θJA 416 K/W (JCET datasheet) → T_j ≈ 50 °C enclosure air + 54 K ≈ 104 °C (< 150 °C). LEDs are off
  when the 3.3 V rail is down. PWM: low frequency (100–200 Hz); the 1 nF collector capacitor slows edges.
- Switch-supply budget ≈ 60 mA at 30 V (4 × 7.5 mA switch load + 4 × 2.6 mA divider + 4 × 5 mA LEDs; was ≈ 50 mA
  counting the 6.4 mA loads and leaving out the divider); F4 holds 500 mA.
- **Switch loads 2 k + 2 k (T-0046 → T-0105, Q-0048/decision 74, 2026-11-03):** each 4.7 k load became two 2 kΩ 1206 in
  series, R3+R45, R4+R46, R7+R47, R8+R48 (UNI-ROYAL 1206W4F2001T5E, C17944, basic; `docs/part-facts/C17944.md`):
  0.25 W at 70 °C, derated linearly to 0 at 155 °C; RCWV = √(0.25 W × 2 kΩ) = 22.4 V; short-time overload 2.5 × RCWV =
  55.9 V for 5 s (datasheet §9, test 4.13). Replaces the 2.2 k + 2.4 k of decision 35 (no basic part).
  - Continuous, SWIN 29.6 V (30 V behind D55): 7.4 mA, 14.8 V and 0.11 W per part (44 %, ≤ RCWV); at 32 V 0.13 W (51 %).
    At ≈ 50–60 °C enclosure air plus self-heating the parts stay below the 70 °C derating knee or close to it. Was 0.19 W
    in one 0.25 W part (77 %).
  - SMAJ30CA clamp on SWIN (≈ 48 V): 12 mA, 24 V and 0.29 W per part (115 % for the surge's µs–ms), inside the 5 s
    overload rating of 55.9 V per part; was 0.49 W in one part. The pulse capability below 5 s is not published
    (UNVERIFIED), but 24 V is well under the 5 s level.
  - Thresholds unchanged (the load is parallel to the divider; §3 recheck). Wetting current up: 3.0 mA at 12 V, 7.5 mA
    at 30 V.
  - Leakage across an open contact (lamp or LED across a switch, against the README's dry-contact rule): below the zener
    knee the input looks like 4.0 k ∥ 14.7 k = 3.1 kΩ (was 4.7 k ∥ 14.7 k = 3.6 kΩ). Reaching the ≈ 7.5 V EN threshold
    now takes ≈ 2.4 mA of leakage instead of ≈ 2.1 mA: slightly better rejection; the dry-contact rule stays.
  - Panel load +0.13 W at 30 V (p_other ≈ 2.3 W, §4); switch-supply budget below.
- **Failure mode (safety), T-0105:** the panel inputs control safety-relevant outputs (bilge forced run, navigation lights).
  - One half open (the usual thick-film failure): that input loses its load, the switch still works; only the wetting
    current and the leakage rejection of that line are gone, so a leaky contact or a floating cable could switch it on.
    Same as the old 4.7 k open.
  - One half shorted: the load drops to 2 k (15 mA, 0.44 W in the remaining part at 30 V, above its rating); it heats
    and drifts or opens (then as above). The switch still works. The old single 4.7 k shorted would have pulled SWIN to
    GND and tripped F4 for all panel lines; two in series need a double fault for that.
  - A competent person must review the panel wiring and these outputs before installation.
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
  - D55 open: all panel switches and LEDs of the board dead, the same symptom as a tripped F4. The SW_SUPPLY
    sense (decision 93) sits on the J5.5 side and catches it too.
  - D55 shorted: back to the old behaviour (the panel works; the LEDs are unprotected against reversal).
  - A hard short in the panel cable drives the F4 fault current through D55 until F4 trips (≤ 0.15 s at 8 A). Whether
    D55 survives the highest fault currents (IFSM 25 A for 8.3 ms) is UNVERIFIED. A diode that fails open gives the
    "D55 open" case above.
  - A competent person must review this before installation.
- **Failure mode (safety):** a short in the panel cable (or at a panel switch) trips F4; all panel
  switches of that board then do nothing until the short is cleared, while NMEA 2000 control keeps
  working, but the panel LEDs go dark too. The firmware sees this on SW_SENSE (below) and can alert. Outputs that must
  keep working from the panel (bilge forced run, navigation lights) need a competent person's review; an
  installer can also feed the switches from a separate fused supply (the inputs accept any 10.5–30 V).
- **SW_SUPPLY sense (decision 93, replaces decision 21):** R49 10 k 1206 (C17902) from SW_SUPPLY to SW_SENSE; R57 4.7 k
  (C25900), D24 BZT52C3V3 (C19077396) and C21 470 nF (C47339) to GND; R58 10 k (C25744) to IO12, read as a digital input.
  It is the switch input network, so no new unique part. The 100 k/10 k divider of decision 21 was dropped: IO12 is ADC2,
  which invariant 10 rules out, every ADC1 pin is taken on pdm-4ch, and as a digital input the divider gives 2.18 V at 24 V
  against VIH 2.475 V (0.75 × VDD; ESP32-S3 datasheet p. 65, GPIO12 = ADC2_CH1 p. 24).
  - Reads high from about 2.475 V × 14.7 / 4.7 ≈ 7.7 V on SW_SUPPLY. At 30 V: 2.6 mA, 68 mW in R49 (≈ 0.2 W at the 48 V clamp).
    Adds ≈ 0.08 W to p_other; `heat_budget.py --p-other 2.4` still gives 4 × 4 A Tj ≈ 101 °C.
  - Reads low on: F4 tripped, D55 open, a short at J5.5 or a battery below about 8.5 V. So the firmware alerts only while
    VBAT_SENSE shows a healthy battery (cranking on a 12 V system must not raise a false alarm).
  - It cannot see a fault on one switch line, only the shared supply.
  - **Failure mode:** R49 open or D24/C21 shorted gives a false alert and nothing else; the panel path does not pass through
    this network, so invariant 1 holds. This is an alert, not a safety function. The panel-switched outputs (bilge forced run,
    navigation lights) still need a competent person's review before installation.
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

| IIS(FAULT) | P in RIS 680 Ω (I²R) | 0603 (0.1 W) | 1206 (0.25 W) | RIS 500 Ω = 2 × 1 kΩ 1206 (T-0107): total / per part (of 0.25 W) |
|---|---|---|---|---|
| 6 mA | 24 mW | ok | ok | 18 mW / 9 mW – ok |
| 15 mA | 153 mW | **over** | ok (61 %) | 113 mW / 56 mW – ok (23 %) |
| 40 mA | 1.09 W | **over** | **over** | 0.80 W / 0.40 W – **over** (160 %) |

Hardware: R103/R203/R303/R403 are now 680 Ω **1206**, 0.25 W, 1 %, C17975 (UNI-ROYAL 1206W4F6800T5E). No *basic* 1206
680 Ω exists at JLCPCB (all 25 parts are extended), so the cheapest extended one was taken; the 0603 C23228 is no
longer used on the board. The value is unchanged, so the sense scaling (≈ 0.45 V/A) is unchanged. The 1206 covers the
typical fault current continuously. The 40 mA maximum (1.09 W) is **not** covered by hardware – by ruling that case is
covered by the firmware rule above (IS is clamped at ≈ 3.3 V by D102, but the current still flows through RIS until DEN
is dropped). A 2 W part was not fitted (not asked for). If the owner wants the 40 mA case covered in hardware, RIS would need a rating of about 1.5–2 W (a larger, costlier part): open point.

**Update T-0107 (2026-11-03, cost lever L7, auto):** each RIS is now **two 1 kΩ 1206 0.25 W 1 % in parallel = 500 Ω**
(R103 ‖ R107, R203 ‖ R207, R303 ‖ R307, R403 ‖ R407; UNI-ROYAL 1206W4F1001T5E, C4410, **basic**; facts file
`docs/part-facts/C4410.md`: 1/4 W up to 70 °C, derated to 0 at 155 °C, 200 V working). This removes the extended C17975
(no basic 1206 680 Ω exists). Decision 36 (RIS 1206 ≥ 0.25 W) is met by each part; together they carry 0.5 W.
Full-load IS (kILIS from Table 9 p. 30 of each datasheet, facts files C534868/C534858; worst case = minimum kILIS):

| Part, load | kILIS typ (min) | IIS typ (max) | VIS at 500 Ω typ (max) |
|---|---|---|---|
| BTT6050, 4.5 A | 1500 (1380, −8 % at 4 A) | 3.0 mA (3.26 mA) | 1.50 V (1.63 V) |
| BTT6010, 8 A | 3900 (3549, −9 % at 10 A) | 2.05 mA (2.25 mA) | 1.03 V (1.13 V) |
| BTT6010, 9 A IL(NOM) | 3900 (3549) | 2.31 mA (2.54 mA) | 1.15 V (1.27 V) |

All stay below the ADC's calibrated 2.9 V (12 dB) and the 3.3 V clamp D102, and far below the IS compliance limit
VS − 3.5 V (VIS(RANGE), P_7.5.6). Resolution at small currents falls by about a quarter (0.45 → 0.33 V/A); this is
still more than the alarms need (cost report L7). The full-scale reading that triggers rule 2 below is now reached at
a sense current of ≈ 5.8 mA (2.9 V / 500 Ω) instead of 4.3 mA – still below the IIS(FAULT) minimum of 6 mA, so every
fault current still reads full scale.
**Firmware scale constant: RIS = 500 Ω, IL = VIS / 500 Ω × kILIS (≈ 0.33 V/A for the BTT6050 at kILIS 1500,
≈ 0.128 V/A for the BTT6010 at kILIS 3900).**

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
fails to a hazardous state; a failed-open RIS reads as zero current (a fault would not be reported). With RIS as two parallel 1 kΩ (T-0107), one
part failing open doubles the reading (1 kΩ: a false high current or full-scale fault report, the safe direction);
only both open reads zero; one part failing short (rare for thick-film) reads zero as before. These are not
safety outputs on their own, but the sense path is used for the bilge-pump jam detection, so a competent person
reviews this before installation.

**Firmware requirements (for `/system firmware`):**
1. DEN pulsed only while sampling IS, never held high in Active mode (Q-0041); in Eco sampled less often.
2. Drop DEN immediately on a full-scale IS reading (fault current flowing); report the channel; retry later.
3. Nothing else may hold DEN high (bootloader/reset state: IO33 pulls down; check at firmware design).
4. Allow the settling time after the DEN rise and after IN falls (tsIS(FAULT_OL_OFF), datasheet Fig. 26) before
   diagnosing open load in OFF.

## 7. Mechanics and connectors

Decision 97 (amends decision 10). The board mounts two ways on the same four non-plated M3 holes H1–H4:

- **DIN rail, no enclosure of its own:** bare board on a plastic carrier, PCB edge-on to the rail, about 65 mm (4-ch) / 75 mm (HC2) deep and up to 100 mm long (decision 98), in an enclosure the
  installer provides. One enclosure can hold several units. The carrier and its screws never reach board copper, because the
  rail may be bonded to the hull (invariant 6).
- **3D-printed enclosure instead of the rail:** vented ASA (PETG softens at ~80 °C), also for flat mounting on a wall or ceiling.

**Rail pitch (the 36 mm is unverified until the sample check).** A terminal's height runs across the rail, so its drawing height plus pin length below the board plus 1 mm sets the
pitch. KF135T-10.16 (C475108): 29.5 + 4.3 + 1 = 34.8 mm. KF7620-7.62 (C475104): 21.5 + 4.9 + 1 = 27.4 mm. DB128V-5.08 (C2915639):
14 + 3.5 + 1 = 18.5 mm. Those fixed blocks set the first figure of about 36 mm per unit. Decision 98's J10 socket C6394053 is 13.4 + 4 + 1 = 18.4 mm, and its 27.8 mm plug
at worst 27.8 + 4 + 1 = 32.8 mm, so 36 mm stays conservative; how the plug sits against the board is not on the drawing. The pdm-4ch J10 (decision 104) is C577772: socket 14.2 + 5 + 1 = 20.2 mm. Its plug C577752 has a 30.60 mm overall height on the drawing, which would be 36.6 mm if that dimension lay across the rail. The drawing does not settle which way it lies, so the sample check decides it (the same plug is on HC2 J11). The old 1-module target (about 14.5 mm inside) could
not hold even the smallest of these.

**Screw access (solved by decision 98).** On fixed screw blocks the screw faces away from the PCB, so edge-on it would face the
neighbouring unit. Face-on mounting (about 60 mm per unit) was the alternative; the owner chose rail density and keyed plugs on
right-angle sockets, wired on the bench and pushed in from the board edge.

**Connectors (decisions 98, 104, drawings C6394053, C577772, C577767, C441238, C26895).** Footprints in `lib/ESP32-PDM.pretty`, origin at
pad 1, y toward the mating face. Row lengths: 4-ch J10 30.5 + J11 21.9 = 52.4 mm; HC2 J10 38.1 + J11 30.5 = 68.6 mm; J5 39.0 + J4
16.1 = 55.1 mm. Hence about 65 mm and 75 mm board depth with gaps. On pdm-4ch the J5/J4 row now sets the depth; the board size stays decision 98's until layout. The 4-ch J10 and HC2 J11 bodies reach 29 mm in from the edge, the HC2 J10 body 34 mm,
so the HC2 parts take most of one end of that board. J5 stays a Conn_02x05 symbol; its pins 1–10 run in a single row. The HC2 J10 plug
adds about 39 mm past the board edge plus the cable bend, and it is 27.8 mm thick. **Not proven by the drawings, so checked on one
sample of each set before layout:** that plugs cannot go in reversed, whether a 4-pole J4 plug can enter the 10-pole J5 socket (label
them), and that plugs fit the 36 mm pitch. Pad 3.2 mm for the HC2 J10 pins (three per pole); 2.8 mm pads, drill 1.5 mm for the 7.62 mm set (two per pole). Hand-soldering J10 into 2 oz copper needs a
powerful iron; a cold joint at the full input current (16 A on 4-ch, 36 A on HC2) overheats. The flange holes are non-plated, so the header screws touch no copper. Stock when
chosen (2026-11-05): C6394053 39, C6394029 50, C577772 40, C577752 63. **Stock on 2026-11-07: C577772 0 (minimum order 18), C577752 63, and the set now serves both boards (pdm-4ch J10, pdm-hc2 J11).** The Phoenix 10.16 mm set (C6790556) is the
fallback at a higher price, not footprint-compatible.

**pdm-4ch J10, 7.62 mm set (decisions 103, 104, T-0158, 2026-11-07).** Footprint `Kefa_KF2EDGSRM-7.62-2P` checked against the C577772 drawing (KF2EDGSRM-7.62 rev. A, 2023-05-12, rendered and read; `docs/part-facts/C577772.md`): **pass, footprint unchanged, so HC2 J11 is unaffected.**

| Drawing | Value | Footprint (origin pad 1) |
|---|---|---|
| Column / row spacing | 7.62 ± 0.03 mm both | pads x 0 / 7.62, y 0 / 7.62 |
| PCB hole | Ø1.50 +0.10/0, pin 0.80 × 1.00 mm (1.28 mm diagonal) | drill 1.5, pad 2.8 mm |
| Flange holes | Ø3.20, spacing (P−1) × 7.62 + 15.24 = 22.86 mm, 13.00 mm from the rear edge | NPTH 3.2 at x −7.62 / 15.24 (22.86 mm), y 11 = −2 + 13 |
| First row to rear edge | 2.00 mm | body edge y −2 |
| Body width / depth | P × 7.62 + 15.24 = 30.48 mm / 29.00 mm | x −11.43…19.05, y −2…27 |

The pin rows lie at the rear edge and the mating face opposite it (side view), so the facts file's open point on the side of the second row is settled. The drawing does not number the poles. Pad 1 = VBAT_IN and pad 2 = GND are this design's choice, to be marked on the board at layout; the sample check covers the plug's one-way fit. The JLCPCB footprint has no flange holes; ours does. The socket is hand-soldered (decision 85), so no CPL check applies.

**Rating at the enclosure temperatures of decision 97.** The ratings are 30 A UL (group B, 300 V) and 32 A IEC at pollution degree 2; the socket's IEC table has no current for pollution degree 3, which the plug lists at 32 A. Both parts are rated −40 to +105 °C. **Neither drawing has a derating curve or a contact resistance**, so the check below is an estimate, not a datasheet figure. 16 A is 53 % of the 30 A UL figure, and contact heat goes with I², so 28 % of the heat at the rated current. Assuming a 30 K rise at rated current (assumption, common for terminal-block ratings), that is about 8.5 K at 16 A: about 59 °C in 50 °C air (decision 97's full rating) and about 80 °C at 16 A in 70 °C air, which decision 97 does not allow anyway (3 A per channel there, 12 A, ≈ 5 K). All stay below 105 °C. The plug's wire limit is 4 mm² (24–10 AWG), M3, 0.5 N·m max, strip 7–8 mm. A 4 mm² feed suits 16 A; the installer's cable and fuse rules apply.

**Heat in a shared enclosure.** Every board gives off about 9 W at full load, all into the same air, so the rating is the air inside
the box (`heat_budget.py --r-box 0 --ambient T`, estimates): 4-ch at 4 A Tj 107 °C at 50 °C air, 114 °C (marginal) at 55 °C, 127 °C
(over) at 65 °C; at 3 A 96 °C at 65 °C and 102 °C at 70 °C. HC2 at 15 A: 99 °C at 55 °C, 111 °C (marginal) at 65 °C. A closed
300 × 200 × 120 mm plastic box rises roughly 0.75 K/W (rule of thumb), so three boards at full load in a 40 °C space give about
60 °C: derate or vent. Board spacing and the tall blocks affect the assumed RthJA; measure on the prototype.

**Bare board rules (README).** The enclosure must keep out drips and loose metal, because an open board has unfused battery copper.
Conformal coating is an option to consider for marine air.

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
  **Limit (T-0121, EMC E16, owner ruling Q-0054):** the paragraph above covers the BTT6050 switches only. C31
  (C487384, 100 µF/63 V polarised aluminium electrolytic on VS, added in T-0064 after this analysis) has no reverse
  rating in its datasheet. Without a blocker it would be reverse-biased by the full battery voltage, limited only by
  the cable and battery fuse, and could overheat and vent. **Since T-0121 the reverse-battery blocker Q30/U30 (§8.6)
  sits in front of everything on VS**: with a reversed battery of up to 30 V (D30 stand-off) VS stays unpowered, so
  C31, the BTT6050s, the panel interface and the loads see no reverse voltage, with no time limit. The BTT6050 limits
  above apply again only if Q30 has failed short. Check the polarity before connecting anyway.
- Reverse battery (`pdm-hc2`, T-0072/T-0055, Q-0044, decision 40): the survival statement above does **not** apply to
  HC2. A reversed battery puts the full battery voltage negative on TPS48110A-Q1 VS/CS+/CS−/ISCP (abs max −1 V to
  GND, SLUSEE5E §6.1); D30 SMCJ30CA is bidirectional and does not conduct below ≈ 33 V, so nothing limits the current
  and both controllers are likely destroyed (mechanism `UNVERIFIED`). The back-to-back MOSFETs still block the loads
  and the buck is protected by D2. Mitigation for this revision: keyed J10 plug (decision 98, one-way fit checked on a sample)
  plus a README and label warning. Full reverse-polarity protection is deferred to a later HC2 revision.

### 8.1 Battery input J10: TVS, capacitors, ferrite position (decision 26, T-0064, 2026-11-01)

Root sheet, the same on both boards (controller part):

| Ref | Part | Net | Purpose |
|---|---|---|---|
| D30 | SMCJ30CA (C19077607, preferred) | VBAT_IN–GND | surge clamp at the terminal (unchanged part, now on the terminal side of FL30) |
| C30 | 2.2 µF/100 V X7R 1206, Samsung CL31B225KCHSNNE (C170101, extended, the same part as C1; was 1 µF C13832 until T-0107 – decision 26 allows 1–2.2 µF at J10) | VBAT_IN–GND | HF return at the terminals |
| FL30 | ferrite / CMC position, **DNP** | VBAT_IN–VS | decided at the pre-compliance scan (decision 28) |
| JP30 | copper bridge (net tie, no part) | VBAT_IN–VS | keeps VS connected while FL30 is not fitted; cut only when FL30 is fitted |
| C31 | 100 µF/63 V Al electrolytic, Ymin VKMD1001J101MV (C487384, extended) | VS–GND | bulk at J10 |

**pdm-4ch since T-0121 (§8.6):** FL30/JP30 now link VBAT_IN to the new net `VBAT_FL`, and the reverse-battery blocker
Q30 (source VBAT_FL, drain VS) feeds VS. D30 and C30 stay on VBAT_IN at J10; C31 and everything else on VS sit behind
Q30. pdm-hc2 is unchanged (FL30/JP30 still VBAT_IN–VS, decision 40).

HC2 only (`hc_channel`, ×2): C106/C206, the same 100 µF/63 V at each channel's VS, so HC2 has 3 × 100 µF.
4-ch only (`channel`, ×4): C104–C404, 2.2 µF/100 V X7R 1206 C170101 (the part of C1/C30) at each BTT6050 VS tab, next to
C103 (100 nF). Was 1 µF C13832 until T-0120; owner rulings Q-0063/Q-0064 amend decision 26 to "≥ 1 µF/100 V (2.2 µF
C170101)" and supersede auto decision 44. Same footprint, so placement and the 100 V rating above the 48.4 V clamp are
unchanged. DC bias at 24–29 V leaves an estimated ≈ 1–1.5 µF (not checked against a Samsung curve), still ≥ the former
nominal 1 µF. pdm-4ch now carries no C13832, so its loading fee is gone; revisit if runs grow past about 12 boards (ruling).

Part facts:
- Ymin VKM series datasheet (catalogue pp. 178–180): −55…+105 °C, tan δ 0.14 at 63 V (120 Hz), life
  10 000 h at 105 °C for ≥ φ8, AEC-Q200. 100 µF/63 V = 8 × 10 mm, ripple 902 mA rms (105 °C, 100 kHz);
  frequency factor 0.50 at 120 Hz → 451 mA rms. ESR is not specified. From tan δ, ESR(120 Hz) ≤ 0.14/(2π·120·100 µF)
  ≈ 1.9 Ω; it is lower at 100 kHz, but the datasheet gives no figure. Body dimensions (B = C = 8.3, A = 3.4, H = 0.9,
  E = 3.1 mm) are the standard 8 × 10 size of KiCad `CP_Elec_8x10`. Check that footprint against the JLCPCB/EasyEDA
  footprint before ordering.
- Samsung CL31B225KCHSNNE (C170101, now C1, C30, C104–C404): X7R, 100 V, 2.2 µF ±10 %, 1206, soft termination
  (`docs/part-facts/C170101.md`, Samsung MLCC catalogue p. 4 and p. 45).
- Former part, no longer on either board: Samsung CL31B105KCHNNNE: part-numbering code 31 = 1206, B = X7R, 105 = 1 µF, K = ±10 %, C = 100 V (Samsung MLCC
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

Cost per board at 10 units (part prices at 1–49 pcs, T-0064 figures; since T-0107/T-0120 C30 and C104–C404 are C170101 at
0.1185 USD (1+, JLCPCB 2026-11-03), so 4-ch C30 + 4 × C104 ≈ 0.59 USD, but no C13832 fee): 4-ch C31 0.22 + C30 0.065 + 4 × C104 0.26 = 0.54 USD;
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

**PTC + series resistor (T-0104, Q-0047, decision 73, 2026-11-03): PTC check passed, resistor pulse check NOT passed,
nothing changed, back to the owner.** Part facts: `docs/part-facts/C70113.md`, `C427396.md`, `C269104.md`, `C25334.md`,
`C2960770.md`, `C327006.md`, `C7420022.md`, `C19633830.md`.

| PTC | V_max / I_max | I_hold 25 / 40 / 60 °C | I_trip 25 °C | R_min / R1max | Trip | Body | JLCPCB (2026-11-03) |
|---|---|---|---|---|---|---|---|
| TECHFUSE mSMD050-60V C70113 | 60 V / **100 A** (p. 1) | 0.50 / 0.45 / 0.35 A (p. 2, mSMD050 row) | 1.00 A | 0.150 / **1.000 Ω** | ≤ 0.15 s at 8 A | 4.37–4.73 × 3.07–3.41 × ≤ 1.8 mm | extended, 0.088 USD, stock 70 k |
| JDT ASMD1812-050-60V C427396 | 60 V / **100 A** (p. 2/7) | 0.50 / 0.45 / 0.35 A (p. 4/7, -050 row) | 1.00 A | 0.150 / 1.400 Ω | ≤ 0.15 s at 8 A | same | extended, 0.0725 USD, stock 14.8 k |
| (present F2) Brightking SMD0805B050TF C269104 | **6 V** / 100 A | 0.50 (23 °C) / 0.40 / 0.33 A | 1.00 A | 0.150 / 0.850 Ω | ≤ 0.10 s at 8 A | 0805 | extended, 0.024 USD |

Both 1812 parts pass the I_max ≥ 100 A at ≥ 30 V test and fit the present `Fuse_1812_4532Metric` body (same body as
1812L050/60GR). Both datasheets recommend 1.78 × 3.2 mm pads with a 3.2 mm gap (pitch ≈ 4.98 mm); the KiCad footprint
has 1.125 × 3.4 mm pads at 4.275 mm pitch (gap ≈ 3.15 mm). This must be checked against the JLCPCB footprint before
ordering. Preferred part when the swap is made: **C70113**. Its R1max is 1.0 Ω instead of 1.4 Ω, which matters on F2
(USB VBUS ≈ 0.40 A peak: 0.40 V instead of 0.56 V worst-case drop, against 0.34 V for the present 0805 part). It costs
+0.016 USD per position. The trip curves of both parts are plotted only up to ≈ 10 A (≈ 0.01–0.02 s), so no datasheet
gives a trip time at the fault current.

Series resistor sizing (ruling formula, cable and terminals not counted): R_s ≥ 30 V / 100 A − 0.150 Ω = 0.150 Ω.
At 0.150 Ω the margin is zero, so the choice would be **0.20 Ω** (E24) → I_pk = 30 / 0.35 = 86 A, or 0.22 Ω → 81 A.
- Continuous: F1 (buck input ≈ 0.18 A at 10.5 V) 6.5 mW / 36 mV; at I_hold 0.5 A 50 mW / 0.10 V. F3 ≤ 77 mA: 1.2 mW / 15 mV.
  F4 ≈ 55 mA: 0.6 mW / 11 mV.
- SWIN margin (§3): 11 mV at SWIN is ≈ 3.5 mV at IN (× 0.32). The thinnest case (battery 10.5 V via D55, ≈ 2.05 V) stays
  ≥ 2.0 V. **Pass.**
- Pulse energy: the PTC I²t is not published. Bound: the adiabatic I²t to trip can only fall as the current rises, so it is at
  most the tabulated maximum point, 8² × 0.15 = **9.6 A²s**. From the typical curve (≈ 10 A in 0.01–0.02 s) it is ≈ 1–2 A²s.
  Energy in 0.20 Ω: E ≤ 9.6 × 0.20 ≈ **1.9 J** (typ. 0.2–0.4 J), delivered at a peak of 86² × 0.20 ≈ **1.5 kW** for
  ≈ 9.6 / 86² ≈ 1.3 ms (typ. 0.15–0.3 ms).
- Resistor ratings: **no cheap candidate publishes a 0.1–10 ms pulse rating.** UNI-ROYAL 1206W4F100LT5E C25334 (the only
  basic part in range, 0.1 Ω 1/4 W thick film): only a 5 s short-time overload at 2.5 × RCWV (≈ 1.6 W). FOJAN FRL2512FR220TS
  C2960770 (1 W thick film): 5 s at 6.25 W. Yageo RL1206FR-7W0R22L C327006: 5 s at 5 × P. Alloy shunts FOJAN FRM252WJR200TK
  C7420022 (0.2 Ω 2 W, 0.028 USD) and UNI-ROYAL LR123WF200LT4E C19633830 (0.2 Ω 3 W): 5 s at 10–12 W (50–60 J), ΔR ≤ 0.5 %.
  A 5 s test at 10 W does not cover a 1.5 kW pulse lasting about 1 ms: the heat has no time to spread out of the film or element,
  so the energy ratio (1.9 J against 50 J) proves nothing. Rough thermal estimate for a thick-film 2512 (alumina diffusion
  depth √(α·t) ≈ 0.1 mm in 1.3 ms, own estimate, not a rating): several hundred kelvin at the 1.9 J bound. So it is not shown to pass.
  The ruling says to return to the owner in that case (T-0104 report).
- Failure mode if a series resistor is overstressed: thick-film and alloy chip resistors fail open, so the feed is
  interrupted. For F4 this is the same as a tripped F4 (panel switches disabled, bus control keeps working, decision 17),
  but it does not reset. A brief arc across an opening film at 30 V / ≈ 80 A cannot be excluded from the datasheets.

**PTC + series resistor fitted (T-0118, Q-0060, decision 81, 2026-11-03).** The owner accepted FOJAN FRM252WJR200TK
C7420022 (0.2 Ω ± 5 %, 2 W at 70 °C, alloy 2512) on its 5 s / 5 × P (10 W, ≈ 50 J) overload rating, without a published
ms pulse rating; the pulse-energy question above is settled by that ruling. Part facts: `docs/part-facts/C70113.md`,
`C7420022.md` (both rechecked: 60 V / I_max 100 A / I_hold 0.50 A / 1812; 0.2 Ω / 2 W / 2512 / 5 s overload; both in stock
at JLCPCB on 2026-11-03, 70 k and 53 k).

| Ref | Was | Now | Footprint | Net |
|---|---|---|---|---|
| F1, F3, F4 | 1812L050/60GR C19078719 | mSMD050-60V C70113 | `Fuse:Fuse_1812_4532Metric` (unchanged) | as before on the supply side |
| F2 | SMD0805B050TF C269104 | mSMD050-60V C70113 | `Fuse_0805_2012Metric` → `Fuse_1812_4532Metric` | unchanged, no series resistor |
| R54 (new, `power-usb`) | – | 200m C7420022 | `Resistor_SMD:R_2512_6332Metric` | F1.2 → R54 → D1.2/D2.2 (new net F1-Pad2) |
| R55 (new, `can`) | – | 200m C7420022 | same | F3.1 → R55 → D10.2/FB2.2 (new net F3-Pad1) |
| R56 (new, `analog_sw`) | – | 200m C7420022 | same | F4.2 → R56 → D55 anode (new net F4-Pad2) |

Each PTC moved 7.62 mm towards its supply and the resistor sits in its old place (F3: the wire to J4.2 now runs at
x = 167.64). Prospective current for a hard short right behind the resistor: 30 V / (0.150 + 0.20 Ω) ≈ **86 A** < I_max
100 A (cable not counted). Series resistance in normal use: R1max 1.0 + 0.2 = **1.2 Ω** (was 1.4 Ω with 1812L050/60GR).

Checks with the new parts (R1max 1.0 Ω + 0.2 Ω):
- **(a) F4 / switch path (§3, T-0042):** panel current ≤ ≈ 60 mA (§5, the 30 V figure; less at 10.5 V). F4 + R56 drop
  1.2 Ω × 60 mA = 72 mV at SWIN, ≈ 23 mV at IN (× 0.32); the old F4 alone was 1.4 Ω → 84 mV / 27 mV, so the change
  *lowers* the drop by ≈ 4 mV at IN. Even if the whole 23 mV is taken off the thinnest case (battery 10.5 V via D55, 3V3
  down, ≈ 2.05 V), IN stays ≈ **2.03 V ≥ VIN(H) 2.0 V. Pass.** The prototype measurement T-0042 still decides.
- **(b) F3 / L78M05 headroom:** NET-S minimum 9 V − D11 ≈ 0.4 V − (F3 + R55) 1.2 Ω × 77 mA = 92 mV − FB2 0.30 Ω × 77 mA
  = 23 mV ≈ **8.48 V** against 7 V (5 V + 2 V dropout): ≈ 1.5 V headroom. **Pass** (the "< 0.05 V" for F3/FB2 above
  was optimistic even with the old part: 1.4 Ω gave 0.11 V).
- **(c) F1 / buck input:** ≈ 0.18 A at 10.5 V: 1.2 Ω × 0.18 A = **0.22 V** (was 0.25 V); at I_hold 0.5 A 0.60 V. With
  D2 (≤ 0.70 V) the LMR51610 still sees ≥ 9.5 V at a 10.5 V battery, far above its 4 V minimum. R54 loss 6.5 mW,
  50 mW at I_hold (2 W part). **Pass.**
- **(d) USB-only (VBUS 4.75 V, 0.40 A peak, §8.3 FB1 row):** VBUS − F2 − FB1 (0.30 Ω, 0.12 V) − D3 (DSK16: ≈ 0.49 V typ
  at 0.4 A read from Fig. 3, 0.70 V max at 1 A is the only limit). LMR51610 VIN: recommended ≥ 4 V, UVLO rising ≤ 4 V,
  falling 3.40–3.56 V (C22427220 facts, §6.5).

  | F2 | F2 drop at 0.40 A | VIN, D3 typ | VIN, D3 0.70 V | Self-consistent at constant power (1.83 W), D3 typ / 0.70 V |
  |---|---|---|---|---|
  | SMD0805B050TF (R1max 0.85 Ω) | 0.34 V | 3.80 V | 3.59 V | 3.69 V / 3.44 V |
  | mSMD050-60V (R1max 1.0 Ω) | 0.40 V | 3.74 V | 3.53 V | 3.60 V / 3.34 V |

  At the 0.40 A peak neither part reaches the 4 V recommended minimum, so USB-only power **did not reach it before
  either**; the new part costs 60 mV (≈ 90 mV at constant power). The pass/fail result is the same in every corner:
  with typical D3 both stay above the falling UVLO (3.56 V max), with D3 at its 0.70 V limit both can drop below it at
  the peak. At start-up (≈ 50 mA) VIN is ≈ 4.3 V with D3 ≈ 0.4 V for both parts (D3 below 0.1 A is UNVERIFIED), 65 mV vs 58 mV of PTC + FB1 drop. The ruling's stop condition is therefore not met
  and F2 was swapped. USB stays a service port (README).

Heat budget: no output changes; the new losses are mW (R54 6.5 mW, R55 1.2 mW, R56 ≤ 0.7 mW at 10.5–30 V), so
`tools/heat_budget.py` was not rerun (decision 9 covers output changes).

Cost: +3 × C7420022 per board (≈ 0.028 USD each), F1–F4 +0.016 USD each against 1812L050/60GR (F2 +0.064 against the
0805 part). Unique extended parts +C70113 +C7420022 −C19078719 −C269104 = **±0** (fix_check: 61 / 69 unique, +0).

Pre-order: check the KiCad `Fuse_1812_4532Metric` pads (1.125 × 3.4 mm, pitch 4.275 mm) against the JLCPCB footprint of
C70113 (datasheet land 1.78 × 3.2 mm, gap 3.2 mm) and `R_2512_6332Metric` against the JLCPCB footprint of C7420022
(datasheet land a 4.0, b 2.1, L 4.1 mm, letters per the p. 4 drawing). C70113 is up to 1.8 mm high.

**Mandatory prototype test (decision 81):** a hard short at J5.5 (behind F4/R56), and behind F1 (at D1/D2) and F3
(at D10/FB2), from a 30 V battery-like supply (low source impedance, short heavy leads). Scope the current; afterwards
inspect R54–R56 and F1/F3/F4 (cracks, discoloration, resistance). Must pass before installation.

Failure mode (safety): an overstressed series resistor fails **open**. For F4/R56 that is a permanently tripped panel
supply: all panel switches of that board (bilge forced run, navigation lights) and the panel LEDs stop working, bus
control over NMEA 2000 keeps working (decision 17), but unlike a tripped PTC it does not reset. For F1/R54 the board
loses its battery supply (USB still powers the controller); for F3/R55 the CAN transceiver side loses power. A brief arc
across an opening element at 30 V / ≈ 80 A cannot be excluded from the datasheets, which is why the 30 V short test is
mandatory. **A competent person must review F1–F4 and R54–R56 before installation.**

**L3 swaps (T-0026, Q-0019).**

| Ref | Old | New | Check | Result |
|---|---|---|---|---|
| FB1, FB2 | BLM18AG601SN1D 0603 | Sunlord GZ2012D601TF 0805, C1017 (basic) | Sunlord GZ catalogue (rev. 2024-06-19) p. 3: 600 Ω ± 25 % at 100 MHz, DCR ≤ 0.30 Ω, I_r 500 mA. FB1 carries VBUS only when the board runs from USB: buck input ≈ 3.3 V × 0.47 A / (0.85 × 4.6 V) ≈ 0.40 A peak < 500 mA; drop ≤ 0.12 V. FB2 carries the CAN-side current (≤ 77 mA). | adopted |
| F2 | SMD0805B050TF | 1812L050/60GR | depends on the PTC I_max check above | **not adopted**; F2 became mSMD050-60V C70113 in T-0118 (below) |
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
  transceiver (T-0030 CA-IS3050G) must be rechecked against it (done in §8.5: still LEN 1 / LEN 2).
- Dropout 2 V: NET-S minimum 9 V − D11 (≈ 0.4 V) − F3/FB2 (< 0.05 V) ≈ 8.5 V > 7 V needed. V_O 4.8–5.2 V over
  temperature (ISO1044 V_CC2 4.5–5.5 V).
- Capacitors: the datasheet's test circuit uses C_I 0.33 µF and C_O 0.1 µF. C13 was raised from 0.1 µF to **1 µF/50 V
  X7R 0805 (C28323, basic)**. C12 1 µF + C11 0.1 µF on the output are kept.
  T-0159: C13 stays on C28323, C12 is now C15849 (see "BOM merge" at the end of this section).
- Heat: (16 − 0.4 − 5) V × 45 mA ≈ 0.48 W normal traffic (same as the TPS7B91 plus 0.07 W from I_d). R_θJA 100 K/W (DPAK,
  Table 2) gives +48 K, so ≈ 98 °C at 50 °C enclosure air (T_J max 125 °C). Copper under the tab lowers that.
- **DPAK area:** body ≈ 6.6 × 6.1 mm plus leads, footprint ≈ 10.4 × 6.7 mm, against ≈ 3 × 3 mm for SOT-23-5. This is for
  `/system mechanical` (decisions 97, 98: no module width limit; board size set at layout).

**USB service port (T-0014, Q-0008).**
- README: USB-C is a service port only (battery-powered laptop or USB isolator).
- J3 shield is no longer tied to GND directly: new net `USB_SHIELD` → R13 1 MΩ 1206 (C17927, basic) ‖ C18 4.7 nF/1 kV
  X7R 1206 (Yageo CC1206KKX7RCBB472, C107198, extended; Yageo voltage code C = 1 kV) to GND, plus R14 0 Ω 0603 (C21189)
  **DNP** as the hard-tie option. Choice (auto): RC fitted, 0 Ω DNP. 1 MΩ bleeds static charge; 4.7 nF gives an RF/ESD
  return (Z ≈ 0.3 Ω at 100 MHz, ignoring ESL) but blocks the 50 Hz/DC loop to shore PE. No basic 4.7 nF part ≥ 250 V exists
  (searched 2026-11-02), so this is one new extended part. 1206 sizes keep creepage for ESD on the shield.
- **Update T-0119 (2026-11-03, owner Q-0061/Q-0062, decision 83 amends decision 31; supersedes auto decision 46):** C18 is now
  **1 nF/2 kV X7R 1206, FH 1206B102K202NT (C9196, basic)** – the part already used as C50–C53 (pdm-4ch) and C70/C114/C214
  (pdm-hc2). Footprint unchanged (`C_1206_3216Metric`); R13 1 MΩ fitted and R14 0 Ω DNP unchanged. Shield RC is now
  1 MΩ ‖ 1 nF: corner 1/(2π × 1 MΩ × 1 nF) ≈ 160 Hz (was ≈ 34 Hz with 4.7 nF). RF/ESD return |Z_C| ≈ 1.6 Ω at 100 MHz
  (was ≈ 0.3 Ω; ESL ignored in both figures). At
  50 Hz |Z_C| ≈ 3.2 MΩ, so the shore-PE loop still sees ≈ 0.76 MΩ (R13 ‖ C18), µA-level current. The 2 kV rating is
  higher than the old 1 kV for ESD on the shield. One unique extended part fewer (−C107198) on both boards.
- TLP/clamp check of the ESD part left by step 2 (H5VL10B): **no TLP curve is published**. Clamp data are 8/20 µs only
  (≤ 8 V at 1 A, ≤ 10 V at 5 A, Fig. 4). Extrapolating the 0.5 Ω dynamic resistance to the 8 kV contact first peak (≈ 30 A)
  gives roughly 20–25 V for the first nanoseconds (estimate, not datasheet). That is far below the replaced part's 40 V.
  The remaining margin comes from the ESP32-S3's own pin ESD structures. If TLP data are wanted before ordering, a part with
  published TLP (e.g. a USBLC6-2 type) is the alternative.

**Buck (T-0011, Q-0005).** TI SLUSEY1B §8.2.2.6: C_IN ≥ 2.2 µF rated about twice V_IN, plus 0.1 µF close to the pins.
§7.3.5/8.2.2.7: C_BOOT 0.1 µF ≥ 16 V. C2 is 100 nF/50 V X7R 0402 C307331 since T-0159.
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
T-0119: C107198 is gone again (C18 → C9196, basic, already on the BOM).

**BOM merge (T-0159, decisions 99 and 105, 2026-11-07).** Standard PCBA charges 1.53 USD per unique line. Values and nets do not change. Same edit on both boards, because all of these parts are on the shared sheets.

| Ref | Was | Now | Check |
|---|---|---|---|
| C2 boot | 0.1 µF C14663 0603 | C307331 0402 (100 nF/50 V X7R ±10 %) | TI SLUSEY1B §7.3.5, §8.2.2.7: 100 nF, X7R or X5R, ≥ 16 V. CB–SW abs max 5.5 V. Samsung curve below: 97 nF at 5 V |
| C12 VCC2 | 1 µF C52923 0402 (25 V) | C15849 0603 (50 V X5R ±10 %) | 0.70 µF at 5 V, against 0.60 µF for the old part. CA-IS3050G asks for 0.1 µF at VCC2 (C11), L78M05 C_O is 0.1 µF. Better than before |
| R9 | 68 k C23231 0603 | C36871 0402 | Both ±1 %, ±100 ppm/°C, Uniroyal thick film (series sheet V.3, §2.3, §11) |
| R10 | 22 k C31850 0603 | C25768 0402 | As R9. The 3.3 V setpoint tolerance does not change, so nothing in decision 30 or the budgets moves. Divider current ≈ 37 µA, ≈ 0.1 mW in R9, far below the 62.5 mW rating |
| C13 | 1 µF/50 V C28323 0805 | **unchanged** | Fails the DC-bias check on C15849, see below |

*C13 check.* Requirement: C_I 0.33 µF (L78M05 DS0425 rev. 24, p. 8, Table 4 header; a test-circuit value, the only input figure the datasheet gives). Bias at the clamp voltage: 29 V. Curves: Samsung Component Library simulation, https://weblib.samsungsem.com/mlcc/mlcc-ec.do?partNumber=CL10A105KB8NNN (DC Bias graph, Precise model, 25 °C, read 2026-11-07). The catalog and the part's spec sheet carry no curve for this part. Worst case below takes ±10 % tolerance and ±15 % temperature (X5R and X7R, catalog p. 54) as a factor of 0.9 × 0.85 = 0.765 on the 25 °C curve, which is a simple product of limits, not a measurement.

| Bias | C15849, X5R 0603 | C28323, X7R 0805 |
|---|---|---|
| 0 V | 1.06 µF | 1.01 µF |
| 5 V | 0.70 µF | 0.99 µF |
| 12 V | 0.31 µF | 0.87 µF |
| 16 V | 0.21 µF | 0.79 µF |
| 29 V | 0.10 µF (−90 %) | 0.55 µF (−46 %) |
| 29 V, worst case | **0.08 µF: fails** | **0.42 µF: passes** |

C15849 falls below 0.33 µF already at 12 V, before tolerance. C13 therefore keeps C28323 (decision 105's own outcome). Its line stays on both BOMs.

*Result.* Removed: C14663, C52923, C31850, C23231 on both boards. pdm-hc2: 64 unique parts (−4, `fix_check.py`), 6.12 USD per order. pdm-4ch: C36871 is new there because R9 is on the shared sheet (one line swapped for one line), so 59 unique parts (−3), 4.59 USD per order. The cost report's 6 and 7.65 USD assumed C13 too, which is 1.53 USD per board not saved.

*Layout.* New land patterns: C2, R9, R10 0402; C12 0603 (was 0402). C13 stays 0805.

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

### 8.5 CAN sheet: CA-IS3050G, TXD pull-up, barrier Y-cap and CMC footprints (T-0067, 2026-11-02)

Shared `can` sheet, identical on both boards. Owner rulings that frame this section:

- **EMC target (Q-0012, T-0019):** "IEC 60945 as a design target, no certification; one pre-compliance scan on the first
  prototypes decides the DNP footprints; the N2K shield stays unconnected at the node (4-pole J4)". J4 stays 4-pole.
- **CAN supply (Q-0031, T-0039):** "keep the isolated CAN side powered from NET-S (NMEA 2000 practice, LEN)". The bus
  side still runs from NET-S → F3 → FB2 → D11 → U6 (L78M05) → VCC2; nothing in this section changes that.

**U5 ISO1044 → Chipanalog CA-IS3050G (Q-0023, T-0030).** Source: Chipanalog CA-IS305x datasheet v1.10 (2024-07-02).
Every check passed, so the part was swapped:

| Check | CA-IS3050G | Against | Result |
|---|---|---|---|
| VCC1 | 2.5–5.5 V (§7.3); TXD V_IH ≥ 2 V, V_IL ≤ 0.8 V; RXD V_OH ≥ VCC1 − 0.8 V at 4 mA | +3V3 | pass |
| VCC2 | 4.5–5.5 V (§7.3), UVLO+ 3.9–4.4 V (§7.7) | U6 L78M05 V_O 4.8–5.2 V from NET-S (§8.3) | pass, supply unchanged (Q-0031) |
| Bus fault | CANH/CANL ±58 V abs max, CMR ±30 V (§7.1, §7.3) | NET-S ≤ 16 V, SMAJ18CA D10 clamp; same ±58 V as ISO1044 | pass |
| Loop delay | t_loop1/2 110–210 ns (§7.8) | ISO1044 ≤ 199 ns (t_PROP(LOOP1), 2.25–5.5 V). 250 kbit/s: 2 × (210 ns + 200 m × 5 ns/m) ≈ 2.4 µs < ≈ 3.5 µs sample point (87.5 % of 4 µs) | pass |
| TXD dominant timeout | 2–8 ms → minimum 5.5 kbit/s (§7.8, §9.5.4) | 11 dominant bits at 250 kbit/s = 44 µs | pass |
| Isolation | 5 kV_RMS (UL 1577), V_IORM 1414 V_pk, reinforced (VDE 0884-17); CLR/CPG 8 mm; C_IO ≈ 0.5 pF (§7.4, §7.5) | ISO1044: 3 kV_RMS | pass (better) |
| Pinout | SOIC8-WB: 1 VCC1, 2 RXD, 3 TXD, 4 GND1, 5 GND2, 6 CANL, 7 CANH, 8 VCC2 (Table 6-1; CA-IS3052G has 2/3 swapped, Table 6-2) | ISO1044 D: 5 CANL, 6 CANH, 7 GND2 – **not pin-compatible** | new symbol |
| Package | SOIC8-WB, body 7.40–7.60 × 5.75–5.95 mm, lead span 11.25–11.75 mm; land 0.60 × 1.80 mm pads, 10.90 mm row pitch (Fig. 11-1) | KiCad `Package_SO:SOIC-8_7.5x5.85mm_P1.27mm`: 0.6 × 1.8 mm pads at 10.65 mm pitch, pad 4.425–6.225 mm from centre, covers the foot (toe ≤ 5.875 mm) | accepted |
| JLCPCB | C528763, extended, stock 5970 (2026-11-02), EasyEDA footprint present, 0.917 USD at 10+ | ISO1044BDR C2878225, 1.62 USD | −0.71 USD/board |
| Heat | P_D2 ≤ 175 mW, P_D1 ≤ 25 mW (§7.3, worst case), R_θJA 110.1 K/W → ≤ +22 K | – | negligible |

- Symbol: `ESP32-PDM:CA-IS3050G` in `lib/ESP32-PDM.kicad_sym`, a copy of the ISO1044BD graphic with the pins renumbered by
  name. The pin points are unchanged, so no wire moved. The netlist confirms U5.5 = GND_CAN, U5.6 = CANL, U5.7 = CANH.
  2026-11-03 (T-0076, package T-0078): the symbol had pins 2 = TXD and 3 = RXD (the CA-IS3052G order); corrected to
  2 = RXD, 3 = TXD (v1.10 p. 5, Fig. 6-1/Table 6-1) by renumbering only, so the pin points did not move: /IO17 → U5.3 TXD,
  /IO18 → U5.2 RXD. R70 stays on TXD (/IO17, now U5.3).
- **LEN recheck.** I_CC2 dominant 44 typ / 73 max mA, recessive 3 typ / 12 max mA (§7.7). The datasheet gives no
  50 %-duty figure (the ISO1044 check used 38 mA). Worst-case average (73 + 12) / 2 = 42.5 mA, plus the L78M05 I_d
  6 + 0.8 mA, gives 49.3 mA ≤ 50 mA → **LEN 1**, with only 0.7 mA margin and every value at its maximum. Typical ≈ 29 mA.
  Continuous dominant: 73 + 6.8 = 79.8 mA → LEN 2 (was 76.8 mA). The 2–8 ms dominant timeout releases a stuck-low TXD,
  so a continuous dominant needs a toggling fault. Measure the NET-S current on the first prototype before declaring LEN 1.

**TXD pull-up R70 (Q-0039, T-0048).** R70 10 kΩ 0402 (C25744, basic, already on the BOM) from TXD (/IO17) to +3V3. The
CA-IS3050G TXD is "weakly pulled-up internally" (Table 9-2, note 2; I_IH/I_IL ≤ 20 µA), and the ruling applies the same
pull-up to it. Cost when TXD is low: 0.33 mA. R70 holds TXD recessive while GPIO17 is high-impedance or only weakly
pulled during reset. A glitch actively driven low by the pin would not be removed: check TXD and the bus with a scope at
power-up on the prototype.

**Barrier Y-capacitor C70 and CMC FL1 (Q-0004, T-0010).** Both are footprints for the pre-compliance scan (Q-0012).

- **C70, DNP:** 1 nF/2 kV X7R 1206, FH 1206B102K202NT (C9196, basic, the same part as C50–C53), from GND_CAN to GND.
  - It is a capacitor only. No resistor or other DC path crosses the barrier, so the NMEA 2000 isolation stays at DC.
  - At 1 nF the ideal impedance is ≈ 1.6 Ω at 100 MHz. 1 nF is the low end of the 1–2.2 nF range, chosen to reuse a
    part already on the BOM.
  - The part is not safety-certified (Y2). Both sides are SELV (N2K NET-C and the boat's DC negative), so the barrier is
    functional isolation and a Y rating is not required.
  - If the scan asks for C70 and a fail-open part is wanted, a certified Y2 capacitor can replace it on the same
    1206 pads.
- **FL1, DNP:** cjiang FACT4532-510-2P-T (C20624726, extended).
  - Ratings: 51 µH (+50/−30 %) at 100 kHz, Z ≥ 1 kΩ (typ 2.8 kΩ) at 10 MHz, DCR ≤ 1 Ω per line, 50 V DC, I_r 200 mA.
  - Package 4.5 × 3.2 × 2.6 mm, AEC-Q200, intended for CAN (datasheet §1, §8).
  - Windings 1→2 and 4→3, dots on 1 and 4 (§6). The bus side is on pins 1 and 4 and U5 on 2 and 3, so CM current
    adds and DM current cancels.
  - Footprint placeholder: `Inductor_SMD:L_CommonModeChoke_Coilank_ACM4532` (pads 1.15 × 1.55 mm at ±1.825/±1.125 mm).
    The cjiang land is 1.3 × 0.9 mm pads, L 5.5, G1 2.9, H 3.4, G2 1.6 mm. Both cover the electrodes (D 0.70, E 0.85 mm).
  - **The cjiang drawing does not number the pads:** check the pad numbering against the JLCPCB footprint of C20624726
    before FL1 is fitted. With one pair swapped, the choke works in differential mode and corrupts the bus.
- **R71/R72, fitted:** 0 Ω 0402 (C17168, basic, the same part as R43), one across each winding (CANH_BUS–CANH_XCVR,
  CANL_BUS–CANL_XCVR). To fit FL1, remove R71 and R72.
- **Order on the line:** J4 → D9 (PESD2CAN at the connector) → FL1/R71/R72 → U5. The TVS stays on the cable side of the
  CMC, as E6 recommends.

**Failure modes.** No safety-relevant output is touched; the panel switches still work without the MCU and the bus.
- C70 shorted (only if fitted): GND_CAN joins GND. The node loses its isolation and the N2K ground can carry DC return
  current, a ground loop. No hazard on SELV, but N2K expects isolated nodes.
- R71/R72 or FL1 open: that CAN line is cut and the node drops off the bus. Outputs stay in their last state or the
  hardware switch state.
- U5: the dominant timeout (2–8 ms) keeps a stuck TXD from blocking the bus.

**Cost (10 pcs):**
- U5 −0.71 USD/board; R70, R71, R72 ≈ +0.005 USD; C70 and FL1 are DNP. Net ≈ −0.70 USD/board.
- No new unique fitted part: C25744 and C17168 are already fitted elsewhere, and C528763 replaces C2878225.
- FL1 (C20624726) becomes one extra extended part only if the scan asks for it.

### 8.6 Reverse-battery blocker Q30/U30 on VS (`pdm-4ch`, T-0121, owner ruling Q-0054, 2026-11-03)

Finding EMC E16 (`docs/reviews/2026-11-03-emc-system.md`): C31 is a polarised electrolytic with no reverse rating and
nothing in front of it. The owner ruled (Q-0054): add a reverse-blocking element on VS in front of the bulk capacitors
on pdm-4ch in this revision, sized for the 40–50 A path and checked with the heat budget at 40 °C. pdm-hc2 keeps
decision 40 (keyed J10, warning). J10 on pdm-4ch is keyed too (decisions 98, 104, one-way fit checked on a sample).

**Re-selected for 16 A (decisions 103, 104, T-0158, 2026-11-07).** The first pdm-4ch is 16 A only, all BTT6050, with no BTT6010 build. Q30 is now AGM601LL C5464765 instead of IPT007N06N C122552, with the same pin order and footprint. The 40–50 A in the ruling above and the 32 A of decision 95 no longer apply to this board.

**Circuit (root sheet of pdm-4ch only).** J10.1 → `VBAT_IN` (D30, C30) → FL30 (DNP) / JP30 → new net `VBAT_FL` →
Q30 source; Q30 drain → `VS` (C31, C104–C404, U11–U14, F1, F4, R60). U30 LM74500-Q1: SOURCE (pin 5) and EN (pin 1) on
VBAT_FL, GATE (pin 6) → Q30 gate, VCAP (pin 4) → C32 → VBAT_FL, GND (pin 2) → GND, pins 3/7/8 N.C. D31 (T-0143, owner
ruling Q-0067) sits across Q30: VS (drain) to VBAT_FL (source).

| Ref | Part | Facts |
|---|---|---|
| Q30 | AGM-Semi AGM601LL, TOLL, C5464765, extended, 0.85 USD @1, stock 2016 (2026-11-07) | `docs/part-facts/C5464765.md` (VER2.65): VDS 60 V, VGS ±20 V, VGS(th) ≤ 2.2 V, RDS(on) max 1.6 mΩ (10 V, 30 A, 25 °C), ≈ 2.35 mΩ at 100 °C and ≈ 2.9 mΩ at 150 °C (derived: Fig. 6 × max), Tj 175 °C, RthJC 0.7 K/W max, RthJA 50 K/W with no copper area stated, body diode IS 223 A, VSD ≤ 1.2 V at 20 A, ISM not given, IDM 892 A, Ciss 5.47 nF typ (no max), Qg 102 nC typ. Pin 1 G, pins 2–8 S, tab D = KiCad `Infineon_PG-HSOF-8-1` pads 1 G, 2 S, 3 D |
| U30 | TI LM74500-Q1 (LM74500QDDFRQ1), SOT-23-THIN-8 (DDF), C5219210, extended, 1.82 USD @1, stock 2923 | `docs/part-facts/C5219210.md` (SNOSDB7): SOURCE ±65 V abs max (±60 V recommended), GATE–SOURCE abs max 15 V, gate drive VCAP−SOURCE 10.3/11.6/13.0 V on, 13.9 V max; **no reverse-current blocking** (FET fully on both ways); EN tied to SOURCE = always on; IQ 80/130 µA; Tj −40…150 °C; footprint KiCad `TSOT-23-8` (0.65 mm pitch, 2.9 × 1.6 mm body) |
| C32 | 1 µF/50 V X5R 0603, Samsung CL10A105KB8NNN, C15849 (basic, already on the BOM) | `docs/part-facts/C15849.md`; VCAP capacitor |
| D31 | hongjiacheng SMDJ40CA, SMC / DO-214AB, C42371557, preferred, 0.22 USD @1, stock 10271 (2026-11-04) | `docs/part-facts/C42371557.md`: bidirectional, VRWM 40 V, VBR 44.4–49.1 V (1 mA), VC 64.5 V at IPP 46.5 A (10/1000 µs), IR ≤ 2 µA at VRWM (25 °C), 3 kW 10/1000 µs on 8 × 8 mm copper per terminal, VBR +0.1 %/K, derating 60 % at 75 °C. Footprint `Diode_SMD:D_SMC` as D30 |

Why this topology:
- **P-FET rejected.** The best 60 V P-FETs at JLCPCB are 3.5–4.7 mΩ at 25 °C (≈ 6–7 mΩ hot): ≈ 3.5 W at 24 A and
  ≈ 10 W at 40 A in one package.
- **Ideal-diode controller rejected.** It blocks VS → VBAT_IN, so a positive PROFET output surge (OUT → body diode →
  VS) could no longer reach D30, and VS would need its own TVS (a change of invariant 4).
- **LM74500-Q1 + N-FET.** It is not an ideal diode: it keeps Q30 fully on in both directions and turns it off only when
  the input is reversed or too low. Requirements of the ruling:
  - (a) Invariant 1: U30 is powered from VBAT_FL with EN tied to SOURCE: no ESP32, no 3.3 V, no firmware. The panel
    supply (F4 on VS) works as before.
  - (b) Invariant 3: Q30 VDS 60 V and U30 SOURCE 65 V abs max are above the 48.4 V D30 clamp. VDS = VS − VBAT_FL ≤ 48.4 V
    holds only for a steady reversal with VS discharged (D30 clamps VBAT_IN). For a negative transient with VS charged,
    VS adds to the clamp (about 77 V without a TVS, above Q30's 60 V), and D31 clamps VDS: figures and limits under
    "D31 across Q30" below. Q30's gate never sees the battery directly. U30 drives it only from VCAP (≤ 13.9 V
    above SOURCE, abs max 15 V) or ties it to SOURCE (reversed or off). The ±20 V VGS rating is therefore never
    reached and no zener is needed (U30 datasheet: zener only for a FET with VGS rating < 15 V).
  - (c) Invariant 4: with the battery connected, Q30 is enhanced and conducts drain → source, so OUT → PROFET body diode
    → VS → Q30 → VBAT_IN → D30 stays as before (≤ 2.9 mΩ more; IDM 892 A, no pulse width stated, against about 62 A at D30's 3 kW and 48.4 V; 0.18 V extra drop there, 0.10 V more than with IPT007N06N). No TVS from VS to GND: the
    only TVS added, D31, is across Q30 (VS to VBAT_FL). This surge path stays and invariant 4 is unchanged.
  - (d) Turn-on: when the battery is connected, C31 + C104–C404 (≈ 109 µF nominal) charge through Q30's body diode
    (IS 223 A continuous, ISM not in the datasheet; ≈ 3.3 mC at 30 V, ≈ 3 mJ in the diode) before U30 enhances the gate. Q30 therefore
    turns on with VDS below about 1 V and never works in its linear region at battery voltage. That is the same
    inrush as before T-0121, now with the diode in series. The peak is set by the cable and C31's ESR and was not calculated, and AGM601LL's SOA curve (Fig. 8) was not read: the linear region is not used.
- **C32 sizing and gate drive.** U30 wants C(VCAP) ≥ 10 × Ciss = 55 nF (5.47 nF typ; the datasheet gives no max; recommended minimum
  0.1 µF, so 0.1 µF is the real floor). C32 stays 1 µF/50 V, about 180 × Ciss. It stays above both unless it loses more than 90 %; the bias
  curve is not in the facts file, but an 0603 50 V X5R part usually keeps far more. The worst VCAP at turn-on, 10.3 V, is above the
  10 V at which RDS(on) max is specified, and 13.9 V max is below VGS ±20 V, so Q30 is fully enhanced and needs no zener. The gate charge sags C32 by about 0.1 V.
  Gate-on time ≈ 75 µs + C32 × 6.5 V / I_CP = 22 ms typ (300 µA), ≤ 40 ms at the 162 µA minimum, to the 6.5 V UVLO. Until then the load
  current flows in the body diode: at 16 A with VSD ≤ 1.2 V ≈ 19 W for < 0.1 s, i.e. ≈ 13 K rise with RthJC 0.7 K/W. Harmless.
- **CIN.** U30 asks for ≥ 22 nF at SOURCE. C30 (2.2 µF/100 V) sits on the same node through the JP30 copper bridge. If
  FL30 is ever fitted instead of JP30, C30 is behind the ferrite. Then check whether U30 needs its own 22 nF–100 nF at
  SOURCE.

**Heat at 40 °C (decision 9, `tools/heat_budget.py`, run 2026-11-07, T-0158).** Q30's RDS(on) is added to the shared path.
`--r-path 0.0069` = the 4 mΩ default + 2.9 mΩ (the 150 °C value, conservative: it is ≈ 2.1 mΩ at the 16 A temperature), `--p-other 2.3`:

| Case | IPT007N06N (`--r-path 0.00505`) | AGM601LL (`--r-path 0.0069`) |
|---|---|---|
| 4 × BTT6050 at 4 A (16 A) | inside 45.5 °C, Tj 102 °C | inside 45.8 °C, Tj 102 °C |
| 4 × BTT6050 at 4.5 A (above the rating) | Tj 125 °C, marginal | Tj 125 °C, OVER (the tool's limit falls between the rounded figures) |
| 4 × 4 A in 50 °C air (decision 97, `--r-box 0 --ambient 50`) | – | Tj 107 °C |

The 4 A channel rating stands. Q30's own junction, solved by hand with RDS(on) interpolated linearly from the max curve
(1.6 mΩ at 25 °C, ×1.14 at 50 °C, ×1.47 at 100 °C, ×1.80 at 150 °C) and the enclosure air from the tool:

| Input current | Enclosure air | Q30 loss | Q30 Tj at 40 K/W | at 50 K/W | **at 62 K/W** |
|---|---|---|---|---|---|
| **16 A (board input limit, decision 103)** | 45.8 °C | 0.51–0.55 W | 66 °C | 72 °C | **80 °C** |
| 16 A, decision 97's full rating | 50 °C | 0.52–0.56 W | 71 °C | 77 °C | 85 °C |
| 12 A (3 A per channel, decision 97's hot case) | 65–70 °C | 0.30–0.32 W | 77–83 °C | 80–86 °C | 85–90 °C |
| 20 A (not rated: fuse tolerance or overload) | 46 °C | 0.86–0.97 W | 80 °C | 91 °C | 106 °C |
| 32 A (the old limit, not allowed on this version) | 48.4 °C | – | 179 °C, above Tj max | – | no solution |

**Which RthJA.** AGM601LL's 50 K/W has no stated copper area (**UNVERIFIED**), so it is not relied on. The 40 and 62 K/W are Infineon's figures for its own TOLL package (6 cm² 70 µm Cu / minimal pad, `docs/part-facts/C122552.md`), used as an analogue for the same outline: an assumption, not an AGM figure. AGM's higher RthJC (0.7 against 0.4 K/W) adds under 0.2 K at this loss. The result is not sensitive to it: at 16 A Q30 stays at or below 125 °C up to RthJA ≈ 118 K/W (112 K/W in 50 °C air).

**Copper rule (replaces the 6 cm² of decisions 90 and 95).** ≥ 2 cm² of 2 oz VS copper joined directly to Q30's drain tab. That is the tab land (0.8 cm²) plus D31's 8 × 8 mm terminal copper (0.64 cm²), rounded up, so it asks for no copper the layout does not already need. The Tj above is taken at the 62 K/W minimal-pad figure, so the 2 cm² is margin, not a calculated RthJA. U30 loses microwatts (80–130 µA).

**Why AGM601LL (selection, T-0158).** No basic or preferred part fits: the lowest 60 V N-FET with no loading fee is 90 mΩ (`jlc_search`, catalogue of 2026-11-06), ≈ 23 W at 16 A. AGM601LL passes all criteria: VDS 60 V, VGS ±20 V, enhanced at 10.3 V, C32 unchanged, stable Tj at 16 A. The land was checked against the drawing (VER2.65 p. 5): body D 10.25–10.55, E 9.75–10.05, H 11.55–11.85 mm, pitch 1.20 mm, lead 1.55–1.85 mm long, 0.65–0.85 mm wide. Exposed pad from the tab end to 7.0 mm back (H2, or H1 6.95 in the second table), about 9.1 mm wide, 9.8 mm at the fingers. In the KiCad land, measured from the package centre: lead pads x −6.65…−3.85 over leads −5.85…−4.15; tab land x −1.35…6.65, ±4.85 mm (±5.05 mm at the fingers), over exposed pad about −1.15…+5.85. **Pass; `Infineon_PG-HSOF-8-1` unchanged.** Pad width 0.8 mm against lead width 0.65–0.85 mm, as tight as on IPT007N06N (0.70–0.90 mm); the exposed-pad extents are read from the drawing. The symbol stays `ESP32-PDM:IPT007N06N` with value AGM601LL (same pins); keep the value when updating symbols from the library.

**D31 across Q30: residual risk the owner accepted (T-0143, ruling Q-0067, safety).** In a negative transient on VBAT_IN
with VS charged, D31 conducts instead of Q30 avalanching, and it keeps conducting until its voltage is back at its
breakdown voltage. While D30 holds VBAT_IN negative, VS can therefore fall below 0 V. The owner accepted VDS 59.4 V worst
case and VS down to about −4 V for the 31 A bounding spike. The ruling's short figures depend on the following:

- **C31 is briefly reverse-biased during such a spike.** Its datasheet gives no reverse rating
  (`docs/part-facts/C487384.md`), so its behaviour under −4 V is unverified.
- **VS.** Floor = VBR min − (D30 VBR max + 0.374 Ω × I) = 44.4 V − (36.8 V + 0.374 Ω × I). VS stays ≥ 0 V up to about
  20.3 A and reaches about −4.0 V at 31 A (−2.4 V with the 0.75 Ω load). So VS is negative for every source current
  between about 20.3 A and 31 A, in proportion. At 31 A, VS crosses 0 V after about 170 µs and stays negative until the
  spike ends (about 830 µs of a 1 ms pulse).
- **VDS.** VBR max + chord = 49.1 V + 0.331 Ω × I gives 59.4 V at 31 A (59.7 V at the 32 A of decision 92). This figure is at
  25 °C and at a source short-circuit current of at most 31 A. It depends on D31, not on Q30, and AGM601LL has the same 60 V minimum (at 250 µA, against 1 mA for IPT007N06N), so the limit still holds (T-0158).
  - With the TVS at 47 °C, VDS is about 60.4 V, slightly above Q30's 60 V 25 °C minimum. Q30's own rating rises with temperature too (IPT007N06N: about
    63 V at 125 °C; AGM601LL's coefficient is not in the facts file). Q30 may then take a small share in avalanche, far inside EAS 1225 mJ (Tj(start) 25 °C), since the whole pulse is about 190 mJ.
  - A source tuned to 31 A at the D30 clamp drives more at first, so it stays under 60 V with SMDJ40CA only for Us ≥ about
    334 V. An inductive load on the bus is limited by its own running current and fits the 31 A model.
- **Pulse rating.** Margin about ×5.3 at 25 °C for a 31 A, 1 ms pulse (about 190 mJ, 1.84 kW peak, Fig. 1 read at the
  equivalent pulse length). Multiply by 0.6 for a TVS at 75 °C (Fig. 2).
- **Textbook pulse.** ISO 7637-2 pulse 1 (12–15 A, figures from secondary sources): VDS 53.1–54.1 V, VS +2 V or above.
- **Unverified.** Whether such spikes occur on a real bus is unverified (T-0130). All figures use the straight chord from
  VBR max to VC at IPP, because the maker gives no VC at lower currents.

**Recheck with AGM601LL (T-0158).** While D31 clamps, Q30 is off, so VS (−4.0 V at 31 A), the pulse energy (about 190 mJ in D31, ×5.3 margin) and the reversed-battery case do not depend on the FET. Its lower Qg (102 against 216 nC) turns it off faster. Decision 96's limits and D31 are unchanged.

Calculation and method: `docs/reviews/2026-11-04-fix-pdm-4ch-T-0137.md`. The prototype test list in
`hardware/pdm-4ch/STATUS.md` measures VDS and VS during a negative pulse.

The other VS branches at −4 V (checked against the netlist, T-0143):

| Branch | At VS ≈ −4 V |
|---|---|
| F1 → R54 → D2 → U3, C1 | D2 (DSK16, VRRM 60 V) blocks; U3 and C1 do not see it |
| F1 → R54 → D1 (SMAJ30CA to GND) | Bidirectional, VRWM 30 V: does not conduct |
| F4 → R56 → D55 → panel supply | D55 (DSK16) blocks; SW_SUPPLY does not see it |
| C103–C403, C104–C404 | Non-polar ceramics |
| U11–U14 | 4 V is well inside −VS(REV) 28 V (T-0137). Load current flows through the body diode: about 1 A for a 3 Ω channel at 4 V, under the 2.3 A that the 28 V / RL ≥ 12 Ω rating allows. D101–D401 block reverse current in the GND pins |
| R60 → IO10 | Current limited by 220 k to under 70 µA (T-0137), about 17 µA at −4 V. C60 with R60 ‖ R61 has τ ≈ 2 ms, so VBAT_SENSE barely moves in a 1 ms spike |

F3 and the CAN supply are not on VS. So C31 is the only polarised part exposed, as the ruling assumes.

D31 dissipates nothing in steady state, so it does not change the heat budget above.

**Reverse battery now.** A reversed battery puts VBAT_IN negative. U30 ties GATE to SOURCE, Q30 is off and its body
diode is reverse-biased. VS stays near 0 V.
- **Steady reversal ≤ 28 V:** D31 does not conduct (VRWM 40 V, VBR ≥ 44.4 V); the same holds up to D30's VRWM of 30 V. Only
  leakage flows (Q30 IDSS ≤ 1 µA at 25 °C, D31 IR ≤ 2 µA, D30, C30 is a non-polar MLCC; U30's reverse SOURCE current is
  not in the facts file). D31's leakage into the R60 divider (242 k) gives VS at most about −0.48 V. That is an upper bound:
  IR is specified at 40 V and 25 °C only, and its hot value is not in the datasheet. A leakage of this size is far below
  C31's own 63 µA forward leakage limit, so "no time limit" stays.
- **VS charged at the moment of reversal:** D31 conducts once, until VS is at about VBR − 28 V (+16 to +21 V), VDS at most
  about 57 V (29 V + 28 V). This is about 40–70 mJ from the capacitors, starting at under 38 A (below IPP 46.5 A), far
  inside the pulse rating. VS does not go negative; the rest discharges through the loads and R60.
- **Above D30's VBR (about 33 V):** D30 conducts and the battery fuse has to clear, as before. U30 is rated to −65 V and Q30
  to 60 V, above the 48.4 V clamp while VS is discharged.

Assumption: the loads return to the same negative bus as J10.2 (whole battery reversed). If
only the two J10 leads are swapped while the loads return elsewhere, the case has not been analysed. Keyed J10
(decision 34) and checking the polarity remain the first protection.

**Failure modes (safety: the panel supply F4 for navigation lights and bilge forced run hangs on VS).**
- **Q30 fails short** (drain–source): no reverse protection, exactly as before T-0121. C31 can vent with a reversed
  battery and the BTT6050 limits (28 V, < 2 min, RL ≥ 12 Ω) apply. Normal operation is unaffected, so this fault is
  not visible in use.
- **Q30 fails open**, or the JP30/Q30 copper is interrupted: the board is dead, panel switches included. Navigation
  lights and the bilge forced-run switch on the panel stop working. The float-switch circuit stays independent of
  the PDM (invariant 8), so the bilge pump still runs on its float.
- **U30 fails (no gate drive, e.g. C32 open or U30 dead):** Q30 conducts only through its body diode (≈ 1 V, ≤ 1.2 V at 20 A). At 16 A
  that is about 16–19 W, far above what the package can shed on the PCB. Q30 heats until it fails, usually
  short (→ first case), possibly open (→ second case). VS sits ≈ 1 V low. R60/VBAT_SENSE measures VS, not VBAT_IN, so the firmware
  cannot see the drop directly. See the suggestion in the T-0121 report.
- **U30 fails with GATE shorted to SOURCE:** same as "U30 fails".
- **U30 or C32 short to GND:** U30 SOURCE pin to GND = battery short behind JP30, cleared by the battery fuse. C32 sits
  between VCAP and SOURCE, not to GND.
- **D31 fails short:** it bypasses Q30, so there is no reverse protection. Normal operation is unaffected, so this fault
  is not visible in use: the same as "Q30 fails short".
- **D31 fails open:** back to Q30 avalanche in a negative transient with VS charged (T-0132: about 60–63 V and 80–115 mJ in
  Q30). AGM601LL's EAS 1225 mJ is for Tj(start) 25 °C, 70 A, 0.5 mH (≈ 0.6 ms) only, and the facts file has no hot avalanche curve, so the margin at its ≈ 66–80 °C at 16 A is **unverified**. IPT007N06N's was about 1–2× in its hot 40 A case. Also not visible in use.
- **More than 16 A through Q30 and J10 (T-0158):** nothing on the board limits the sum of the outputs, so the battery fuse has to. The channels' own limits lie above 4 A, so they do not hold the total at 16 A. About 20 A is still stable (Q30 ≈ 80–106 °C). Four BTT6010 at 8 A (32 A, unsupported on this version) would take Q30 to about 179 °C or into runaway: it fails short (first case above) or open (second case). J10 itself has margin (30 A UL).
- **Bad J10 joint or a loose plug (T-0158):** the heat appears at the contact, not in Q30. A cold joint can overheat at 16 A in the battery path, and a plug that lets go makes the board dead, panel switches included (as "Q30 fails open"). Check the joints and the plug screws; the drawings give no contact resistance.
- **pdm-4ch battery plug put in a pdm-hc2 J11 socket (T-0158, decision 104):** both are the 7.62 mm set, so it physically fits when both boards sit in one installation. Decision 98's keying holds only within one board. The owner's choice is listed in `hardware/pdm-4ch/STATUS.md`; label the plugs until then.
- The TVS's own failure mode, short or open, is not in its datasheet (`docs/part-facts/C42371557.md`, unverified), so assume
  either case can happen.

A competent person reviews this reverse-battery circuit, J10, D31 and the failure modes above before installation, because F4
feeds the panel switches: the navigation lights and the bilge forced run depend on Q30 conducting.

**PCB rules (T-0121, T-0158).** Q30 sits in the 16 A path between J10 and the VS copper. Use VBAT_FL copper (source pins 2–8) and
VS copper (drain tab) as wide as the existing VS copper, on both layers with stitching vias. Use ≥ 2 cm² of 2 oz
copper joined directly to the drain tab (VS), the rule derived under "Heat" above. Keep U30 next to Q30 with short SOURCE and GATE traces (U30 §11.1). Keep C32 at
U30 but away from Q30's hot tab. Keep the VS loop from the four switches through Q30 to D30 short and wide (invariant 4
path). Place D31 directly across Q30's drain tab and source pins, short and wide (T-0143); its 3 kW rating assumes 8 × 8 mm
copper per terminal. Before ordering, check the KiCad footprints `Infineon_PG-HSOF-8-1` (Q30) and `TSOT-23-8` (U30) against the
JLCPCB footprints of C5464765 (`TOLL-8_L10.4-W9.9-P1.20-LS11.7-BL_2`) and C5219210. The U30 land pattern in the datasheet: 1.05 × 0.45 mm pads, 2.6 mm column pitch.

**Cost.** Q30 0.85 + U30 1.82 + C32 0.01 ≈ 2.7 USD per board at 1 pc (T-0158; 5.4 USD with IPT007N06N), plus two extended loading fees (≈ 3 USD each per
order). D31 (T-0143): +0.22 USD per board, one more unique preferred part, no loading fee. Alternative checked: 2 × BSC014N06NS (C113391, 1.45 mΩ max each, 1.52 USD, `docs/part-facts/C113391.md`) in
parallel (≈ 1.1 mΩ hot, 3.03 USD) would also work, but it is two parts and more copper area for the same unique-part count; a
single one gives ≈ 4.3 W at 40 A and is too hot.

**Cheaper Q30 checked at 40 A and dropped (T-0126, cost lever L1, 2026-11-04; record, taken up at 16 A in T-0158).** AGM-Semi AGM601LL (C5464765, TOLL, 0.85 USD,
`docs/part-facts/C5464765.md`, datasheet VER2.65): 60 V, VGS ±20 V, EAS 1225 mJ, Tj 175 °C, pin 1 G / 2–8 S / tab D.
The 1.25 mΩ in the cost report is **typical**; the maximum is **1.6 mΩ** (10 V, 30 A, 25 °C), and Fig. 6 gives ×1.47 at
100 °C and ×1.80 at 150 °C (≈ 2.9 mΩ at 150 °C, max). RthJA 50 K/W has no stated copper area, there is no Ciss max and no
pulsed body-diode current. Q30 junction solved as above with the max curve (enclosure air 45.7 / 46.6 / 52.5 °C, from
`tools/heat_budget.py --p-other 2.3 --r-path 0.0069` = 4 mΩ + 2.9 mΩ hot):

| Input current | IPT007N06N max curve, 40 K/W (check of the method) | AGM601LL max curve, 40 K/W | AGM601LL max curve, 50 K/W |
|---|---|---|---|
| 16 A | 54 °C | 66 °C | 72 °C |
| 24 A | 67 °C | 101 °C | 121 °C |
| 40 A | 124 °C | no solution below 175 °C (thermal runaway) | no solution |

Even the typical 1.25 mΩ held at its 25 °C value would give 2.0 W and ≈ 132 °C at 40 A, which is above 125 °C. Making
it pass would need RthJA ≈ 17 K/W (more copper or a second FET, neither in the item). The channel ratings would have
held: 4 × 4 A Tj 102 °C (4.5 A now OVER), mix 91/103 °C, 4 × 8 A 93 °C. **Lever dropped. Q30 stays IPT007N06N C122552.**
Rechecked at the 32 A limit of decision 95 (same method, air 48.4 °C): AGM601LL ≈ 179 °C at 40 K/W, above its 175 °C Tj max and with the 150 °C curve point extrapolated, so the lever stays dropped.

### 8.7 Sign-of-life LEDs, unfitted service footprint J6 (T-0160: T-0150, T-0151, T-0152; owner rulings 2026-11-06; 2026-11-07, auto)

Root sheet, controller part, the same on both boards except J6 pins 4–6 (below). Facts: ESP32-S3-MINI-1-N8
`docs/part-facts/C2913206.md` (T-0160 section), KT-0603R `docs/part-facts/C2286.md`, CA-IS3050G `docs/part-facts/C528763.md`.

**Pin checks (ESP32-S3-MINI-1 v1.7 Table 3-1; ESP32-S3 v2.2 Tables 2-1, 2-4, 2-14, 3-5).** None of the pins is a strapping
pin, and none is used inside the N8 module: N8 has quad flash and no PSRAM, so IO33–IO37, which are the octal-SPI
lines, are free. IO26 is used only by the N4R2 PSRAM. At reset: IO13, IO35–IO37 and IO42 are inputs with no pull;
TXD0 (GPIO43) and RXD0 (GPIO44) have a weak pull-up, and TXD0 carries the ROM boot log. IO42 is the MTMS pad, but with the default eFuses JTAG
runs through USB Serial/JTAG, so the pad is a plain GPIO (the T-0051 rule never to burn `EFUSE_STRAP_JTAG_SEL` stays).
IO45/IO46 (strapping) are not used.

**LEDs (T-0150).** One new BOM line: KT-0603R red 0603, C2286 (basic). The resistors are 2.2 k 0402 C25879, which is already on
the BOM, so the change adds +4 parts and +1 unique line per board.
- D8 + R67: power LED from +3V3 to GND. D7 + R59: status LED from IO13 (R59) to GND, so it lights while IO13 is high.
- Current: Vf ≈ 1.85 V at 1 mA (typical curve, C2286 p. 5; nothing is plotted below 1 mA), so
  (3.3 − 1.85) V / 2.2 kΩ ≈ 0.66 mA, or ≈ 0.7 mA if Vf is a little lower at this current. The LED is rated 25 mA at 25 °C,
  derated to about 6–7 mA at 85 °C, so ≥ 9× margin. Dissipation is ≈ 1.2 mW in the LED and ≈ 1 mW in the resistor.
- Brightness: the relative-intensity curve gives ≈ 0.06 at 1 mA, so ≈ 0.04 at 0.66 mA, which is about 6–12 mcd from the
  145–300 mcd bins. This is extrapolated, not a datasheet value. It is a visible indicator indoors and dim in daylight.
- IO13 drive: the default drive is 20 mA, and VOH ≥ 0.8 × VDD is specified into a high-impedance load. Even at the
  2.64 V floor the LED gets ≈ 0.38 mA and still lights. With IO13 undriven (input, no pull, also during the 60 µs power-up glitch) the
  LED is off. Firmware must not enable IO13's internal 45 k pull-up, or the LED glows faintly (≈ 35 µA).
- **Continuous draw:** D8 draws ≈ 0.7 mA (≈ 2.3 mW from 3.3 V) whenever 3.3 V is up, also in Eco and Sleep (decision 13).
  No GPIO can switch it off. On the battery side that is ≈ 0.1 mA at 24 V and ≈ 0.2 mA at 12 V with ideal
  conversion; the LMR51610's light-load efficiency is not bounded here, so the real figure is higher. D7 adds ≈ 0.7 mA
  while lit, and firmware turns it off in Sleep (IO13 is an RTC GPIO and can be held low). The controller power budget
  in ARCHITECTURE carries both figures. Heat: ≈ 5 mW against the 2.3 W `p_other`, negligible, so no output rating changes.
- Invariant 1: the LEDs hang on +3V3 and IO13 only and do not touch the switch-to-output path.
- Failure modes: an LED failing short leaves ≈ 1.5 mA through its 2.2 k, which is harmless; an LED failing open is only a dark LED. No
  safety-relevant output changed.

**CAN TX/RX LEDs: left out.** An LED + 2.2 k from IO17 (TXD) to GND fails the check. While IO17 is undriven (reset,
boot), R70 10 k and the LED path form a divider. With Vf ≈ 1.7 V at ≈ 0.13 mA (estimated below the curve), TXD sits at
≈ 3.3 − 10 k × 0.13 mA ≈ 2.0 V, which is exactly the CA-IS3050G VIH minimum of 2 V (v1.10 §7.3). That loses R70's
recessive margin. An LED + 2.2 k from +3V3 to TXD or to RXD (lit while dominant) would not load the lines: TXD
recessive leaves 0 V across it, and RXD VOL is ≤ 0.4 V at 4 mA (p. 11), far above 0.7 mA. But these LEDs would light only for
dominant bits, and at 0.7 mA a 250 kbit/s frame (≈ 0.1–0.5 ms) is not visible without a pulse stretcher, which would be a new
circuit. The parts would buy no visible function, so they are not fitted. The suggestion stays in the T-0160 report.

**J6 (T-0151, T-0152).** One unfitted footprint `Connector_PinHeader_2.54mm:PinHeader_1x08_P2.54mm_Vertical`, DNP,
no LCSC code and no BOM line:

| J6 pin | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| pdm-4ch | GND | TXD0 | RXD0 | IO35 | IO36 | IO37 | IO42 | +3V3 |
| pdm-hc2 | GND | TXD0 | RXD0 | NC | NC | NC | IO42 | +3V3 |

On pdm-hc2, IO35–IO37 are FLT_T1, FLT_I2 and FLT_T2 and are not spare, so pins 4–6 carry no-connect flags and the FLT nets are untouched
(auto decision). The same footprint keeps the layout of the controller area identical. IO33 (HC2) and IO34 (4-ch) are
spare too but are not brought out (suggestion in the report). A 3.3 V USB-serial adapter connects with GND on pin 1;
pin 8 (3V3) is at the far end from GND, as the brief asked. A reversed adapter would still put its GND on 3V3, so mark pin 1 on the silkscreen.
**Rules:** J6 is for on-board service only. No cable leaves the board (invariant 9 for 3V3), and the lines are not
filtered or protected (invariant 4), so J6 must never become an external connector. A probe that shorts pin 8 to GND pulls down the 3.3 V
rail and resets the ESP32; the panel switches still drive the outputs (invariant 1). Layout: J6 inside the board, not at an edge connector, near the EMC
test points (VS, 3V3, GND, buck SW, CANH/CANL; `docs/reviews/2026-11-03-emc-system.md` item 9), with short traces
from U1 pins 31–33 and 38–40, outside the antenna keep-out.

**Footprint polarity (D7, D8).** KiCad `LED_0603_1608Metric`: pad 1 = cathode at x −0.79 mm, pads 0.875 × 0.95 mm. The JLCPCB
footprint `LED-SMD_L1.6-W0.8-R-RD` of C2286: pad 2 = K at −0.75 mm, pad 1 = A at +0.75 mm, pads 0.8 × 0.8 mm. So the cathode is on
the same side in both, only the pad numbers differ, and the electrical connection is by name. The maker's mark (green) is at the
cathode. Check the CPL rotation of D7/D8 at the first order.

## 9. Open items

- [x] Panel cable: fused switch-supply output, constant-current LED sinks, TVS on every line (§5, decision 17)
- [x] Battery-voltage measurement (IO10) and NTC near the switches (IO9) (decision 18)
- [ ] Failure modes and alert handling: LED blink codes, Signal K alerts with acknowledge/mute (decision 20)
- [x] Mounting and connectors (§7, decisions 97, 98)
- [ ] DIN carrier and printed enclosure design, connector sample check (§7)
- [x] Verify the PG-TDSO-14 footprint against the package drawing and the JLCPCB/EasyEDA footprint (§8.4, T-0066)
- [ ] Per-output fuse strategy (on board vs. in the installation)
- [x] Standard population: all four BTT6050 (Q-0032, T-0040); heavy loads go on HC2. BTT6010 only where > 4 A, mixed builds ordered together (§3, pdm-4ch STATUS/README)
- [x] High-current board: connectors (§7, decision 98)
- [ ] Bilge pumps (Vega: SEAFLO 01 Series 3500 GPH, 24 V model SFBP2-G3500-01: 8.0 A rated, 12.5 A max
      draw per the product page; current rises with pumping head; start-up and jammed-impeller current not
      given). BTT6010 at 8 A → Tj ≈ 86 °C, at 10 A ≈ 123 °C, at ≥ 11 A thermal shutdown: a pump working
      hard must not be cut off, so it goes on a high-current channel. Wiring per manual: float switch and
      manual switch in parallel to the pump; the PDM channel replaces the manual switch. Back-to-back
      MOSFETs block back-feed when the float switch runs the pump; on HC2 the OUT voltage divider on IO4/IO5
      (§4a.2) sees float-driven runs (OUT high while the channel is off), and SW3/SW4 too if the installer wires
      the pump feed to them. IMON cannot see them (that current does not pass the shunt). Timed overcurrent reports a jammed impeller instead of blowing a fuse.
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
