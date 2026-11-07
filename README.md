# ESP32-PDM

An open, low-cost power distribution module for boats: solid-state outputs controlled both by ordinary
panel switches and over NMEA 2000, with current and fault reporting. Built around an ESP32-S3 and
Infineon PROFET+24V high-side switches, for 12 V and 24 V systems, assembled by JLCPCB.

**Status:** schematic phase. Both boards (`hardware/pdm-4ch`, `hardware/pdm-hc2`) are complete at schematic
level and pass ERC (apart from library-version notices); no PCB layout yet. Not tested in hardware. `pdm-4ch`
goes first as a prototype, with `pdm-hc2` after its bring-up.

## Boards

| Board | Channels | Output stage | Continuous current per channel (estimate, 40 °C, vented) |
|---|---|---|---|
| `pdm-4ch` | 4 | Infineon PROFET+24V BTT6050-1ERA (first version, 16 A in total) | ≈ 4 A |
| `pdm-hc2` | 2 | TI TPS48110A-Q1 + back-to-back MOSFETs, built-in breaker ≈ 17.5 A / 146 ms (≈ 15–20 A over tolerances) | ≈ 15 A |

Both boards share the controller, power, NMEA 2000 and switch-input design.

## Population and ordering rule (`pdm-4ch`)

The first version of `pdm-4ch` is built with four BTT6050-1ERA (≈ 4 A per channel, 16 A in total). Heavy loads go on
`pdm-hc2`. A BTT6010-1ERA (≈ 8 A) option may return in a later revision; it is not supported on this version.

## Features

- Physical switch inputs drive the outputs directly in hardware: they keep working if the ESP32 or
  its 3.3 V supply fails. Surge-protected, 12 V and 24 V, suitable for long switch cables.
- NMEA 2000 (isolated CAN), USB-C for programming, Wi-Fi for Signal K / configuration / OTA.
- Per-channel current measurement and fault reporting.
- Low-power modes controlled over the bus.

## Important limitations

- **Not protected against load dump.** Onboard TVS diodes clamp short transients only. A load dump
  (battery disconnected while an alternator is charging, or a BMS disconnect) must be handled at system
  level: alternator protection device, field-disconnect battery switch, or a BMS that signals the
  charge source before disconnecting. Like most marine electronics, this device relies on that.
- **Not a circuit breaker.** Every output wire must be protected by a fuse or breaker sized to the
  wire. The switches protect themselves, not your wiring.
- Install in an enclosed, ventilated location; observe the continuous current ratings.
- **Panel switches: dry contacts only.** Use plain (unlit) switch contacts. A lamp or LED across the contacts leaks
  current that can switch the output on in hardware. Use the J5 LED lines for panel indication instead.
- **12 V systems, engine cranking:** the panel-switch path switches an output off when the switch voltage drops below
  about 8 V (about 8.5 V at the battery). While the engine cranks, panel-switched outputs such as navigation lights can
  therefore go off for a moment. 24 V systems are not affected.
- **Reverse battery (`pdm-4ch`):** a reverse-blocking MOSFET in the supply input (Q30 with controller U30) keeps
  a reversed battery of up to 30 V away from the rest of the board, with no time limit: the bulk capacitor, the
  output switches, the panel switches and the loads see no reverse voltage. Above about 33 V the input surge diode
  conducts and the battery fuse must clear. If that MOSFET has failed short, the old limits apply: only the output
  switches survive (at most 28 V, under 2 minutes, each load at least 12 Ω), and the bulk capacitor C31 is not rated
  for reverse voltage and can overheat and vent. So check the polarity before connecting.
- **`pdm-hc2` external breaker (required):** each HC2 output must have its own external breaker or fuse that trips at
  **at most 15–18 A** (within minutes), in addition to the wire protection above. The built-in breaker trips at about
  17.5 A (≈ 15–20 A over part tolerances) only after 146 ms; between the 15 A rating and that level the board relies on
  the external breaker and the firmware soft fuse. The board label states the same. A bilge-pump output's breaker sits
  between J11 and the junction with the float-switch circuit, so the float circuit never depends on the PDM.
- **`pdm-hc2` reverse battery destroys the board:** a reversed battery connection destroys both HC2 output controllers
  (TPS48110A-Q1, rated −1 V). There is no reverse-polarity protection on this revision. Use the keyed/polarised
  battery connector J10 only as marked, check polarity before connecting; the board label carries this warning.
- **Mounting:** two ways, on the same four M3 holes. On a DIN rail the bare board goes on a plastic carrier, edge-on, about 36 mm
  of rail per unit, inside an enclosure you provide; it must keep out drips and loose metal, and carrier and screws must never
  touch board copper. All connectors are keyed plugs that pull out from the board edge: wire them on the bench and leave room for the plug and cable bend.
  Alternatively use a vented 3D-printed enclosure, also for flat mounting. Each board gives off about 9 W at full load: in a
  shared enclosure keep the air inside at or below 50 °C for the full rating (estimate until measured), or derate.
- **Board input limits:** at most **32 A** continuous through J10 on `pdm-4ch` and **36 A** on `pdm-hc2`, whatever the
  outputs could draw together. Size the battery feed, and its fuse, so that these limits are not exceeded.
- **`pdm-hc2` timing:** after power is connected, the first switch-on of each output (also from a panel switch)
  takes about 0.1 s. After an overcurrent or short-circuit trip the output stays off for about 4 minutes and then
  tries again. HC2 outputs are on/off only (no dimming/PWM).
- **`pdm-hc2` loads:** HC2 is for motor loads (bilge pumps, wipers) and LED work lights, one light per output. Each HC2 output is
  rated for at most **about 50 µF of load input capacitance** (to be confirmed on the prototype). A larger capacitive
  load can trip the short-circuit protection at switch-on, and the output then stays off for about 4 minutes. Put
  DC-DC converters (e.g. 24→12 V for a car radio), radios and other electronics on `pdm-4ch`. Put several lights on one
  output only if they have little capacitance (plain LED strips without their own driver) or a test shows the group
  switches on cleanly from warm; if a group trips at switch-on, split it over several outputs.
- **USB-C is a service port only.** Connect only a battery-powered laptop, or use a USB isolator. The
  board's GND is the boat's battery negative. A laptop on a shore-powered charger can tie its protective
  earth to battery negative through the USB cable, which can cause ground-loop currents, galvanic
  corrosion and damage. Unplug the USB cable after service.

## Installation

The interference immunity of the boards assumes the cable practice below. It adds to the points in
[Important limitations](#important-limitations) (load dump, wire fuses, dry contacts, reverse battery, the `pdm-hc2`
external breaker, USB service only), which are not repeated here.

- **Battery feed.** Fuse at the battery, sized to the wire. Run + and − as a twisted or tightly bundled pair, as short
  as possible, at least 0.5 m from the VHF antenna feed and the transmitter; where they must cross, cross at 90°.
  Check polarity before connecting (see the reverse-battery points above).
- **Loads.** Run each load's return with its feed (same cable, twisted) back to the battery negative bus. Never return
  load current through the PDM ground. Fuse each output wire (see "Not a circuit breaker" above).
- **Inductive loads** (solenoids, relays, horns, motors): fit a diode or TVS at the load.
- **PWM.** No PWM above 200 Hz on `pdm-4ch`. No PWM at all on `pdm-hc2` until it has been measured on the bench
  (its outputs are on/off only, see above).
- **Panel cable.** One screened multicore, at most 10 m, with the switch, LED and supply wires inside the same cable.
  Connect the drain only at the PDM end (J5.10). Dry contacts only (see above). Do not share the cable with other
  loads.
- **NMEA 2000.** Drop cable at most 6 m; ground the backbone shield once, at the power tap. The node has no shield pin,
  so do not connect the drain at the node. Keep the drop away from the VHF coax.
- **Position.** An enclosed, vented box (see above), as far from the VHF antenna and its coax as practical. The plastic
  box gives no shielding: the cables act as the antenna, so cable practice matters more than box position.

## Repository layout

```
hardware/pdm-4ch/   KiCad project, 4-channel board (PROFET)
hardware/pdm-hc2/   KiCad project, 2-channel high-current board
lib/                shared KiCad symbols and footprints
docs/               CONTINUE-FROM-HERE (next steps), decisions, ARCHITECTURE, design notes, reviews
tools/              heat budget model, schematic editing helpers, netlist checker
.claude/            Claude Code roles: commands and review agents (see docs/WORKING-WITH-CLAUDE.md)
```

See [docs/design-notes.md](docs/design-notes.md) for the design rationale, heat budget and open items.

## History

This repository supersedes the earlier two-board design (base board + output module):
[ESP32-PDM-base](https://github.com/plektra/ESP32-PDM-base) and
[ESP32-PDM-4x4](https://github.com/plektra/ESP32-PDM-4x4).

## License

MIT, see [LICENSE](LICENSE).
