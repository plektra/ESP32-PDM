# Decisions

Every design decision, numbered. Numbers are never reused. **Confirmed** = decided by the owner; **[proposed]** =
recommended, not decided. Background and calculations: [design-notes.md](design-notes.md). New decisions take the next
free number (`/handoff` adds them).

| # | Date | Area | Decision | Status |
|---|---|---|---|---|
| 1 | 2026-10-29 | system | Purpose: replace mechanical relays with smart high-side switching, controlled by ordinary panel switches **and** over NMEA 2000; status and current reported on the bus. No relays in the product. | confirmed |
| 2 | 2026-10-29 | system | **Low cost is the guiding principle.** JLCPCB PCBA; JLCPCB basic or preferred parts wherever one fits; few unique extended parts. | confirmed |
| 3 | 2026-10-29 | system | Supply: 12 V and 24 V systems, up to ~30 V while charging. | confirmed |
| 4 | 2026-10-30 | system | Keep the ESP32-S3 (NMEA 2000 / SensESP / Signal K ecosystem, Wi-Fi, OTA). Native USB; no USB-UART bridge. | confirmed |
| 5 | 2026-10-30 | system | One board per product, built from shared schematic sheets; the earlier base board + output module split is dropped. | confirmed |
| 6 | 2026-10-30 | system | Physical switch inputs drive the outputs in hardware, independent of the ESP32 and its 3.3 V rail (protected direct inputs, no optocoupler). | confirmed |
| 7 | 2026-10-30 | pdm-4ch | 4-channel board with Infineon PROFET+24V switches, fitted per channel at assembly: BTT6050-1ERA (≈ 4 A) or pin-compatible BTT6010-1ERA (≈ 8 A). BTT6030 not used. | confirmed |
| 8 | 2026-10-30 | pdm-hc2 | High-current board: 2 channels, TI TPS48110A-Q1 + back-to-back MOSFETs (≈ 15 A continuous with BSC030N08NS5). | confirmed |
| 9 | 2026-10-30 | system | Heat budget is part of the design process: 40 °C engine-room ambient, `tools/heat_budget.py`. | confirmed |
| 10 | 2026-10-30 | mechanical | Enclosure 3D printed (ASA), **vented**, installed in an enclosed location. Two mountings: DIN rail with the PCB perpendicular to the rail (target 1 module width, 17.5 mm) and flat (wall/ceiling). | confirmed |
| 11 | 2026-10-30 | mechanical | No metal base plate: risk of bridging DC negative to a steel hull, and cost. | confirmed |
| 12 | 2026-10-30 | system | Load dump is **not** handled on the board; the README states it (system-level protection required). | confirmed |
| 13 | 2026-10-30 | system | Low-power modes are entered by a bus command (NMEA 2000 or Signal K); local switches always work and can wake the node. Panel LEDs dimmable. | confirmed |
| 14 | 2026-10-29 | system | Board variant ID: resistor divider on IO1 (`MOD_ID`, 10 kΩ pull-up). 4-ch = 10 kΩ, HC2 = 4.7 kΩ. | confirmed |
| 15 | 2026-10-30 | system | Bilge pumps: the automatic float-switch circuits stay wired directly to the battery; the PDM is used only for manual forced run (in parallel with the float switch). | confirmed |
| 16 | 2026-10-30 | system | Moved to vega-systems (not part of ESP32-PDM). | moved |
| 17 | 2026-10-30 | system | Panel cable: fused switch-supply output on the panel connector, LEDs on constant-current sinks (BC817 + emitter resistor, ~5 mA, PWM-dimmable), TVS on every line, no 3.3 V on the cable. | [proposed] |
| 18 | 2026-10-30 | system | Battery-voltage measurement and an NTC near the switches; needs ADC pins (move panel LED drive off IO10–IO13). | [proposed] |
| 19 | 2026-10-30 | pdm-hc2 | For loads ~21 A (searchlight), fit lower-RDS(on) MOSFETs (candidate onsemi NTMFS5C612NL); for halogen inrush, disable the fast short-circuit trip only after an SOA check. | [proposed] |
