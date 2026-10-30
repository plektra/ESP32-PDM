# Continue from here

Project-level handoff: which board is where and what to do next. Updated: 2026-10-30.

## Boards

| Board | Schematic | PCB | Status file |
|---|---|---|---|
| `pdm-4ch` (4 × PROFET+24V) | done, ERC clean except library notices | not started | `hardware/pdm-4ch/STATUS.md` |
| `pdm-hc2` (2 × TPS48110A-Q1 + MOSFETs) | done, ERC clean except library notices | not started | `hardware/pdm-hc2/STATUS.md` |

Firmware: not started.

## Order of work

1. **`/system panel-cable`** – decide decision 17 (fused switch supply, constant-current LED sinks, TVS on every
   line, no 3.3 V on the cable) and decision 18 (battery voltage, NTC, pin map). Changes the shared `analog_sw` sheet
   on both boards.
2. **`/emc system`** – EMC review of both schematics before layout: long switch and load leads, VHF immunity,
   surge/ESD paths, PWM edges, layout rules for the PCB phase.
3. **`/cost system deep`** – price both BOMs (parts, JLCPCB extended-part fees, 2 oz copper, through-hole terminals)
   and propose levers.
4. **`/validate pdm-4ch deep`** and **`/validate pdm-hc2 deep`** – independent check: pinouts, the two custom
   footprints, circuit math, heat budget.
5. **`/system mechanical`** – terminal blocks and pole count, DIN (1 module width) and flat-mount enclosure, vents.
6. **`/board pdm-4ch pcb`**, then **`/board pdm-hc2 pcb`**.
7. **`/system firmware`** – firmware architecture: NMEA 2000 switch bank (PGN 127501/127502), power modes, soft fuse,
   variant ID.

## Waiting on the owner

- Decisions 17, 18, 19 **[proposed]**.
- Searchlight: halogen vs LED (drives decision 19).
- Measurements on Vega: bilge pump locations and feeds.

## Housekeeping

- The superseded repos `ESP32-PDM-base` and `ESP32-PDM-4x4` can be archived on GitHub.
