# Owner inbox

Questions the agents may not decide themselves (decision 22, `docs/AUTONOMY.md`). Write your ruling on each
question's Answer line – `yes` (do the proposed fix), `no` (drop it) or your own ruling in words – or use `/inbox`.
The next `tools/orchestrate.py run` (or `inbox`) applies the answers. This file is regenerated from
`docs/queue.json`: only the Answer lines are read; other edits are lost.

## Open (13)

## Q-0001 · MAJOR · pdm-hc2 · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E2 (hc_channel: R104/R204 (RG 10 ohm), GATE/PU/PD); task T-0006
- **Summary:** MOSFET gate drive is not slew-limited (about 400-800 V/us estimated, PD direct), so switching clicks reach the VHF receiver and cable emissions rise; PROFET channels switch at 0.8 V/us.
- **Proposed:** RG_PU about 100-220 ohm plus an RGATE_PD footprint, tune on the bench, then recheck switching loss, SOA and the fast short-circuit response.
- **Why it needs you:** reviewer classed it big: Changes switching and protection timing of a safety-relevant output (bilge pump) and the heat budget.; touches safety

**Answer:** 

---

## Q-0002 · MAJOR · system · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E3 (root sheet: J10 battery input, D30, net VS); task T-0007
- **Summary:** Battery input has only an SMCJ30CA: no bulk or HF capacitance and no filter, so short-circuit turn-off spikes, switched-current steps and RF go straight onto the cable and the rails.
- **Proposed:** Add about 100 uF/50 V bulk plus 1-2.2 uF/100 V ceramic at J10 (more on HC2), 1 uF/100 V at each BTT6050 VS tab, and a ferrite/CMC footprint.
- **Why it needs you:** reviewer classed it big: Shared root sheet, new part type, cost about 0.2-0.3 USD per board.; affects both boards; touches shared-sheet, budget

**Answer:** 

---

## Q-0003 · MAJOR · pdm-hc2 · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E5 (hc_channel: OUT1/OUT2 at J11, D102/D202); task T-0009
- **Summary:** HC2 outputs have no surge/ESD clamp at the connector (invariant 4); the back-to-back MOSFETs also stop positive surges from reaching D30, so only the 80 V avalanche limits them.
- **Proposed:** Add SMAJ30CA (already on the BOM) from each OUT to GND at J11 with a short return to J10.2; check float-switch case at 28.8 V.
- **Why it needs you:** reviewer classed it big: New protection element on output lines (protection topology) of safety-relevant outputs.; touches protection, invariant, safety

**Answer:** 

---

## Q-0004 · MAJOR · system · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E6 (can: GND_CAN island, U5 ISO1044, D9, D10, J4); task T-0010
- **Summary:** No high-frequency return across the isolation barrier (CIO about 1 pF) and no CMC option, so the N2K cable can radiate logic-ground noise and ESD lifts the whole island; not measured.
- **Proposed:** Add a footprint for a 1-2.2 nF/1 kV Y-class capacitor GND_CAN-GND and a CMC footprint in series with CANH/CANL; confirm with a pre-compliance scan.
- **Why it needs you:** reviewer classed it big: Shared can sheet, protection and grounding topology change.; affects both boards; touches shared-sheet, protection

**Answer:** 

---

## Q-0005 · MAJOR · system · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E7 (power-usb: U3 LMR51610YDBVR, C1, C2, L1); task T-0011
- **Summary:** Buck is the 1.1 MHz PFM variant; PFM drops into the 150-350 kHz band at light load, the datasheet's separate 0.1 uF at VIN is missing, C1 is only 50 V, and SW ringing can land in the tightly limited 156-165 MHz band.
- **Proposed:** Add 100 nF/100 V at VIN, footprints for an SW RC snubber and a boot resistor, and consider the LMR51610YF (FPWM) if the scan shows PFM noise.
- **Why it needs you:** reviewer classed it big: Shared power-usb sheet; the FPWM option would be a different extended part.; affects both boards; touches shared-sheet, new-extended-part

**Answer:** 

---

## Q-0006 · MINOR · system · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E8 (analog_sw: R34-R37, C14-C17, R3-R8); task T-0012
- **Summary:** Hardware switch path has tau 0.32 ms (no real debounce), turns the output off below about 8 V at the switch (12 V cranking), and a lamp across the switch contacts above about 1.4 mA turns it on.
- **Proposed:** Raise C14-C17 to 470 nF-1 uF; document dry contacts and the cranking behaviour in the README.
- **Why it needs you:** reviewer classed it big: Shared analog_sw sheet and the invariant 1 signal path.; affects both boards; touches shared-sheet, invariant

**Answer:** 

---

## Q-0007 · MINOR · pdm-4ch · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E9 (channel: OUT1-OUT4 at J11, C102/C202/C302/C402); task T-0013
- **Summary:** 4-ch outputs rely on the PROFET (body diode to VS, clamp, 4 kV HBM) and D30 at J10; this meets the intent of invariant 4 but not its wording, and D30 is far from J11.
- **Proposed:** Document the output rule in invariant 4 and leave a DNP SMAJ30CA footprint per output; keep the VS copper to D30 wide.
- **Why it needs you:** reviewer classed it big: Touches an invariant and the protection scheme.; touches invariant, protection

**Answer:** 

---

## Q-0008 · MINOR · system · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E10 (power-usb: J3 shield, D4-D6 PESD0402V05); task T-0014
- **Summary:** USB shield is tied to battery negative (shore PE loop via a laptop) and the ESD diode is listed with a 40 V clamp against 3.6 V ESP32 pins (unverified).
- **Proposed:** README: service only, battery-powered laptop or USB isolator; check the TLP data of the DOWO part before ordering; consider an RC shield-to-GND.
- **Why it needs you:** reviewer classed it big: Shared power-usb sheet; a shield change is a design decision.; affects both boards; touches shared-sheet

**Answer:** 

---

## Q-0009 · MINOR · system · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E11 (analog_sw: C50-C53 (C1523); power-usb: C1); task T-0015
- **Summary:** 1 nF collector capacitors and the 2.2 uF buck input capacitor are probably 50 V parts against a 48.4 V TVS clamp; TI advises twice VIN for CIN.
- **Proposed:** Use 100 V (or 63 V) parts for C50-C53 and C1 if available as basic parts.
- **Why it needs you:** reviewer classed it big: Shared sheets (analog_sw, power-usb); part change needs the stock check.; affects both boards; touches shared-sheet

**Answer:** 

---

## Q-0010 · MINOR · system · finding

- **From:** `docs/reviews/2026-10-30-emc-system.md` E12 (root sheet: J10.2 (GND), D102/D202 return path on HC2); task T-0016
- **Summary:** Board ground reaches the battery negative through one terminal pole that carries TVS surge current and, on HC2, motor freewheel current (up to 25 A per channel); its rating is not defined.
- **Proposed:** Size the GND pole (or use two poles) in /system mechanical to match the VS input; wide GND copper to J10.2.
- **Why it needs you:** reviewer classed it big: Terminal and pole count decision.; affects both boards; touches connector, mechanical

**Answer:** 

---

## Q-0011 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-emc-system.md` E14 (F1, F3, F4 (1812L050/60GR)); task T-0018
- **Summary:** Is the interrupt rating (Imax at 60 V) of the 1812L050/60GR PTC enough for the prospective current of a direct battery short at J5.5 (F4 is fed from VS) or on NET-S? I could not read the datasheet.
- **Proposed:** Validator to check Imax and minimum resistance against 30 V / (cable + PTC resistance).
- **Why it needs you:** reviewer classed it big: Question for the owner or validator, not a design change.; a question only the owner can answer; affects both boards

**Answer:** 

---

## Q-0012 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-emc-system.md` E15 (can: J4 (4 poles, no shield pin), project goal); task T-0019
- **Summary:** Is IEC 60945 (marine) compliance a goal or only good practice, is a pre-compliance scan planned, and may the N2K shield stay unconnected at the node (4-pole J4)? This sets how far E3-E7 must go.
- **Proposed:** Owner ruling on the compliance target and the shield strategy.
- **Why it needs you:** reviewer classed it big: Only the owner can answer; shared sheet and connector.; a question only the owner can answer; affects both boards; touches shared-sheet, connector

**Answer:** 

---

## Q-0013 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-emc-system.md` L1 (power-usb: U3); task T-0020
- **Summary:** LMR51610YF (FPWM, same 1.1 MHz) would avoid PFM noise below 350 kHz; E7 asks for a scan first.
- **Proposed:** Swap only if the pre-compliance scan shows PFM noise; check price and stock.
- **Why it needs you:** reviewer classed it big: New extended part on a shared sheet.; affects both boards; touches shared-sheet, new-extended-part

**Answer:** 

---
