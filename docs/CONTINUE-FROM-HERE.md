# Continue from here

Project-level handoff: which board is where and what to do next. Updated: 2026-10-30.

## Boards

| Board | Schematic | PCB | Status file |
|---|---|---|---|
| `pdm-4ch` (4 × PROFET+24V) | done, ERC clean except library notices | not started | `hardware/pdm-4ch/STATUS.md` |
| `pdm-hc2` (2 × TPS48110A-Q1 + MOSFETs) | done, ERC clean except library notices | not started | `hardware/pdm-hc2/STATUS.md` |

Firmware: not started.

## Order of work

Steps 1–3 ran unattended (reviews done, 46 rulings answered). Next: `python3 tools/orchestrate.py run` applies the
approved changes unattended (decision 24, `docs/AUTONOMY.md`); then read `git log --stat main..auto/pilot` and the
inbox, and merge.

1. **`/emc system`** – EMC review of both schematics before layout: long switch and load leads, VHF immunity,
   surge/ESD paths, PWM edges, layout rules for the PCB phase.
2. **`/cost system deep`** – price both BOMs (parts, JLCPCB extended-part fees, 2 oz copper, through-hole terminals)
   and propose levers.
3. **`/validate pdm-4ch deep`** and **`/validate pdm-hc2 deep`** – independent check: pinouts, the two custom
   footprints, circuit math, heat budget.
4. **`/system mechanical`** – terminal blocks and pole count (panel connector J5 = 10 poles), DIN (1 module width) and flat-mount enclosure, vents.
5. **`/board pdm-4ch pcb`**, then **`/board pdm-hc2 pcb`**.
6. **`/system firmware`** – firmware architecture: NMEA 2000 switch bank (PGN 127501/127502), power modes, soft fuse,
   heater thermostat, variant ID, VBAT and NTC readings. Owner's wish (decision 20): panel LED on = output on,
   blinking = fault; alerts and failures go to Signal K where they can be acknowledged and muted – design the
   failure modes per output (what blinks, alerts, latches, clears).

## Waiting on the owner

- Decisions 19 and 21 **[proposed]**; decision 20 (fault/alert handling) open until `/system firmware`.
- Decision 16 (searchlight heating) open: revisit with cost in mind; halogen vs LED.
- Measurements on Vega: searchlight glass diameter and thickness; bilge pump locations and feeds.

## Housekeeping

- The superseded repos `ESP32-PDM-base` and `ESP32-PDM-4x4` can be archived on GitHub.
