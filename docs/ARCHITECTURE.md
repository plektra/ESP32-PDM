# Architecture

The system's constitution: what both boards share, the invariants, and the budgets. Changed only in `/system`
sessions, with a decision in [decisions.md](decisions.md). Rationale and calculations: [design-notes.md](design-notes.md).

## Boards

| Board | Folder | Output stage | Variant ID (R42) |
|---|---|---|---|
| 4-channel | `hardware/pdm-4ch` | 4 × PROFET+24V (BTT6050 / BTT6010 per channel) | 10 kΩ (1.65 V) |
| High-current | `hardware/pdm-hc2` | 2 × TPS48110A-Q1 + back-to-back MOSFETs | 4.7 kΩ (1.05 V) |

## Shared sheets (contract between the boards)

`power-usb`, `can` and `analog_sw` and the controller part of the root sheet are the same on both boards. A change to
them is a system change: make it on both boards in the same session (or note it in the other board's `STATUS.md`).

| Sheet | Contents |
|---|---|
| root (controller) | ESP32-S3-MINI-1-N8, native USB on IO19/IO20, boot/reset buttons, variant ID, battery input J10 + SMCJ30CA (D30) and C30 2.2 µF/100 V C170101 (decision 79, within decision 26's range) on the terminal net VBAT_IN, FL30 (DNP ferrite) bridged by JP30 copper to VS (on pdm-4ch only: to `VBAT_FL`, then the reverse-battery blocker Q30 IPT007N06N with U30 LM74500-Q1 and C32 to VS, plus TVS D31 SMDJ40CA C42371557 across Q30 from VS to `VBAT_FL`, decisions 82, 88, 89, 92, 96; HC2 unchanged, decision 40), C31 100 µF/63 V on VS (decision 41), battery-voltage divider (R60/R61/C60), NTC TH1 (R62/C61) |
| `power-usb` | LMR51610 buck (4–65 V) → 3.3 V, 60 V PTC, SMAJ30CA, diode-OR with USB VBUS |
| `can` | CA-IS3050G isolated CAN (SOIC-8-WB) with TXD pull-up R70, DNP CMC FL1 (bridged by 0 Ω R71/R72) and DNP Y-cap C70 (design-notes §8.5); L78M05ABDT 5 V from NET-S (DPAK, footprint ≈ 10.4 × 6.7 mm, decision 45, design-notes §8.3); SMAJ18CA, PESD2CAN; LEN 1 (49.3 mA worst case, measure on the first prototype) |
| `analog_sw` | Panel connector J5 (decision 17): 4 protected switch inputs (SMAJ30CA, 2 × 2 k load, 10 k + 4.7 k/BZT52C3V3 divider, 100 nF); fused switch supply SW_SUPPLY (F4 PTC, SMAJ30CA, 100 nF); 4 constant-current LED sinks (MMBT5551 + 470 Ω, ≈ 5 mA, SMAJ30CA + 100 Ω + 1 nF per line); SW_SUPPLY sense SW_SENSE (R49 10 k, R57 4.7 k/D24 BZT52C3V3, C21 470 nF; R58 10 k on the root sheet to IO12; decision 93) |

### Pin map (ESP32-S3)

| Pin | 4-channel | High-current |
|---|---|---|
| IO1 | MOD_ID (ADC) | MOD_ID (ADC) |
| IO2–IO5 | channel current sense IS1–IS4 (ADC) | IO2/IO3 IMON1/2 (ADC); IO4/IO5 OUT1/OUT2 sense (ADC1, 220 k/22 k + 100 nF, float-run detection; decision 39) |
| IO6–IO8, IO11 | channel drive ch1–3 on IO6–IO8, ch4 on IO11 (diode-OR with the switch inputs) | IO6/IO7 drive ch1/2; IO8, IO11 unused (2.2 k pull-downs R1/R2) |
| IO9 | NTC (ADC1) | NTC (ADC1) |
| IO10 | VBAT_SENSE (ADC1) | VBAT_SENSE (ADC1) |
| IO12 | SW_SENSE, digital input: high = SW_SUPPLY present (decision 93) | same |
| IO13 | spare | spare |
| IO14, IO15, IO16, IO21 | switch state SW1–SW4 | switch state SW1–SW4 (3–4 sense-only) |
| IO17 / IO18 | CAN TX / RX | CAN TX / RX |
| IO19 / IO20 | USB D− / D+ | USB D− / D+ |
| IO33 | DEN (diagnostics enable, all channels) | spare |
| IO34–IO37 | spare | FLT_I1, FLT_T1, FLT_I2, FLT_T2 |
| IO38–IO41 | panel LED sinks LED1–LED4 (DIAG1–4) | panel LED sinks LED1–LED4 (DIAG1–4) |

Channel drive pins must stay on RTC GPIOs (IO0–IO21) for output hold through deep sleep; IO38–IO41 are not RTC GPIOs, so the panel LEDs are off in deep sleep.

## Invariants

1. A physical switch turns its output on without the ESP32 and without the 3.3 V rail (decision 6).
2. No relays; every output is a protected solid-state switch (decision 1).
3. 12 V and 24 V systems; every part on the battery side rated for ≥ 30 V continuous and ≥ 48 V transients (decision 3).
4. Every external line is filtered and surge-protected at the connector (long leads, VHF on board). The only
   exception is a PROFET output (pdm-4ch J11). It is protected through the switch itself: positive surges through
   its body diode to VS and the input TVS D30 at J10 (with wide VS copper to D30), negative surges by its own clamp
   (VS − VDS(AZ)). It keeps a DNP SMAJ30CA footprint to GND at the connector. Every other external line, including
   the HC2 outputs, has its own TVS at the connector (decision 27).
5. Parts: JLCPCB basic/preferred where one fits; pinouts, footprints and limits verified in the datasheet, never invented (decision 2).
6. No conductive path from the circuit to the mounting surface or hull (decision 11).
7. Load dump is a system-level responsibility; the README says so (decision 12).
8. The automatic bilge float-switch circuit never depends on the PDM (decision 15).
9. No 3.3 V (or other logic rail) leaves the board on a cable; panel switches and LEDs run from the fused switch supply (decision 17).
10. Analog measurements the firmware relies on (MOD_ID, current sense, VBAT_SENSE, NTC) use ADC1 pins (IO1–IO10); ADC2 is shared with Wi-Fi.

## Mechanics

Same four non-plated M3 holes (H1–H4) for every mounting (decision 97). DIN rail: bare board on a plastic carrier, PCB edge-on to the rail, about 36 mm of rail per unit, in an enclosure the installer provides. Alternative: a 3D-printed vented ASA enclosure, also for flat mounting. Nothing conductive from carrier, screws or enclosure reaches board copper (invariant 6).

Connectors (decision 98): keyed plugs on right-angle sockets, hand-soldered, plugs pull away from the board edge.

| Connector | Socket + plug | Rating UL / IEC | Row length | Reach from the board edge |
|---|---|---|---|---|
| J10, both | KF2EDGSRAM-10.16-2P C6394053 + locking C6394029 | 65 / 57 A | 38.1 mm | 34 mm |
| J11, 4-ch | KF2EDGRC-5.08-4P C441238 + C440882 | 10 / 15 A | 21.9 mm | 8.4 mm |
| J11, HC2 | KF2EDGSRM-7.62-2P C577772 + locking C577752 | 30 / 32 A | 30.5 mm | 29 mm |
| J5, both | WJ15EDGRC-3.81-10P C26895 + C26865 | 8 / 7 A | 39.0 mm | 7.25 mm |
| J4, both | WJ15EDGRC-3.81-04P C7245 + C7244 | 8 / 7 A | 16.1 mm | 7.25 mm |

Board depth about 65 mm (4-ch) and 75 mm (HC2), length up to 100 mm, set at layout.

## Budgets [estimate until measured]

| Budget | Figure | Source |
|---|---|---|
| Ambient | 40 °C engine room (own printed enclosure: air +2…10 °C). Shared enclosure: full rating up to 50 °C air inside the box, BTT6050 at 3 A up to about 65–70 °C; each board gives off about 9 W at full load | decisions 9, 97 |
| 4-ch, BTT6050 per channel | 4 A at 2 oz copper | `tools/heat_budget.py` |
| 4-ch, BTT6010 per channel | ≈ 8 A | `tools/heat_budget.py --mix` |
| HC2 per channel | ≈ 15 A continuous; breaker ~17.5 A / 146 ms (RIWRN 68 k, ≈ 15–20 A over tolerances); fast trip 80 A; external breaker ≤ 15–18 A per output plus firmware soft fuse (decision 39); load input capacitance ≤ ≈ 50 µF per output (decisions 77, 94) | `tools/heat_budget.py --part HC-2xBSC030`, TPS4811-Q1 equations |
| Shared supply path | ≤ 2 mΩ (terminal + VS copper), plus on pdm-4ch the blocker Q30 (≤ 0.75 mΩ at 25 °C, ≈ 1.1 mΩ hot); board input limit 32 A (4-ch) / 36 A (HC2), decision 95 | design-notes §4, §8.6 |
| Controller power | ≈ 0.47 A at 3.3 V peak (ESP32 radio); panel LEDs no longer on 3.3 V; F1 500 mA hold | design-notes |
| Panel switch supply | ≈ 63 mA (4 × 7.5 mA switch load + 4 × 2.6 mA divider + 2.6 mA SW_SENSE + 4 × 5 mA LEDs at 30 V); F4 500 mA hold; MMBT5551 ≈ 0.13 W each at 30 V | decisions 17, 74, 93 |

## Open system items

See `docs/CONTINUE-FROM-HERE.md` (order of work) and the **[proposed]** rows in `decisions.md`.
