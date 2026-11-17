# pdm-4ch bring-up and prototype validation

The order in which the two assembled prototypes are brought up and tested, with what each step needs and the pass
criteria. Stop at the first failure, write it down and fix the cause before going on. The tests already on the
`STATUS.md` "Prototype test list" are part of this plan; their IDs are kept (T-xxxx, decision numbers).

Figures marked *expect* are estimates from the design notes, not limits; anything that differs by a lot is still worth a
look. Results go in the record sheet at the end, one column per board (board A, board B: write the letter on the
silkscreen or a label).

**Safety.** These boards switch a battery. Every step from section 4 on puts a fuse (≤ 20 A for the 16 A tests, ≤ 5 A
before that) in the battery's positive lead. Work on the bench, never in the boat, until section 9 is passed. Bilge
pumps, navigation lights and anything that can trap or burn stay off these boards until a competent person has
reviewed the board and this record (CLAUDE.md rule 7).

## Gear

| Item | Used for |
|---|---|
| Multimeter | resistance checks, rail voltages, isolation |
| Bench supply (current limit, reads to 0.01 A) | first power-up, all low-current tests; the steps need up to 30 V |
| Oscilloscope (Hantek DSO1060), on its own battery where possible | switch edges, hot-plug peaks, short-circuit current |
| Function generator (FG1617) | bouncing-contact test (T-0012), PWM of the panel LEDs |
| USB-C cable and a computer | flashing and the REPL |
| 12 V or 24 V battery with a fuse | sections 7–9 (low source impedance) |
| Loads: 24 V (or 12 V) lamps or power resistors, up to 4 A per channel, 16 A in total | sections 7 and 9 |
| Panel switches, LEDs and a 10-pole plug wired as a test panel | section 6 |
| A known NMEA 2000 device and a powered, terminated backbone | section 8 |
| Surface thermometer or thermocouple, if one is at hand (not in the recorded gear) | section 9 |

Connector pins (netlist):

| Connector | Pins |
|---|---|
| J10 battery | 1 VBAT_IN (+), 2 GND |
| J11 outputs | 1 OUT1, 2 OUT2, 3 OUT3, 4 OUT4 (load returns to the boat negative, not to the board) |
| J5 panel | 1–4 SWIN1–4, 5 SW_SUPPLY, 6–9 LED_K1–4 (LED anode to SW_SUPPLY), 10 GND |
| J4 NMEA 2000 | 1 GND_CAN (NET-C), 2 NET-S (via F3), 3 CANH, 4 CANL |
| J6 service pads (unfitted) | 1 GND, 2 TXD0, 3 RXD0, 4–6 IO35–IO37, 7 IO42, 8 +3V3 |

## 1. Before any power (both boards)

1. Visual check under a lamp or loupe: solder bridges on U11–U14 (TDSO-14), U30 (SOT-23-THIN-8), U5 (SOIC-8), U1; rotation
   of U3, U11–U14, D7/D8 as fixed in the JLCPCB placement preview; polarity of C31 (electrolytic).
2. Hand-solder J4, J5, J10, J11 (decision 85). J10 needs a powerful iron; check the joints from both sides.
3. Connector fit (decision 127): the J11, J5 and J4 plugs cannot go in reversed; whether the J4 plug enters the J5 socket;
   height across the rail (part height + pin length + 1 mm, J10 *expect* 34.8 mm, recorded only); J10 wire entry and
   M4 screw access at 36 mm pitch; reach of mated plugs past the edge. Findings go to the next revision.
4. Resistance, board unpowered, meter on the 200 kΩ / 20 MΩ range, both polarities:

| Between | Pass |
|---|---|
| J10.1 (VBAT_IN) – GND | no short (≥ 1 kΩ; it charges C30/C31 and rises slowly) |
| VS (C31 +) – GND | no short |
| +3V3 (J6.8 or C8) – GND | no short (≥ 100 Ω) |
| J5.5 SW_SUPPLY – GND | no short |
| J11.1–4 – GND and – VS | no short |
| J4.2 NET-S – J4.1 GND_CAN | no short |
| GND – GND_CAN (J10.2 – J4.1) | open (≥ 10 MΩ; C70 is unfitted, nothing bridges the barrier) |

## 2. First power from USB (no battery)

USB VBUS feeds the buck through F2 and D3 (diode-OR), so the logic comes up without the power stage.

1. Plug USB-C into a computer, with nothing on J10. *Expect* the power LED D8 on and +3V3 at 3.2–3.4 V (J6.8 or C8 to GND).
2. VS (C31 +) stays near 0 V: USB must not feed VS.
3. The computer sees an Espressif USB device (USB-Serial/JTAG).
4. Flash the bring-up firmware (section 3). If the chip does not answer, hold BOOT (SW_BOOT1), tap RESET (SW_RESET1),
   then release BOOT.

## 3. Bring-up firmware: MicroPython

Most of the tests below need the MCU to drive pins and read ADCs, and the product firmware is not written yet
(`/system firmware`). The generic MicroPython build for ESP32-S3 does this without any firmware work: flash it once with
`esptool` over USB, then type commands in the REPL (`mpremote` or Thonny). Pins (`docs/ARCHITECTURE.md` pin map):

| Function | Pin | Check |
|---|---|---|
| Status LED D7 | IO13 out, high = on | blinks on command |
| MOD_ID | IO1 ADC | *expect* 1.65 V (10 k / 10 k) |
| VBAT_SENSE | IO10 ADC | V_J10 / 11 (full scale ≈ 32 V) |
| NTC | IO9 ADC | plausible room value; warms with a finger |
| SW_SENSE | IO12 in | high when SW_SUPPLY is present |
| Channel drive ch1–ch4 | IO6, IO7, IO8, IO11 out | sections 7 |
| Current sense IS1–IS4 | IO2–IO5 ADC | section 7 |
| DEN (all channels) | IO33 out | high only while sampling IS |
| Switch state SW1–SW4 | IO14, IO15, IO16, IO21 in | section 6 |
| Panel LED sinks LED1–4 | IO38–IO41 out | section 6 |

Use 11 dB attenuation on the ADC pins (calibrated range up to about 2.9 V). Two firmware rules apply even here: **never
burn eFuse `EFUSE_STRAP_JTAG_SEL`** (IO3 is held low by the IS2 network, design-notes §2), and **raise DEN only to take a
sample, then drop it** (design-notes §6.1: a fault current through RIS is not covered by hardware).

The CAN test (section 8) needs a TWAI driver, which the generic MicroPython build does not have: use the ESP-IDF TWAI
example for that step, or wait for the first product firmware.

## 4. First battery-side power (bench supply on J10)

USB unplugged. Bench supply on J10 (+ on pin 1), current limit 0.2 A.

1. 12 V: D8 on, +3V3 3.2–3.4 V, VS ≈ 12 V (Q30 on). Note the idle current (*expect* tens of mA at 12 V; Wi-Fi is off in
   the REPL).
2. Raise to 24 V, then 30 V. +3V3 stays in range; the current falls as the voltage rises (buck).
3. VBAT_SENSE reads within ±3 % of the meter at 12, 24 and 30 V (calibrate the scale here and note it).
4. Lower slowly from 12 V: note where +3V3 drops out (*expect* around 4–5 V at the buck input).
5. **Reverse polarity** (decision 108, design-notes §8.6): supply reversed on J10, 24 V, limit 0.1 A. Pass: current
   ≤ a few mA, VS ≈ 0 V, D8 off. Restore the polarity: the board works as in step 1.
6. Hot-plug (T-0161 part): bench supply set to 28.8 V, connect J10 with the scope on U3 VIN (C1) and VS. Pass: U3 VIN
   peak ≤ 65 V.

## 5. Logic with power on J10 (bench supply 24 V, limit 0.5 A)

1. MOD_ID 1.55–1.75 V; NTC plausible; SW_SENSE high (SW_SUPPLY present, J5.5 ≈ VS − 0.4 V for D55).
2. D7 follows IO13.
3. Wi-Fi on (any scan in MicroPython): +3V3 stays in range during transmit bursts (scope, 1 ms/div).
4. Serial console on J6.2/J6.3 only if J6 is fitted (optional).

## 6. Panel inputs and LEDs (test panel on J5)

Wire a test panel: one switch per input from J5.5 to J5.1–J5.4, one LED from J5.5 (anode) to J5.6–J5.9 (cathode), no
LED resistor (the sinks are constant-current).

1. Each switch reads on its pin (SW1–SW4 → IO14, IO15, IO16, IO21), and only on its own pin.
2. Switch threshold: with the bench supply as the switch source on one input, the input turns on at *expect* 7.5–8 V at the
   switch and stays on up to 30 V.
3. Each LED sink: IO38–IO41 high → LED on, *expect* about 5 mA (meter in series with one LED), the same at 12 V and 24 V.
   PWM at 100–200 Hz dims it without flicker.
4. **T-0012, bouncing contact:** drive one switch input from the function generator through the test panel (or bounce a
   real switch) and watch the channel output: no output chatter; τ ≈ 1.5 ms. Note the switch voltage at the moment it
   turns on (*expect* ≈ 8 V at the switch, ≈ 8.5 V at the battery).

## 7. Outputs, one channel at a time

Battery with a fuse on J10 from here on, or the bench supply if it can deliver the load current. One load at a time on
J11, load return to the battery negative.

1. **MCU path:** IOx high → OUTx ≈ VS, load on; low → off. Each channel only switches its own output.
2. **Hardware path (invariant 1):** the panel switch alone turns the channel on and off, with the MCU running and with
   U1 held in reset (hold SW_RESET1).
3. **Hardware path without 3.3 V (invariant 1, T-0042):** this needs the 3.3 V rail down while VS is up. Proposed
   method (owner's choice before doing it): on one board, cut the JP1 copper bridge (it feeds the buck from VS; T-0161
   cuts it anyway when L2 is fitted) and unplug USB, so +3V3 is 0 V. Then: the switch turns the output on and off.
   Measure IN − device GND (U11–U14 pin IN against the channel's ground network) at SWIN = 10.5 V with the channel on, once with the
   3.3 V rail down and once with it up; repeat at a 10.5 V battery with D55's drop (SWIN ≈ 9.8–10.1 V). Pass: ≥ 2.0 V
   (VIN(H) min). If short, the planned fix is RIN R101/R201/R301/R401 → 4.7 kΩ. Re-bridge JP1 with solder afterwards.
4. **Current sense:** at 1, 2, 3 and 4 A per channel, raise DEN, read IS, drop DEN. *Expect* ≈ 0.33 V/A
   (kILIS 1500, RIS 500 Ω; worst case kILIS 1380 → ≈ 0.36 V/A). Record the per-channel factor for the firmware.
5. **Open load:** no load, channel off, DEN raised: IS reads the open-load level (full scale); drop DEN at once.
6. **Short to GND at the output:** current-limited supply (bench supply, 24 V, 3 A limit) first, then from the battery
   with the fuse: OUTx shorted to GND with the channel on. Pass: the BTT6050 limits and cycles, the board survives, IS
   reads the fault level when DEN is raised briefly, normal operation afterwards.
7. **Inductive load:** if a relay coil or motor is at hand, switch it off with the scope on OUTx: the negative clamp
   (VS − VDS(AZ)) shows, no damage. A freewheel diode at the load stays the installation rule (design-notes §8.2).

## 8. NMEA 2000

1. Isolation again: GND – GND_CAN open (≥ 10 MΩ) with the board powered.
2. Connect J4 to a powered, terminated backbone. *Expect* 5 V at U5's bus side (U6 output), and NET-S current ≈ 50 mA
   or less (LEN 1, 49.3 mA worst case: **measure and record**, `docs/ARCHITECTURE.md` `can` row).
3. With the ESP-IDF TWAI example at 250 kbit/s: frames sent by the board appear on the other device, and its frames
   appear on the board. CANH/CANL on the scope: clean dominant/recessive levels.

## 9. Heat and full load (16 A)

Battery with a ≤ 20 A fuse, 4 A on each channel (16 A total, the board limit, decision 103), board in free air or in the
printed enclosure if it exists, 30 min.

1. Every channel stays on; no thermal shutdown.
2. Readings every 5 min: NTC, VS, the four IS values, and the surface of Q30, U11–U14, J10 and J11 if a thermometer is
   at hand. Scale to 40 °C ambient by adding (40 − room temperature) and compare with `tools/heat_budget.py`.
3. Voltage drop J10.1 → VS at 16 A (Q30 + copper; *expect* about 2–4 mΩ, so ≤ 65 mV) and VS → each OUTx.
4. **PWM loss (decision 221 [proposed], design-notes §4 "PWM dimming"):** at 24 V (28.8 V if the supply allows), one
   channel at 3.5 A resistive, PWM from the MCU at 100 Hz and then 200 Hz, duty 90 %. Scope OUTx: measure the edge times
   (30–70 %) and compare with 0.3–1.4 V/µs. After 15 min record the U1x case temperature against the same channel at
   3.5 A DC. *Expect* the 200 Hz case at most ≈ 10 K warmer than DC; more than that lowers the PWM rating.

## 10. Destructive and stress tests (one board, after sections 1–9 pass on both)

- **T-0118, PTC hard short (required before installation):** from a 30 V battery-like supply (low source impedance),
  short J5.5 to GND (behind F4/R56), then behind F1 (D1/D2 node) and behind F3 (D10/FB2 node). Make the short behind F1
  with JP1 fitted (and repeat it if L2 is ever fitted). Scope the current; afterwards inspect R54–R56 and F1/F3/F4
  (cracks, discoloration, resistance). Pass before installation (design-notes §8.3).
- **T-0129, negative pulse on J10:** with VS charged and the source short-circuit current within 31 A: scope Q30 VDS
  and VS (also VBAT_IN); *expect* VDS about 60 V or less and VS no lower than about −4 V; inspect C31 afterwards.
- **T-0161, conducted emission scan with JP1 fitted:** spectrum of the battery input (scope FFT, or a LISN if one can be
  borrowed). If the buck's 1.1 MHz or PFM components need it: cut JP1, fit L2 (start 8.2 µH C96963) together with C22
  2.2 µF + R73 10 Ω (3.3–4.7 Ω 1206 if the ring at 33–57 kHz is not damped enough). Then scope U3 VIN at light load
  (PFM) and during a 28.8 V hot-plug; peak ≤ 65 V. **EMC E24:** also scope U3 FB and +3V3 at light load for jitter or
  pulse bunching.
- **VHF exposure (EMC E22, if not fixed in layout before the order):** a handheld VHF at 1 W and then 5 W keyed next to
  a 2–5 m panel cable on J5: LED1 must not flicker or change brightness compared with LED2–LED4; switch inputs must not
  change state. Same with the radio next to the outputs and the battery leads.
- **ESD (EMC E23):** no ESD gun in the recorded gear; if one can be borrowed, contact discharge on J4 CANH and CANL, then
  repeat section 8.3.

## 11. After the tests

- Bilge pump start current (decision 100, `docs/pump-start-current-test.md`): on or after the first working
  prototype, before any board runs a pump in service.
- Everything that failed or surprised goes into `STATUS.md` and, where it changes the design, into a `/board` or
  `/system` session.
- A competent person reviews the board, this record and the installation plan before the board goes into a boat.

## Record sheet

| Step | Board A | Board B | Notes |
|---|---|---|---|
| 1.1 Visual |  |  |  |
| 1.3 Connector fit (decision 127) |  |  |  |
| 1.4 Resistances / GND–GND_CAN open |  |  |  |
| 2 USB power: +3V3, VS ≈ 0, enumerates |  |  |  |
| 4.1–4.2 J10 12/24/30 V: +3V3, idle current |  |  |  |
| 4.3 VBAT_SENSE error at 12/24/30 V |  |  |  |
| 4.4 +3V3 drop-out voltage |  |  |  |
| 4.5 Reverse polarity current |  |  |  |
| 4.6 Hot-plug U3 VIN peak |  |  |  |
| 5 MOD_ID / NTC / SW_SENSE / Wi-Fi burst |  |  |  |
| 6.1–6.3 Switches, threshold, LED current |  |  |  |
| 6.4 T-0012 bounce |  |  |  |
| 7.1–7.2 MCU and hardware path, ch1–4 |  |  |  |
| 7.3 T-0042 IN − GND at 10.5 V (3V3 down / up) |  |  |  |
| 7.4 IS factor ch1–4 (V/A) |  |  |  |
| 7.5–7.6 Open load, short |  |  |  |
| 8 CAN: isolation, NET-S current, frames |  |  |  |
| 9 16 A, 30 min: temperatures, drops |  |  |  |
| 10 T-0118 / T-0129 / T-0161 / VHF / ESD |  |  |  |
| Reviewed by a competent person (name, date) |  |  |  |
