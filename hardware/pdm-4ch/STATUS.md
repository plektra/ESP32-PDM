# pdm-4ch status

Updated: 2026-10-30

**Where it stands:** schematic complete (scripted edits), ERC: 6 `lib_symbol_mismatch` notices only. Netlist checked
after every edit. No PCB. Decisions 1–7, 9–14 apply.

**Waiting for the owner:** decisions 17 (panel cable) and 18 (battery voltage / NTC) are **[proposed]**.

## Next

1. Open in KiCad: tidy what the scripts placed (labels, part positions), run *Update Symbols from Library*
   (BC817, LMR51610, USB-C), then ERC.
2. After `/emc pdm-4ch` and `/validate pdm-4ch deep`: fix findings.
3. Verify the custom footprint `Infineon_PG-TDSO-14_ThermalVias` against the JLCPCB/EasyEDA footprint (C534868).
4. Remaining part checks from the BOM audit: Kangnex WJ15EDGVC CAN connector on the Phoenix MCV footprint; PESD2CAN
   pin 3 = common; Molex 39301080 = 5569-08A2 (if still used).
5. PCB layout after the terminal blocks and enclosure are decided (`/system mechanical`): 2 oz, VS copper on both
   layers around the cooling tabs, switches spread out and away from the ESP32.

## For /system

- Panel connector redesign (decision 17) changes the shared `analog_sw` sheet: both boards.
- Battery-voltage measurement / NTC (decision 18) needs a pin-map change.
- Terminal blocks: ~20 poles in 1 module width (power 2, outputs 4, panel 9, CAN 4–5).
