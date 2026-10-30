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
| root (controller) | ESP32-S3-MINI-1-N8, native USB on IO19/IO20, boot/reset buttons, variant ID, battery input J10 + SMCJ30CA |
| `power-usb` | LMR51610 buck (4–65 V) → 3.3 V, 60 V PTC, SMAJ30CA, diode-OR with USB VBUS |
| `can` | ISO1044 isolated CAN, TPS7B91 5 V from NET-S, SMAJ18CA, PESD2CAN |
| `analog_sw` | 4 protected switch inputs (SMAJ30CA, 4.7 k load, 10 k + 4.7 k/BZT52C3V3 divider, 100 nF), 4 LED drivers |

### Pin map (ESP32-S3)

| Pin | 4-channel | High-current |
|---|---|---|
| IO1 | MOD_ID (ADC) | MOD_ID (ADC) |
| IO2–IO5 | channel current sense IS1–IS4 (ADC) | IO2/IO3 IMON1/2 (ADC); IO4/IO5 spare |
| IO6–IO9 | channel drive (diode-OR with the switch inputs) | IO6/IO7 drive ch1/2; IO8/IO9 unused |
| IO10–IO13 | panel LED drivers | panel LED drivers |
| IO14, IO15, IO16, IO21 | switch state SW1–SW4 | switch state SW1–SW4 (3–4 sense-only) |
| IO17 / IO18 | CAN TX / RX | CAN TX / RX |
| IO19 / IO20 | USB D− / D+ | USB D− / D+ |
| IO33 | DEN (diagnostics enable, all channels) | spare |
| IO34–IO37 | spare | FLT_I1, FLT_T1, FLT_I2, FLT_T2 |

## Invariants

1. A physical switch turns its output on without the ESP32 and without the 3.3 V rail (decision 6).
2. No relays; every output is a protected solid-state switch (decision 1).
3. 12 V and 24 V systems; every part on the battery side rated for ≥ 30 V continuous and ≥ 48 V transients (decision 3).
4. Every external line is filtered and surge-protected at the connector (long leads, VHF on board).
5. Parts: JLCPCB basic/preferred where one fits; pinouts, footprints and limits verified in the datasheet, never invented (decision 2).
6. No conductive path from the circuit to the mounting surface or hull (decision 11).
7. Load dump is a system-level responsibility; the README says so (decision 12).
8. The automatic bilge float-switch circuit never depends on the PDM (decision 15).

## Budgets [estimate until measured]

| Budget | Figure | Source |
|---|---|---|
| Ambient | 40 °C engine room (enclosure air +2…10 °C) | decision 9 |
| 4-ch, BTT6050 per channel | 4 A at 2 oz copper (3.5 A provisional in 1 module width) | `tools/heat_budget.py` |
| 4-ch, BTT6010 per channel | ≈ 8 A | `tools/heat_budget.py --mix` |
| HC2 per channel | ≈ 15 A continuous; breaker 25 A / 146 ms; fast trip 80 A | `tools/heat_budget.py --part HC-2xBSC030`, TPS4811-Q1 equations |
| Shared supply path | ≤ 2 mΩ (terminal + VS copper); input terminal ≈ 40 A (4-ch) / ≈ 50 A (HC2) | design-notes §4 |
| Controller power | ≈ 0.47 A at 3.3 V peak (ESP32 radio + LEDs); F1 500 mA hold | design-notes |

## Open system items

See `docs/CONTINUE-FROM-HERE.md` (order of work) and the **[proposed]** rows in `decisions.md`.
