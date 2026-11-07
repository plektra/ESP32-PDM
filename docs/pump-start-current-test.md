# Bilge pump start current test

Measures whether a bilge pump's start and running current fit the pdm-hc2 hardware breaker. The start current of the
SEAFLO SFBP2-G3500-01 is not published (design-notes §4a.2). Timing: on or after the first working prototype
(decision 100, which moves this from before ordering). Finish it before any board runs a pump in service.

No current clamp is needed. A calibrated length of wire is the current sensor, read with an oscilloscope.

## Gear

- Oscilloscope with a single-shot trigger and at least 20 mV/div, running on its own battery
- Multimeter with a millivolt range
- Bench supply with an adjustable current limit, for calibration only
- 1 m of 2.5 mm² copper wire, about 7 mΩ

**Do not put the multimeter in series with the pump.** The start surge can blow its fuse or damage it. Do not run the
pump from the bench supply either: the current limit would distort the start. Use the real battery.

## 1. Make and calibrate the sensor

1. Mark two measuring points on the wire, a little in from each end. Always measure at those points.
2. Set the bench supply's current limit to about 3 A and pass that current through the wire.
3. Read the millivolts between the marks with the multimeter.
4. Work out `R = volts / amps`. Example: 21 mV at 3 A is 7 mΩ. Write it down.

## 2. Connect it

1. Keep the normal fuse in the circuit.
2. Put the wire in the pump's **negative** lead.
3. Connect the scope's ground clip to the battery-side mark and the probe tip to the pump-side mark.
4. Unplug the scope's charger, so its ground is not tied to anything else.
5. Make and break temporary connections away from the bilge, in case of vapours.

## 3. Set up the scope

Menu names differ between scopes.

- DC coupling; probe and scope channel both set to ×1
- 50 mV/div and 20 ms/div
- Single-shot trigger, rising edge, at about 20 mV
- Bandwidth limit on, if the scope has one (motor brushes are noisy)

Trigger polarity depends on which way round the clips are. If the trace is inverted, swap the probe and ground
positions on the wire.

## 4. Measure

1. Use the pump in water with its real hose, because running current rises with pumping head.
2. Have the charger or alternator running if possible, because higher voltage gives a higher start current. Note the
   battery voltage.
3. Capture five starts: from cold, and again after a short run. Photograph each screen.
4. Convert with `amps = volts / R`. For each start, note the peak current and the time from start until the current
   falls below the limit in the table.
5. Measure the steady running current across the wire with the multimeter's millivolt range.
6. Skip the jammed-impeller test. It is not needed for this result and can damage the pump.

## 5. Read the result

The start must fall below the breaker's lower tolerance limit within the breaker's minimum time, about 122 ms
(design-notes §4a.2). Tolerances come from interpolated datasheet figures, so they are not guaranteed.

| Copper and breaker setting | Breaker range | Most continuous current | Status |
|---|---|---|---|
| 2 oz, RIWRN 68 k (current design) | about 15.2–19.7 A | about 15 A | Current design |
| 1 oz, RIWRN 75 k (proposal only) | about 13.8–17.9 A, scaled from the 68 k figures | about 13 A | Not decided |

| Result, using the lower limit of the setting in question | Meaning |
|---|---|
| Below the limit within about 100 ms, and running current at least 20 % below it | Passes with margin |
| Below the limit within 100–122 ms, or running current less than 20 % below it | Tight; review before relying on it |
| Still above the limit after 122 ms, or running current above the continuous figure | Fails; the breaker could trip |

## 6. Finish

1. Remove the test wire and restore the original wiring.
2. Confirm the float switch runs the pump before leaving the boat. The automatic bilge circuit must always keep working
   (invariant 8).
3. Record the results in `hardware/pdm-hc2/STATUS.md`.

**Failure mode:** this circuit is safety-relevant. If the breaker trips on a pump start, a forced bilge run can stop.
A competent person should review the bilge circuit before installation.
