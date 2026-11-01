# Decisions

Every design decision, numbered. Numbers are never reused. **Confirmed** = decided by the owner; **[proposed]** =
recommended, not decided; **auto** = a two-way-door decision made by an agent under decision 23, which the owner may
overturn. Background and calculations: [design-notes.md](design-notes.md). New decisions take the next
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
| 16 | 2026-10-30 | system | Searchlight heating: an edge heater ring is not enough for de-icing; a film-type heater is preferred, but cost must be reviewed before deciding. | open |
| 17 | 2026-10-30 | system | Panel cable (J5, 10 poles): 1–4 switch inputs, 5 fused switch supply SW_SUPPLY (VS via PTC F4 1812L050/60GR, SMAJ30CA, 100 nF), 6–9 LED cathodes to constant-current sinks (MMBT5551 + 470 Ω emitter, 1 k/10 k base from the GPIO, ≈ 5 mA, PWM-dimmable, 1 nF on the collector), 10 GND/drain. Panel LEDs: anode to SW_SUPPLY, no resistor at the panel; works up to ≥ 10 m of cable at 12 V and 24 V. SMAJ30CA on every line; no 3.3 V on the cable. A short in the panel cable trips F4 and disables that board's panel switches (bus control keeps working). | confirmed |
| 18 | 2026-10-30 | system | Pin map: VBAT_SENSE on IO10 (220 k/22 k + 100 nF, 33 V full scale), NTC on IO9 (10 k B3380 NTC APV ANTC1608-103F3380FB + 10 k pull-up, placed next to the output switches); both ADC1. Panel LED drives move to IO38–IO41; channel-4 drive (4-ch) moves IO9 → IO11; IO12/IO13 spare. | confirmed |
| 19 | 2026-10-30 | pdm-hc2 | For loads ~21 A (searchlight), fit lower-RDS(on) MOSFETs (candidate onsemi NTMFS5C612NL); for halogen inrush, disable the fast short-circuit trip only after an SOA check. | [proposed] |
| 20 | 2026-10-30 | system | Panel LED behaviour and fault handling: LED on = output on, blinking = fault (firmware). Alerts and failures are published to Signal K so they can be acknowledged and muted there; the failure modes per output (what blinks, what alerts, what is latched, what clears) are still to be designed in `/system firmware`. | open |
| 21 | 2026-10-30 | system | Sense the panel switch supply: SW_SUPPLY → 100 k/10 k divider (+ 100 nF) → spare GPIO IO12, so the firmware can alert when F4 has tripped (otherwise indistinguishable from "all switches off"). Two basic resistors per board. | [proposed] |
| 22 | 2026-10-30 | system | Unattended agent runs (`docs/AUTONOMY.md`): agents make small decisions themselves (recorded as **auto**); bigger design changes go to the owner through `docs/OWNER-INBOX.md`. Pilot: only the reviewers run unattended. | confirmed; policy replaced by 23 |
| 23 | 2026-11-01 | system | Autonomy by reversibility (one-way/two-way doors, `docs/AUTONOMY.md`) replaces the small/big rule of decision 22. One-way doors go to the owner: money (orders, changes to ordered boards), the owner's confirmed, proposed or open decisions, weakening safety or invariants, facts only the owner has, CRITICAL findings. Everything else is a two-way door: agents decide (recorded as **auto**, listed in the inbox digest, undoable with `orchestrate.py undo`); questions with a sensible default are answered with it. | confirmed |
| 24 | 2026-11-01 | system | Unattended fixes (`docs/AUTONOMY.md`, "Unattended fixes"): approved items (owner rulings and two-way decisions) are applied by agents without the owner – a planner makes work packages, board-fixer agents edit the schematics, the orchestrator gates every change (scope, ERC, netlist against declared refs, LCSC, shared sheets equal) before merging into `auto/pilot`, and a validator re-checks each board. One-way doors still go to the owner; the owner merges into `main` and reviews before any order. | confirmed |
