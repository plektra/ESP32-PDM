# pdm-4ch status

Updated: 2026-10-30

**Where it stands:** schematic complete (scripted edits), ERC: 6 `lib_symbol_mismatch` notices only. Netlist checked
after every edit. No PCB. Decisions 1–7, 9–14, 17, 18 apply. Panel connector J5 and the pin map changed on
2026-10-30 (decisions 17, 18): SW_SUPPLY on J5.5, MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9,
channel-4 drive moved to IO11.

**Waiting for the owner:** decision 21 **[proposed]** (sense SW_SUPPLY on IO12 so a tripped F4 can be reported).

## Next

1. Open in KiCad: tidy what the scripts placed (labels, part positions; the new parts in `analog_sw` and the
   VBAT/NTC block at the bottom of the root sheet), run *Update Symbols from Library* (LMR51610, USB-C; keep Q3–Q6
   on the BC817 symbol with value MMBT5551 – same pinout), then ERC.
2. After `/emc pdm-4ch` and `/validate pdm-4ch deep`: fix findings.
3. Verify the custom footprint `Infineon_PG-TDSO-14_ThermalVias` against the JLCPCB/EasyEDA footprint (C534868).
4. Remaining part checks from the BOM audit: Kangnex WJ15EDGVC CAN connector on the Phoenix MCV footprint; PESD2CAN
   pin 3 = common; Molex 39301080 = 5569-08A2 (if still used).
5. PCB layout after the terminal blocks and enclosure are decided (`/system mechanical`): 2 oz, VS copper on both
   layers around the cooling tabs, switches spread out and away from the ESP32; TH1 next to the hottest switch;
   J5 TVSs at the connector.

## For /system

- Terminal blocks: J5 is still a 2×5 pin header; ~20 poles in 1 module width (power 2, outputs 4, panel 10, CAN 4–5).
