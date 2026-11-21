# ESP32-PDM firmware (draft)

First draft, written before any board exists. It compiles and its control logic is tested on the development
machine; **nothing has run on hardware yet**. Its stack, fault behaviour and NMEA 2000 messages were confirmed in
`/system firmware` on 2026-11-21 (decisions 230–232); figures marked `proposed` in the code stay proposals until bring-up. Licence: MIT (`LICENSE-MIT`).

## What it does now

`pdm-4ch` in Active mode:

- Reads the variant resistor (MOD_ID). On anything but a `pdm-4ch` it drives no pin and blinks the status LED fast.
- Follows the four panel switches (20 ms qualify). The switches turn the outputs on in hardware (invariant 1); the
  firmware only reads them.
- Takes on/off commands from NMEA 2000 (PGN 127502) and from the USB serial console.
- Measures each channel's current: DEN is raised only for the sample (under 2 ms, every 100 ms) and dropped again
  (design-notes §6.1). After a full-scale reading the next sample comes 500 ms later.
- Soft fuse per channel (4 A, thermal model with a 10 s time constant) and switch-fault detection; panel LED on =
  output on, blinking = fault.
- Battery voltage, board temperature (NTC), panel-supply alert (decision 93).
- Reports on NMEA 2000: PGN 127501 (switch bank status) and PGN 127751 (voltage and current per channel).

## Next (decisions 230–234)

1. SensESP v3 build trial: this core on the ESP32-S3, next to the NMEA 2000 stack, flash size (230). If it fails, an
   own small Signal K websocket client, Arduino OTA and a minimal settings page.
2. Alerts on NMEA 2000 (PGN 126983, response 126984 for acknowledge/silence) and as Signal K notifications (231, 232).
3. PWM at 100 Hz on the drive pins within decision 234's rating, with IS sampled in the on phase.
4. OTA, enabled only with a password (233).
5. Later: per-output settings, including "restore after reset" (231); Eco and Sleep after bring-up (233); pdm-hc2.

## What it does not do yet

Wi-Fi and Signal K (alerts that can be acknowledged and muted, decision 20), OTA update, Eco and Sleep modes
(design-notes §6), outputs held through a reset, panel LED dimming, PWM outputs, the heater thermostat, `pdm-hc2`,
settings per output (name, rating, kILIS, fuse curve) and calibration.

## Fault behaviour (decision 231)

| Fault | Detected by | Firmware does | Panel LED | Clears |
|---|---|---|---|---|
| Overload | soft fuse on the measured current | bus drive off, latched | blinks | switch opened, or bus command off |
| Switch fault (short, current limit, overtemperature) | current sense at full scale for 3 samples while on | bus drive off, latched | blinks | same |
| Open load while off | current sense at full scale while off | warning flag only | off | by itself |
| Panel supply missing | SW_SENSE low for 2 s while the battery is above 10 V | alert only | – | by itself |
| Board hot | NTC at 85 °C or above | warning only | – | by itself |

Nothing retries by itself. The status LED D7 flashes briefly every 2 s when all is well and blinks steadily while
any fault or alert is active.

**Failure modes to know (safety).**

- The firmware cannot switch off an output that a closed panel switch holds on. A fault is then only shown and
  reported; the BTT6050's own protection and the wiring fuse protect the cable.
- An output that was switched on over the bus goes off when the controller resets, crashes or is updated, and stays
  off until it is commanded again. Loads that must not go dark (navigation lights, bilge forced run) belong on a
  panel switch, which works without the controller.
- The soft fuse is not a circuit breaker. Above about 8.4 A the current sense is out of range and the firmware sees
  a switch fault after 1.0–1.5 s; every output wire still needs its own fuse or breaker (design-notes §8).
- A competent person should review any installation with bilge pumps, navigation lights or other safety-relevant
  loads before use.

## Layout

```
platformio.ini
lib/pdm_core/     control logic without hardware access: scaling, input qualifier, soft fuse, channel states
src/              ESP32-S3: pins, GPIO/ADC, TWAI driver for the NMEA2000 library, switch bank, main loop
test/test_core/   host tests for lib/pdm_core
```

Stack: PlatformIO, Arduino-ESP32 2.0.17 (ESP-IDF 4.4), `ttlappalainen/NMEA2000-library` with its own small TWAI
driver (`src/n2k_twai.cpp`), because the library's ESP32 driver does not support the S3.

## Build, test, flash

```
cd firmware
pio test -e native        # logic tests on this machine
pio run -e pdm            # build for the ESP32-S3-MINI-1-N8
pio run -e pdm -t upload  # flash over USB (hold BOOT, tap RESET if the port does not answer)
pio device monitor        # console: status | on N | off N | bank N
```

`bank N` stores the NMEA 2000 switch bank instance (0–252); give each board on the same bus its own.

## Unverified values

Marked `proposed` or `UNVERIFIED` in `lib/pdm_core/pdm_config.h` and `channel.cpp`. To settle before the firmware
runs a real load:

- BTT6050 sense settling time after DEN rises (now 500 µs) and after the output goes off (now 300 ms): read from
  the datasheet into `docs/part-facts/C534868.md`, or measure at bring-up (`hardware/pdm-4ch/bring-up.md` §7).
- The state of IO33 (DEN) from reset until `setup()` runs (design-notes §6.1, requirement 3): scope it at bring-up.
- Per-channel current factor from the bring-up record sheet.
- NMEA 2000 device class 30 / function 140 and the manufacturer code (2046 is a placeholder, not a registered code).
- Soft-fuse curve and the 3-sample start-current allowance against real loads (pump start test, decision 100).
