# Validation pdm-4ch, after decisions 220, 225–226, 238 and the CPL fix (2026-11-23)

Scope: `hardware/pdm-4ch` at commit b238c0a. Since the last validation (2026-11-18, commit 2b18b6b) these changed:
- the RIS resistors are now C844867 (decision 238);
- test pads TP1/TP30/TP70–72 were added (decision 226);
- the V1 via-in-pad fix and a reroute were done (decision 225);
- title blocks and licence silkscreen were added (decision 220);
- the CPL rotations were corrected (`CPL_FIX`).

I worked in a scratch folder and edited no design file.

## Findings

### CRITICAL
None.

### MAJOR

- **V1 – U5 has no bypass capacitor near its VCC1 pin. The cap meant for it (C10) sits by the ESP32.**
  - **Location:** `can.kicad_sch` (shared sheet) has C10 0.1 µF C307331 on +3V3 as the isolator's logic-side cap. On the PCB, C10 sits under U1: pad 2 is 13.3 mm from U1.3 and **33.6 mm from U5.1**. Design-notes §8.9 lists it as "3V3 decoupling C8/C10" for U1. The nearest +3V3 capacitor to U5.1 is C8 at 31.9 mm. The nearest +3V3 via to U5.1 is 2.87 mm away and the nearest GND via to U5.4 is 1.58 mm away. The VCC2 side is fine: C12 is 3.0 mm and C11 5.4 mm from U5.8.
  - **What is wrong:** Chipanalog CA-IS305x datasheet v1.10 (pcbparts mirror of LCSC C528763), p. 5 Table 6-1 says: "Bypass VCC1 to GND1 with a 0.1 µF capacitor as close to the device as possible". p. 18 (layout) says: "at least a 0.1 µF low-ESR decoupling capacitor between VCC1 and GND1 … as close as possible to the device to minimize inductance". The cached facts file `docs/part-facts/C528763.md` says the same.
  - **Failure mechanism:** U5 sends data across its capacitive barrier on a high-frequency carrier. Its VCC1 switching current now returns through about 34 mm of +3V3 track (roughly 15–30 nH) instead of a local capacitor. At carrier frequencies that is tens of ohms, so supply bounce at U5.1 is not held down. The results would be edge jitter or bit errors on the NMEA 2000 link, the board's only bus interface. The loop also radiates. That matters for the IEC 60945 target (decision 28) and for the marine VHF band, with a radio on board. The size of the effect is UNVERIFIED: no measurement, and the datasheet gives no figure. The requirement itself is verified.
  - **Evidence:** pcbnew distance scan of the current board; netlist (+3V3 nodes: C10, C3, C8 are the only capacitors); datasheet pages above.
  - **Cheapest fix:** move C10 to U5 pins 1/4 on the logic side. Put pad 1 on U5.1 and pad 2 on a GND via next to U5.4, within about 2 mm, outside the rule 6 barrier. Then rerun the build (`pf_route.py` → `build_routing.sh`, `silk.py`, `emc_report.py`) and rebuild the fab package.
    - No schematic or BOM change is needed. The part already belongs to U5 on the shared sheet.
    - U1 keeps C8 22 µF at 15 mm plus the module's own internal decoupling (Espressif MINI-1 datasheet v1.7 §8, module schematic p. 39).
    - Optional: if the owner also wants Espressif's 0.1 µF at U1 pin 3 (peripheral schematic p. 41, C3 0.1 µF), add one more C307331. It is the same part already in this BOM line, so there is no new loading fee. Only add it if room allows. It is not needed to fix V1.
    - pdm-hc2: place C10 at U5 when its layout starts (shared sheet, same part).

### MINOR
None.

## Checked and OK

- **ERC** (`kicad-cli sch erc --severity-all`): 5 warnings, all `lib_symbol_mismatch` (4 × BC817, J3 USB4145). Unchanged.
- **Netlist** (kicadxml): 232 components (227 + 5 TPs), 167 nets, no duplicate or unannotated reference, no single-pin net other than explicit `unconnected-` pins. `kicad-cli` prints "schematic has annotation errors" on export; no duplicate or missing reference is visible in the netlist.
- **DRC** (`--schematic-parity --all-track-errors`):
  - 0 errors and 0 unconnected pads.
  - 4 warnings: 3 silk lines clipped at the board edge, plus the U1 library footprint note.
  - The one parity item is `missing_footprint FL30`, the intended bridge.
- **V1 of 2026-11-18 fixed:**
  - Scan of all SMD pads against all 512 vias: only the U6 DPAK tab has a via inside it (37 mm², allowed by rule 9).
  - One more contact: a VS thermal via (0.8/0.4) has its annulus touching the corner of R60 pad 1. Same net, the drill edge is 0.1 mm outside the pad, and vias are tented on both sides (board setup), so solder cannot wick into it. No issue.
- **Fab package against the netlist:**
  - Every fitted part with an LCSC code is in the BOM with the same code, except J4/J5/J10/J11, which are hand-soldered by design.
  - No DNP part is in the BOM. CPL and BOM designators are identical (199 rows). H1–H4 and TP1–TP72 have no LCSC code, as intended.
- **BTT6050-1ERA pinout**, from Infineon datasheet Rev. 1.00 (2019-03-09), p. 4 Table 2 (PDF read): tab = VS, 3 = GND, 4 = IN, 5 = DEN, 6 = IS, 10–12 = OUT, 1/2/7/8/9/13/14 = NC. Matches the netlist for U11–U14 (pin 15 = VS).
- **BTT6050 absolute maximum** (p. 6 Table 3): VS −0.3…48 V, VS(LD) 65 V (RI 2 Ω), VIN/VDEN −0.3…6 V, IIN/IDEN ±2 mA, VIS −0.3…VS, IIS −25…50 mA. Against the circuit:
  - IN ≤ about 3.6 V (zener clamp, or a 3.3 V GPIO through BAT54C and 10 k).
  - DEN is driven through 10 k.
  - IS fault current 40 mA max is inside 50 mA.
- **IS scaling**, from p. 30 Table 9 (VS − VIS(RANGE) 1–3.5 V; kILIS 1500 ±8 % at 4 A; IIS(FAULT) 6/15/40 mA):
  - RIS 2 × 1 k = 500 Ω gives 1.33 V at 4 A.
  - The ESP32-S3 ADC1 at 11 dB is calibrated to 2.9 V (Espressif chip datasheet v2.2 Table 5-6, via the facts file). That puts full scale at about 8.7 A.
  - At the 40 mA fault, 20 V appears at IS. Through R104 10 k that is about 1.6 mA into the BAT54S clamp to +3V3, and only while DEN is high.
  - Firmware `pdm_config.h` uses kRisOhm 500 and kKilis 1500, which match.
- **RIS C844867:** JLCPCB/LCSC lists CRCW12061K00FKEAHP, Vishay, 1 kΩ 1 %, 750 mW. Vishay CRCW-HP e3 doc. 20043 (rev. 17-Mar-2026) p. 1 gives P70 0.75 W for 1206, valid with Rth ≤ 110 K/W (PDF read). 0.40 W per part at the 40 mA fault matches decision 238.
- **BAT54S C7420333 / BAT54C C22466350 pinout:** hongjiacheng BAT54–BAT54S datasheet Rev 2.0 p. 1 function diagram (rendered).
  - BAT54S: 1 = anode, 2 = cathode, 3 = common. In the netlist D102–D402 pin 1 is GND, pin 2 is +3V3, pin 3 is the IO, so the clamp works.
  - BAT54C: 1/2 = anodes, 3 = common cathode. D12–D15 match (IO and SWx on the anodes, SW_INx on the cathode).
- **Firmware pin map** (`firmware/src/pins.h`) against the netlist:
  - Matching nets: IO1 MOD_ID, IO2–5 IS, IO6/7/8/11 drive, IO9 NTC, IO10 VBAT, IO12 SW_SENSE, IO13 D7, IO14/15/16/21 switches, IO38–41 LEDs, IO33 DEN.
  - IO17 is TX and goes to U5 TXD (pin 3); IO18 is RX and goes to U5 RXD (pin 2).
  - VBAT divider 220 k/22 k gives ratio 11, as in the firmware.
- **Power-up output states:**
  - IO6/7/8/11 have 2.2 k pull-downs, so the channels start OFF.
  - DEN has no external pull, so the PROFET's internal pull-down holds it low.
  - The LED sink bases have 10 k pull-downs.
  - No drive pin is a strapping pin (S3 straps: IO0, IO3, IO45, IO46). IO3 is held low by the IS2 network (T-0051 note stands).
- **Buck LMR51610:** VFB 0.8 V (TI SLUSEY1B, via the facts file), so R9 68 k / R10 22 k give 3.27 V.
  - TI Table 8-1 (p. 17, PDF read) gives 10 µF typical COUT at 1.1 MHz / 3.3 V. On this board C3 (2.2 µF X7R) sits at L1 and C8 (22 µF) 68 mm away at the ESP32.
  - Ripple from C3 alone is about 17 mV. C8's track impedance is small at loop-crossover frequencies, and the load step sits at C8.
  - Not a finding. The E24 scope check of +3V3 in bring-up covers it.
- **Heat budget:** `python3 tools/heat_budget.py --ambient 40 --currents 4,4,4,4` gives 1.40 W per channel, 8.92 W total, Tj 101 °C. Unchanged. RDS(on) inputs were checked against p. 15 on 2026-11-18.
- **Invariants 1, 4 and 9 against the netlist:**
  - Invariant 1: the switch path SWx → BAT54C → 10 k → IN works without 3.3 V.
  - Invariant 4: every J3/J4/J5/J10 line has its clamp (D4–D6, D9/D10, D16–D19/D50–D54, D30). J11 is the documented PROFET exception.
  - Invariant 9: J5 carries no logic rail.
- **Test pads (decision 226):** TP1 GND, TP30 VS, TP70 CANH_BUS, TP71 CANL_BUS, TP72 GND_CAN sit on the nets and positions STATUS states. Bare pads, no new copper path.
- **Other bypass caps:** C13 is 2.8 mm from U6 IN; C11/C12 are 5.4/3.0 mm from U5 VCC2; C1/C19 are 5.2/2.8 mm from U3 VIN; C32 is 3.2 mm from U30 VCAP; the C101–C401 IS caps are 2.1 mm from their pins.

## Not checked

- The CPL rotations and origins from `CPL_FIX` (not re-derived independently; taken from the 2026-11-21 footprint report), and the Gerber zip contents.
- The hot-plug / negative-pulse power path with U30 (T-0129), beyond the clamp voltages against the Q30 60 V and BTT6050 48 V/65 V ratings, which are unchanged since earlier reviews.
- Part facts of parts unchanged since earlier validations (LM74502H, AGM601LL, CA-IS3050G pinout, L78M05, SMxJ TVS, PESD2CAN): taken from facts files and earlier reports.
- EMC beyond rule spot checks; pdm-hc2; firmware logic.

<!-- findings:begin -->
```json
[
  {
    "id": "V1",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-4ch",
    "location": "ESP32-PDM-4CH.kicad_pcb: C10 (can sheet, U5 VCC1 bypass) placed under U1, 33.6 mm from U5.1; nearest +3V3 cap to U5.1 is C8 at 31.9 mm",
    "summary": "CA-IS3050G VCC1 has no local 0.1 uF bypass (datasheet v1.10 p. 5 Table 6-1, p. 18: as close as possible); the isolator carrier current loops through ~34 mm of +3V3 track, risking CAN bit errors and radiated emission",
    "fix": "move C10 next to U5 pins 1/4 (logic side, GND via beside U5.4) and rerun the build, silk.py, emc_report and the fab package; no schematic or BOM change (optionally a second C307331 at U1 pin 3)",
    "door": "two-way",
    "reason": "layout-only move of an existing part on an unordered board; undone by git revert",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
