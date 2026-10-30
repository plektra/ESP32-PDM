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
- One product: a 4-channel board. Current per channel is chosen at assembly by fitting a
  pin-compatible switch (BTT6050 ≈ 4 A or BTT6010 ≈ 8 A); loads above that use a relay/contactor
  driven by a channel (e.g. the 500 W halogen searchlight: ≈ 21 A at 24 V, inrush roughly 10–15×).
- Installed in an enclosed location, in a vented 3D-printed enclosure. Two mounting styles:
  DIN rail (PCB perpendicular to the rail, 1–2 module widths) and flat (wall/ceiling).
- Engine-room ambient up to 40 °C.

## 2. Architecture

| Block | Sheet | Notes |
|---|---|---|
| Controller | root | ESP32-S3-MINI-1-N8, native USB (no USB-UART bridge) |
| Power | `power-usb` | LMR51610 buck (4–65 V in) → 3.3 V, diode-OR with USB VBUS, 60 V PTC, SMAJ30CA |
| NMEA 2000 | `can` | ISO1044 isolated CAN, TPS7B91 5 V LDO from NET-S, SMAJ18CA, PESD2CAN |
| Panel inputs | `analog_sw` | Protected direct switch inputs, LED drivers |
| Output channels | `channel` (×4) | BTT6050-1ERA per channel |
| Battery input | root | J10, SMCJ30CA surge clamp |

Pin use (ESP32-S3): IN drive IO6–IO9, current sense IO2–IO5 (ADC1), switch state IO14/IO15/IO16/IO21,
panel LEDs IO10–IO13, DEN IO33, variant ID IO1 (ADC1), CAN IO17/IO18, USB IO19/IO20.

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
datasheet uses 27 Ω + BAS21). The Schottky keeps the device ground shift at ~0.5 V, so the physical
switch path (≈3.2 V node − BAT54C) still clears VIN(H) with ~0.4 V margin.

The footprint is drawn from the datasheet package outline (Figure 53): lead pads 1.6 × 0.6 mm at
x = ±2.6 mm (0.47 mm clearance to the 2.65 × 6.4 mm exposed pad), 10 × 0.3 mm thermal vias,
bottom-side copper pad, ~60 % paste coverage. **Check against the JLCPCB/EasyEDA footprint before
ordering.**

## 4. Heat budget

Run `tools/heat_budget.py` (see `--help`). Model: channel loss I²·RDS(on)(Tj), enclosure air rise
P_total · R_box, junction rise P_channel · RthJA, solved together.

Assumptions (*estimates* until a prototype is measured): vented enclosure with the PCB vertical
(chimney airflow), R_box 0.6 K/W (4-ch) / 0.9 K/W (2-ch, 1 module width), RthJA 40 K/W per switch
with 2 oz copper (50 K/W with 1 oz), 0.6 W for the ESP32/regulator/LEDs, RDS(on) at datasheet max
rising linearly to 150 °C.

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
- Above ~8 A per channel: relay or contactor driven by a channel (searchlight, hydraulic backup pump).
- At high total current the shared supply path dominates: 36 A through 4 mΩ is 5 W. Keep the battery
  terminal + VS copper ≤ 2 mΩ and rate the input terminal for ≈ 40 A; output terminals ≥ 10 A.

Layout rules from the budget: switches spread out and away from the ESP32; large VS copper on both
layers around the cooling tabs, stitched with vias; 2 oz copper; vents at bottom and top; continuous
current rating printed on the label; firmware warns or sheds load from measured current (and an NTC,
when an ADC pin is freed).

## 5. Physical switch inputs and long leads

Per input (sheet `analog_sw`): SMAJ30CA at the connector → 4.7 kΩ 1206 load (contact wetting,
2.5 mA at 12 V / 6.4 mA at 30 V) → 10 kΩ 1206 series → node with 4.7 kΩ, BZT52C3V3 and 100 nF →
BAT54C diode-OR into the channel IN. The node sits at ~3.2 V for any input 10.5–30 V; the EN threshold
is ~7.5 V at the switch; τ ≈ 0.3 ms. The input works without the 3.3 V rail. 10 kΩ series resistors
feed the node to the ESP32 (limits back-feed into an unpowered ESP32 to ~0.3 mA).

Keeping long leads from acting as antennas:
- Filter every external line at the connector (TVS capacitance + series R + RC); no unfiltered line
  enters the board.
- Keep loops small: the switch supply and the switch return in the same cable (twisted pair or
  multicore). **Open item:** provide a fused switch-supply output on the panel connector so the whole
  loop runs inside one cable.
- **Open item:** the panel connector still carries 3.3 V and the LED lines. Proposed: LEDs between the
  switch supply and constant-current sinks (BC817 + emitter resistor, ~5 mA, PWM-dimmable), each line
  with a TVS, no 3.3 V on the cable.
- Outputs: run each load's return with its feed; if outputs are PWM-dimmed, use a low frequency
  (100–200 Hz).
- Firmware: qualify inputs (e.g. 20 ms stable), average ADC readings.

## 6. Power modes

| Mode | Wi-Fi | CAN | Panel LEDs | DEN (diagnostics) | Wake |
|---|---|---|---|---|---|
| Active | on | on | full / dimmed | on | – |
| Eco | power-save or off | on | dimmed / off | slowed | immediate |
| Sleep | off | periodic listen window | off | off | local switch, timer, wake broadcast |

- Entered by a command over NMEA 2000 (or Signal K); local switches always work and can wake the node.
- In deep sleep the ESP32 cannot receive CAN or Wi-Fi; the node wakes every few seconds and listens
  briefly, and the central controller repeats its wake command for ~10 s.
- Output state is held through deep sleep with RTC GPIO hold (IO6–IO9 are RTC GPIOs). A full reset or
  OTA update drops outputs for ~0.3 s unless the physical switch is on.
- DEN low puts the BTT6050s in standby (µA range) – this saves more than the ESP32 sleep itself.

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
- Reverse battery: the switches survive with the ground network, but the loads see reverse voltage.

## 9. Open items

- [ ] Panel cable: fused switch-supply output, constant-current LED sinks, TVS on every line (§5)
- [ ] Battery-voltage measurement (needs an ADC pin: move panel LEDs off IO10–IO13)
- [ ] NTC near the switches (same ADC pin question)
- [ ] Terminal blocks and enclosure layout for DIN / flat mounting (§7)
- [ ] Verify the PG-TDSO-14 footprint against the JLCPCB/EasyEDA footprint
- [ ] Per-output fuse strategy (on board vs. in the installation)
- [ ] Standard population (e.g. 2 × BTT6010 + 2 × BTT6050) vs. all-BTT6010 builds
- [ ] Bilge pumps (Vega: 12 A per pump when running, owner 2026-10-30): too much for one channel
      (BTT6010 @ 12 A → Tj ≈ 186 °C). Plan: automatic float-switch circuit wired directly (always on);
      manual forced run through a motor-rated relay driven by a channel (works without the ESP32 via the
      physical switch); run monitoring via an auxiliary sense input on the pump feed
- [ ] Auxiliary sense-only inputs (1-2, same protected input circuit, spare GPIO) for pump-running /
      float-switch state
- [ ] Load list with nameplate currents (VHF, FM radio, wipers incl. park circuit, bilge pumps, work lights)
- [ ] Update Symbols from Library in KiCad (BC817, LMR51610, USB-C symbols)
- [ ] Remaining checks from the BOM audit: Kangnex CAN connector footprint, PESD2CAN pinout
