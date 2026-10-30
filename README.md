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
