# Continue from here

Project-level handoff: which board is where and what to do next. Updated: 2026-11-08 (decisions 124–129).

## Boards

| Board | Schematic | PCB | Status file |
|---|---|---|---|
| `pdm-4ch` (4 × PROFET+24V) | done, ERC clean except library notices | 100 × 75 mm, 4 layers (decisions 138, 150); stages 1–4 done, planes, routing and silkscreen queued (decision 130) | `hardware/pdm-4ch/STATUS.md` |
| `pdm-hc2` (2 × TPS48110A-Q1 + MOSFETs) | done, ERC clean except library notices | not started | `hardware/pdm-hc2/STATUS.md` |

Firmware: not started.

## Order of work

Steps 1–3 are done, including the fix rounds; `/cost system deep` was re-run on 2026-11-07 (`docs/reviews/2026-11-07-cost-system-2.md`). Step 4 is in progress: mounting and connectors are decided (decisions 97, 98, 121).

**First order (decisions 99–103):** `pdm-4ch` only, as the cheapest MVP: 5 bare PCBs, 2 assembled, 2 oz, Standard PCBA, about 204 $ with connector sets (about 220 $ if the 16.42 $ fixture fee applies), 16 A only; all SMT parts on one side (decision 122). `pdm-hc2` follows after bring-up. Applied by the orchestrator on 2026-11-08 (decisions 124, 125): C3 → C170101 on `power-usb` (T-0190) and HC2 R105/R205 → C17927 (T-0191).

1. **`/emc system`** – EMC review of both schematics before layout: long switch and load leads, VHF immunity,
   surge/ESD paths, PWM edges, layout rules for the PCB phase.
2. **`/cost system deep`** – price both BOMs (parts, JLCPCB extended-part fees, 2 oz copper; connectors are hand-soldered keyed sockets, decisions 85, 98, not yet priced in the report)
   and propose levers.
3. **`/validate pdm-4ch deep`** and **`/validate pdm-hc2 deep`** – independent check: pinouts, the two custom
   footprints, circuit math, heat budget.
4. **`/system mechanical`** – mounting decided (decisions 97, 123: corner M3 holes, one printed ASA DIN mount). The connector sample check moves to bring-up (decision 127), so the PCB can start; the DIN mount and enclosure follow as OpenSCAD files after layout.
5. **`/board pdm-4ch pcb`**, order and bring-up; then **`/board pdm-hc2 pcb`** (decision 102).
6. **`/system firmware`** – firmware architecture: NMEA 2000 switch bank (PGN 127501/127502), power modes, soft fuse,
   heater thermostat, variant ID, VBAT and NTC readings. Owner's wish (decision 20): panel LED on = output on,
   blinking = fault; alerts and failures go to Signal K where they can be acknowledged and muted – design the
   failure modes per output (what blinks, alerts, latches, clears).

## Waiting on the owner

- No **[proposed]** decisions left; decision 20 (fault/alert handling) open until `/system firmware`.
- Connector checks of decision 98 on the first assembled boards, not before the order (decision 127). Re-check connector stock before ordering.
- Measurements: bilge pump locations and feeds. Pump start current on or after the first working prototype, before a board runs a pump in service (decision 100, `docs/pump-start-current-test.md`).
- Check whether the Standard PCBA fixture fee (16.42 $ per order) applies when quoting.

## Backlog (not now)

Ideas parked by the owner to keep focus on the two boards. Not decisions; pick up in a `/system` session later.

- **PWM outputs and stepless blower control** (2026-11-02). Use case: heater/convector blowers, e.g. windshield
  de-fogging, with stepless fan speed; also LED dimming of load outputs. Findings so far:
  - pdm-4ch: MCU can PWM the PROFET channels (LEDC on IO6–IO8/IO11) at ≤ 200 Hz (EMC limit); a closed panel switch
    forces the output fully on via the diode-OR; PROFET has no freewheel diode, so motor PWM puts the turn-off energy
    into the PROFET clamp every cycle; PROFET PWM limits and current-sense timing not checked in the datasheet.
  - pdm-hc2: no PWM until the gate slew is limited and measured on the bench (Q-0001, EMC E2).
  - Stepless brushed-motor control needs ≈ 20–25 kHz, which conflicts with the EMC limits on long load cables near
    VHF; a separate PWM board inside the PDM is not recommended.
  - Options, cheapest first: (1) EC/brushless blowers with their own 0–10 V or PWM speed input – PDM switches power and
    gives a protected signal output; (2) a speed module at the motor (short leads), commanded by a signal wire or
    NMEA 2000; (3) blower speed taps on 2–3 ordinary outputs.
  - Safety: heater element must never run without the blower (firmware interlock + fan-current check; keep the
    heater's own overheat cutout); defogging is a visibility item and should work without the PDM/bus. Competent
    review before installation.
  - Needed from the owner: blower model, current, brushed or brushless.

## Housekeeping

- The superseded repos `ESP32-PDM-base` and `ESP32-PDM-4x4` can be archived on GitHub.
