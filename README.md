# ESP32-PDM

An open, low-cost power distribution module for boats: solid-state outputs controlled both by ordinary
panel switches and over NMEA 2000, with current and fault reporting. Built around an ESP32-S3 and
Infineon PROFET+24V high-side switches, for 12 V and 24 V systems, assembled by JLCPCB.

**Status:** schematic phase. Both boards (`hardware/pdm-4ch`, `hardware/pdm-hc2`) are complete at schematic
level and pass ERC (apart from library-version notices); no PCB layout yet. Not tested in hardware.

## Boards

| Board | Channels | Output stage | Continuous current per channel (estimate, 40 °C, vented) |
|---|---|---|---|
| `pdm-4ch` | 4 | Infineon PROFET+24V, fitted per channel: BTT6050-1ERA / BTT6010-1ERA | ≈ 4 A / ≈ 8 A |
| `pdm-hc2` | 2 | TI TPS48110A-Q1 + back-to-back MOSFETs, adjustable breaker (25 A / 146 ms) | ≈ 15 A |

Both boards share the controller, power, NMEA 2000 and switch-input design.

## Population and ordering rule (`pdm-4ch`)

The standard `pdm-4ch` is built with four BTT6050-1ERA (≈ 4 A per channel). Heavy loads go on `pdm-hc2`. Fit a
BTT6010-1ERA (≈ 8 A) only on a channel that carries more than 4 A. A mixed build adds one extended-part loading fee
per order, so order mixed builds together to pay it once.

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
- **Reverse battery (`pdm-4ch`):** the output switches survive a reversed battery of at most 28 V for less than 2
  minutes, with each load at least 12 Ω (BTT6050 datasheet). Heavier loads rely on the battery fuse to clear. The
  loads see reverse voltage. A series diode in the switch supply protects the panel LEDs.
- **`pdm-hc2` timing:** after power is connected, the first switch-on of each output (also from a panel switch)
  takes about 0.1 s. After an overcurrent or short-circuit trip the output stays off for about 4 minutes and then
  tries again. HC2 outputs are on/off only (no dimming/PWM).
- **USB-C is a service port only.** Connect only a battery-powered laptop, or use a USB isolator. The
  board's GND is the boat's battery negative. A laptop on a shore-powered charger can tie its protective
  earth to battery negative through the USB cable, which can cause ground-loop currents, galvanic
  corrosion and damage. Unplug the USB cable after service.

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
