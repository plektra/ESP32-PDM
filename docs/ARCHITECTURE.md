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
| root (controller) | ESP32-S3-MINI-1-N8, native USB on IO19/IO20, boot/reset buttons, variant ID, battery input J10 + SMCJ30CA (D30) and C30 2.2 µF/100 V C170101 (decision 79, within decision 26's range) on the terminal net VBAT_IN, FL30 (DNP ferrite) bridged by JP30 copper to VS (on pdm-4ch only: to `VBAT_FL`, then the reverse-battery blocker Q30 AGM601LL C5464765 (decision 108) with U30 LM74500-Q1 and C32 to VS, plus TVS D31 SMDJ40CA C42371557 across Q30 from VS to `VBAT_FL`, decisions 82, 88, 89, 92, 96; HC2 unchanged, decision 40), C31 100 µF/63 V on VS (decision 41), battery-voltage divider (R60/R61/C60), NTC TH1 (R62/C61) |
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
| IO13 | firmware status LED D7 (R59 2.2 k to GND, high = on) | same |
| IO14, IO15, IO16, IO21 | switch state SW1–SW4 | switch state SW1–SW4 (3–4 sense-only) |
| IO17 / IO18 | CAN TX / RX | CAN TX / RX |
| IO19 / IO20 | USB D− / D+ | USB D− / D+ |
| IO33 | DEN (diagnostics enable, all channels) | spare |
| IO34 | spare | FLT_I1 |
| IO35–IO37 | unfitted service footprint J6 (pins 4–6) | FLT_T1, FLT_I2, FLT_T2 (J6 pins 4–6 not connected) |
| IO38–IO41 | panel LED sinks LED1–LED4 (DIAG1–4) | panel LED sinks LED1–LED4 (DIAG1–4) |
| IO42 | unfitted service footprint J6 (pin 7) | same |
| TXD0 / RXD0 | serial console on unfitted J6 (pins 2 / 3; pin 1 GND, pin 8 3V3, on-board only) | same |

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

## PCB layout rules

The live list. The EMC reviews, design-notes §8 and older decision rows give the reasons; where they differ from this
list, this list holds. On `pdm-4ch` the router (`hardware/pdm-4ch/scripts/pf_route.py`) and the build
(`build_routing.sh`) enforce rules 2–12 and report rules 13–17 (`scripts/emc_report.py`); `pdm-hc2` follows the same rules when its layout starts.

1. All SMT parts on the top side (decision 122). Connectors on the edges named in decision 128.
2. Four layers: F.Cu/B.Cu 2 oz carry all load current; In1 is a solid GND plane (GND_CAN its own area) with no
   signal on it; In2 is VS under the switches and GND elsewhere, and carries signals (decisions 150, 165).
3. Power pour outlines (VS, VBAT_IN, VBAT_FL, OUT1–4) are closed to foreign tracks and vias, except within 0.6 mm of
   a pad that must be reached. Each pour keeps its island count and at least 95 % of its area (decisions 164, 172).
4. 1.0 mm from VS and VBAT_IN copper to every other net on the outer layers; the board's 0.2 mm applies only within
   0.6 mm of a routed pad (EMC review 2026-11-03 rule 7, decision 219).
5. VS-In2: all 40 PROFET thermal vias sit in copper, and no signal runs over a thermal-via field plus 1 mm. In2 runs
   inside the pour stay 1.5 mm from its outline, except where they cross its east edge. The pour keeps at least 75 %
   of 1190.7 mm²; every piece is tied to VS by vias (decisions 178, 218).
6. CAN isolation: 8.1 mm between logic copper and GND_CAN copper across the U5 body and C70 (y 53.2–66.6),
   4.0 mm elsewhere, on all four layers; no copper under U5 between its pin rows; nothing but C70 crosses
   (EMC review 2026-10-30 rule 9, decision 217).
7. No copper under the antenna (x 45.85–92.5, y 0–4.5) and inside the Ø 8 mm hole keep-outs (decision 123).
   Copper stays 0.5 mm from the board edge.
8. Tracks and clearance 0.2 mm, vias 0.6/0.3 mm, +3V3 0.3 mm. Exceptions on `pdm-4ch`: VBUS and Net-(D3-A) 0.2 mm
   at J3 (decision 219), a 0.15 mm neck on CANL_XCVR between R71 and R72 (decision 168).
9. No via on an SMD pad, except thermal tabs of at least 10 mm² (the U6 DPAK tab; decision 225). In2 tracks stay 1.8 mm from GND through-hole pads (thermal relief). Two vias of one net
   are at least 0.55 mm apart.
10. GND copper on F.Cu, B.Cu and In2 is fill, not the reference plane: a fragment needs two vias to In1 or is
    removed by a fill keep-out; a GND pad the fill cannot reach gets a stub and a via (decisions 206, 214, 219).
11. Buck SW and CB nets on F.Cu only, no via in the hot loop (decision 165). The CAN and USB pairs are fixed
    hand routes (decisions 168, 169).
12. The board file is the output of the build: a change goes into the scripts or `pf_routes.json`, never into the
    board alone (decision 163). A build is accepted with 0 DRC errors, schematic parity 0 and the gates of rules
    3, 5 and 10.
13. A filter's shunt capacitor sits within 5 mm of its series resistor, with a GND via beside its pad; the track
    onward to the protected part may be long (rule 1 of 2026-11-17, design-notes §8.24).
14. TVS flow-through, also on differential lines: every protected line passes through its TVS pad, and nothing taps
    the line between the connector and the clamp (rule 2 of 2026-11-17).
15. Every TVS and RF filter-capacitor GND pad has its own GND via within 2.5 mm, never only fill or grid stitching
    (decision 223).
16. Dead-end copper on the buck SW node (DNP snubber or option footprints) stays short (≤ 3 mm of spur) and ≥ 3 mm
    from the FB node and its divider (rule 3 of 2026-11-17).
17. Rules 13–15 are re-checked after every reroute: the router knows nets, not the order of parts along a filtered
    line. On pdm-4ch `scripts/emc_report.py` reports them after each build (rule 4 of 2026-11-17, decision 223).

## Mechanics

Same four non-plated M3 holes (H1–H4) for every mounting (decision 97), one in each corner, hole centres 4 mm from both edges: 92 mm apart along the rail-side edge, 67 mm across (decisions 128, 138); no copper and no parts within Ø 8 mm of each hole (decision 123). DIN mount: one solid printed ASA part on the two rail-side holes, or a long version also reaching the far corners along the short edges (one 75 mm depth, since both boards are 100 × 75 mm), nylon M3 hardware (decision 123). DIN rail: bare board on a plastic carrier, PCB edge-on to the rail, about 36 mm of rail per unit as a soft target that never limits connectors, layout or mount (decision 127; decision 123's arms-instead-of-plate choice for the long mount may be revisited), in an enclosure the installer provides. Alternative: a 3D-printed vented ASA enclosure, also for flat mounting. Nothing conductive from carrier, screws or enclosure reaches board copper (invariant 6).

Cable entry (decision 237): no connectors in the enclosure wall except CAN. Power and output cables pass through
nylon glands, panel and thin wires through a printed clamp comb, all from the bottom face (drip loop), straight
to the board plugs. NMEA 2000 enters on a panel-mount M12 5-pin connector (the standard drop-cable plug) wired short and direct
to J4, whose protection stays unchanged (invariant 4); its shield pin stays open (decision 28) and the body is plastic
or isolated from all copper (invariant 6). The DIN mount carries cable-tie anchors so no plug carries a cable; in the installer's enclosure its glands seal.

Connectors (decision 98): keyed plugs on right-angle sockets, hand-soldered, plugs pull away from the board edge. Exception for the pdm-4ch prototype: J10 is a fixed screw terminal, wire entry at the board edge (decision 121).

| Connector | Socket + plug | Rating UL / IEC | Row length | Reach from the board edge |
|---|---|---|---|---|
| J10, 4-ch | KF135T-10.16-2P C475108, fixed screw terminal, M4, 10 mm², no plug (decision 121) | 65 / 57 A | 20.3 mm | 18.6 mm |
| J10, HC2 | KF2EDGSRAM-10.16-2P C6394053 + locking C6394029 | 65 / 57 A | 38.1 mm | 34 mm |
| J11, 4-ch | KF2EDGRC-5.08-4P C441238 + C440882 | 10 / 15 A | 21.9 mm | 8.4 mm |
| J11, HC2 | KF2EDGSRM-7.62-2P C577772 + locking C577752 | 30 / 32 A | 30.5 mm | 29 mm |
| J5, both | WJ15EDGRC-3.81-10P C26895 + C26865 | 8 / 7 A | 39.0 mm | 7.25 mm |
| J4, both | WJ15EDGRC-3.81-04P C7245 + C7244 | 8 / 7 A | 16.1 mm | 7.25 mm |

C577772 (pdm-hc2 J11) sources: any seller, flange header KF2EDGSRM-7.62 only; no substitute socket (decision 120). Connector stock is re-checked for the next revision (decision 121).

Both boards are 100 × 75 mm (decisions 128, 138), one 100 mm edge on the rail side. pdm-4ch has 4 copper layers, 2 oz outer (decision 150; owner's quote €43.95 for 5 boards, +€7.07 per order over 2 layers); pdm-hc2 follows PCB layout rule 2 when its layout starts. All SMT parts on the top side; a bottom-side part needs an owner ruling (decision 122).

## Firmware (decisions 230–235)

Shared by both boards; `firmware/` (draft, pdm-4ch first). PlatformIO, Arduino-ESP32, NMEA2000 library with the own
TWAI driver; hardware-free control logic tested on the host. Wi-Fi, Signal K, OTA and web settings through SensESP v3
after a build trial (230). Version 1: Active mode and password-protected OTA; Eco/Sleep after bring-up (233).

- Panel LED on = output on, blinking = latched fault; no automatic retry; a fault clears when the switch opens or the
  bus commands off; a bus-switched output comes back off after a reset (231). The firmware never overrides a closed
  panel switch (invariant 1).
- NMEA 2000: switch bank 127501/127502, 127751 per channel, alerts 126983/126984 (232); the same alerts go to Signal K.
- DEN (pdm-4ch) is pulsed only while sampling IS and dropped at once on a full-scale reading (decision 36), also
  with the hardware RIS cover of decision 235.
- PWM on the drive pins at 100 Hz within the rating of decision 234; pdm-hc2 has no PWM until its gate slew is measured.

## Budgets [estimate until measured]

| Budget | Figure | Source |
|---|---|---|
| Ambient | 40 °C engine room (own printed enclosure: air +2…10 °C). Shared enclosure: full rating up to 50 °C air inside the box, BTT6050 at 3 A up to about 65–70 °C; each board gives off about 9 W at full load | decisions 9, 97 |
| 4-ch, BTT6050 per channel | 4 A at 2 oz copper | `tools/heat_budget.py` |
| 4-ch, BTT6010 per channel | ≈ 8 A; no BTT6010 build in this version (decision 103) | `tools/heat_budget.py --mix` |
| HC2 per channel | ≈ 15 A continuous; breaker ~17.5 A / 146 ms (RIWRN 68 k, ≈ 15–20 A over tolerances); fast trip 80 A; external breaker ≤ 15–18 A per output plus firmware soft fuse (decision 39); load input capacitance ≤ ≈ 50 µF per output (decisions 77, 94) | `tools/heat_budget.py --part HC-2xBSC030`, TPS4811-Q1 equations |
| Shared supply path | ≤ 2 mΩ (terminal + VS copper), plus on pdm-4ch the blocker Q30 AGM601LL (≤ 1.6 mΩ at 25 °C, ≈ 2.1 mΩ at its 16 A temperature; Tj 66–80 °C at 40 °C with ≥ 2 cm² 2 oz drain copper, decisions 108, 109); board input limit 16 A (4-ch, decision 103) / 36 A (HC2, decision 95) | design-notes §4, §8.6 |
| Controller power | ≈ 0.47 A at 3.3 V peak (ESP32 radio); panel LEDs no longer on 3.3 V; plus ≈ 0.7 mA continuous for the power LED D8 (also in Eco and Sleep) and ≈ 0.7 mA for the status LED D7 while lit; F1 500 mA hold | design-notes §8.7 |
| Panel switch supply | ≈ 63 mA (4 × 7.5 mA switch load + 4 × 2.6 mA divider + 2.6 mA SW_SENSE + 4 × 5 mA LEDs at 30 V); F4 500 mA hold; MMBT5551 ≈ 0.13 W each at 30 V | decisions 17, 74, 93 |

## Open system items

See `docs/CONTINUE-FROM-HERE.md` (order of work) and the **[proposed]** rows in `decisions.md`.
