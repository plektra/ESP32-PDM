# Owner inbox

Questions the agents may not decide themselves (decision 22, `docs/AUTONOMY.md`). Write your ruling on each
question's Answer line – `yes` (do the proposed fix), `no` (drop it) or your own ruling in words – or use `/inbox`.
The next `tools/orchestrate.py run` (or `inbox`) applies the answers. This file is regenerated from
`docs/queue.json`: only the Answer lines are read; other edits are lost.

## Open (32)

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

## Q-0014 · MINOR · system · finding

- **From:** `docs/reviews/2026-10-30-cost-system.md` C1 (root, power-usb, can, analog_sw: C2,C4-C13,D12-D15,FB1,FB2,R1,R2,R5,R6,R11,R12,R15-R17,R21,R24,R27,J5,J10,J11); task T-0021
- **Summary:** 22 BOM lines have no LCSC field, so JLCPCB cannot place them as drawn
- **Proposed:** Add the basic/preferred codes listed in rule finding C1 (C14663, C15849, C19666, C28233, C45783, C307331, C52923, C22466350, C25879, C25905, C25744); J5/J10/J11 in /system mechanical
- **Why it needs you:** reviewer classed it big: Missing LCSC field is a small change in kind, but it touches shared sheets and board=system; affects both boards; touches shared-sheet

**Answer:** 

---

## Q-0015 · INFO · system · finding

- **From:** `docs/reviews/2026-10-30-cost-system.md` C4 (U3/L1 (power-usb), U11/U12 (pdm-hc2 hc_channel), BTT6050); task T-0022
- **Summary:** Nothing is below 500 in stock, but TPS48110A (999), L1 SWPA6045S8R2MT (1231) and BTT6050 (1748) are thin and single-source; the EMC option LMR51610YF has only 458
- **Proposed:** Re-check stock before ordering; note L1 second sources SLW6045S8R2MST C47018494 / FNR6045S8R2MT C168074 after a datasheet check
- **Why it needs you:** reviewer classed it big: board=system, affects shared sheet power-usb; affects both boards; touches shared-sheet

**Answer:** 

---

## Q-0016 · INFO · system · finding

- **From:** `docs/reviews/2026-10-30-cost-system.md` C5 (BOM, package variants of 100 nF / 1 uF); task T-0023
- **Summary:** 52/59 unique parts cost 1.53 $ each only under Standard PCBA; merging package variants would save ~9 $ per order then
- **Proposed:** Only if Q1 forces Standard PCBA: merge 100 nF and 1 uF package variants
- **Why it needs you:** reviewer classed it big: board=system, shared sheets; affects both boards; touches shared-sheet

**Answer:** 

---

## Q-0017 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L1 (ordering); task T-0024
- **Summary:** Order 30 instead of 10 per run: -6.05 $/board (4-ch), -7.00 $/board (HC2); 10 instead of 5 saves -9.0/-9.8 $
- **Proposed:** Owner sets the order quantity per board from Vega's needs
- **Why it needs you:** reviewer classed it big: Cost lever needing an owner decision on quantity and cash; board=system; affects both boards; cost change -6.05 USD per board

**Answer:** 

---

## Q-0018 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L2 (PCB/PCBA ordering, panel); task T-0025
- **Summary:** One panel holding pdm-4ch + pdm-hc2 saves one setup, stencil, THT fee and 15 shared extended fees: -59.79 $/order (-2.99 $/board at 10+10)
- **Proposed:** Panelise both designs as one PCBA design at the PCB phase, after checking the JLCPCB multi-design surcharge
- **Why it needs you:** reviewer classed it big: Trades flexibility (fixed 1:1 ratio), mechanical/panel choice, board=system; affects both boards; touches mechanical; cost change -2.99 USD per board

**Answer:** 

---

## Q-0019 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L3 (power-usb FB1, F2, D4-D6; can FB2, U6); task T-0026
- **Summary:** Four basic/preferred swaps remove 4 extended fees: FB->GZ2012D601TF C1017, F2->1812L050/60GR, PESD0402V05->H5VL10B C7420372, TPS7B91->L78M05ABDT C58069
- **Proposed:** Adopt after part-facts checks (USB FS capacitance of H5VL10B, L78M05 at 29 V clamp, DPAK area)
- **Why it needs you:** reviewer classed it big: Touches shared sheets and changes footprints; protection parts swapped; affects both boards; touches shared-sheet, protection; cost change -1.20 USD per board

**Answer:** 

---

## Q-0020 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L4 (power-usb J3, D4-D6, F2, FB1, D3, R11, R12, C4, C5); task T-0027
- **Summary:** USB-C as DNP or pogo pads removes 3 extended fees and ~0.27 $ parts: -1.30 $/board at 10 (overlaps L3)
- **Proposed:** Owner decides whether a fitted USB-C service port is needed
- **Why it needs you:** reviewer classed it big: Connector change on a shared sheet; trades a convenience feature; affects both boards; touches shared-sheet, connector; cost change -1.30 USD per board

**Answer:** 

---

## Q-0021 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L5 (J4, J5 (and J10/J11 when chosen)); task T-0028
- **Summary:** Fixed screw terminals instead of pluggable header + plug: about -1.0 $/board (the plug halves alone cost 1.20 $)
- **Proposed:** Decide in /system mechanical
- **Why it needs you:** reviewer classed it big: Connector and mechanical choice; affects both boards; touches connector, mechanical; cost change -1.00 USD per board

**Answer:** 

---

## Q-0022 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L6 (power-usb U3 LMR51610YDBVR, L1); task T-0029
- **Summary:** LMR51610XDBVR (400 kHz, C20539658, 0.52 $) instead of the Y variant (1.35 $): -0.83 $/board; needs a re-designed L/C and conflicts with EMC lever L1
- **Proposed:** Evaluate with the datasheet and the EMC reviewer before adopting
- **Why it needs you:** reviewer classed it big: Shared sheet, changes the switching frequency (EMC); affects both boards; touches shared-sheet; cost change -0.83 USD per board

**Answer:** 

---

## Q-0023 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L7 (can U5 ISO1044BDR); task T-0030
- **Summary:** CA-IS3050G (C528763, 5 kV RMS, 0.92 $ at 10+) instead of ISO1044 (1.62 $): -0.71 $/board, second source; different package/pinout
- **Proposed:** part-facts check of the CA-IS3050G datasheet (supplies, pinout, timing), then footprint change
- **Why it needs you:** reviewer classed it big: Shared sheet, NMEA 2000 isolation part replaced; affects both boards; touches shared-sheet, protection, new-extended-part; cost change -0.71 USD per board

**Answer:** 

---

## Q-0024 · INFO · system · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L8 (root TH1 (NTC, IO9)); task T-0031
- **Summary:** No basic NTC exists; an MMBT3904 diode sensor (preferred) would remove one extended fee: -0.32 $/board at 10, at the cost of accuracy and calibration
- **Proposed:** Owner decides whether NTC accuracy is worth 3.07 $ per order
- **Why it needs you:** reviewer classed it big: Changes confirmed decision 18 (named NTC part) and firmware; affects both boards; touches decision:18, shared-sheet, firmware

**Answer:** 

---

## Q-0025 · INFO · pdm-hc2 · lever

- **From:** `docs/reviews/2026-10-30-cost-system.md` L10 (root R1/R2 (IO8/IO11 pull-downs)); task T-0033
- **Summary:** Removing R1/R2 on HC2 saves only ~0.01 $/board; recommendation is to keep the controller part identical
- **Proposed:** Keep as is
- **Why it needs you:** reviewer classed it big: Controller part of the root sheet is shared; touches shared-sheet

**Answer:** 

---

## Q-0026 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-cost-system.md` Q1 (PCB fabrication / PCBA mode); task T-0034
- **Summary:** Does JLCPCB accept 2 oz copper with Economic PCBA? If not, Standard PCBA adds +5.1 $ (4-ch) / +5.6 $ (HC2) per board at 10
- **Proposed:** Owner checks the JLCPCB quote page with 2 oz + Economic PCBA before layout
- **Why it needs you:** reviewer classed it big: Question; affects the budget; a question only the owner can answer; affects both boards; touches budget

**Answer:** 

---

## Q-0027 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-cost-system.md` Q2 (ordering); task T-0035
- **Summary:** How many pdm-4ch and pdm-hc2 boards per order (5, 10, 30)? This is the largest cost lever
- **Proposed:** Owner states the quantities for Vega and spares
- **Why it needs you:** reviewer classed it big: Question; a question only the owner can answer; affects both boards

**Answer:** 

---

## Q-0028 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-cost-system.md` Q3 (panel); task T-0036
- **Summary:** Is a combined 1:1 panel of pdm-4ch + pdm-hc2 acceptable (L2)?
- **Proposed:** Owner decides
- **Why it needs you:** reviewer classed it big: Question; a question only the owner can answer; affects both boards; touches mechanical

**Answer:** 

---

## Q-0029 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-cost-system.md` Q4 (power-usb J3); task T-0037
- **Summary:** Is a fitted USB-C service connector required, or are pads/DNP plus OTA enough (L4)?
- **Proposed:** Owner decides
- **Why it needs you:** reviewer classed it big: Question; a question only the owner can answer; affects both boards; touches connector, shared-sheet

**Answer:** 

---

## Q-0030 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-cost-system.md` Q5 (J4, J5, J10, J11); task T-0038
- **Summary:** Pluggable or fixed screw terminals (L5)?
- **Proposed:** Settle in /system mechanical
- **Why it needs you:** reviewer classed it big: Question; a question only the owner can answer; affects both boards; touches connector, mechanical

**Answer:** 

---

## Q-0031 · INFO · system · question

- **From:** `docs/reviews/2026-10-30-cost-system.md` Q6 (can sheet, NET-S supply); task T-0039
- **Summary:** Must the isolated CAN side stay powered from NET-S? If not, an isolated CAN part with integrated isolated supply could also remove the TPS7B91/FB2/D11 chain
- **Proposed:** Owner/architect confirms the NMEA 2000 powering requirement
- **Why it needs you:** reviewer classed it big: Question; touches NMEA isolation and a shared sheet; a question only the owner can answer; affects both boards; touches shared-sheet, protection

**Answer:** 

---

## Q-0032 · INFO · pdm-4ch · question

- **From:** `docs/reviews/2026-10-30-cost-system.md` Q7 (U11-U14 population); task T-0040
- **Summary:** Standard population for Vega's pdm-4ch: all BTT6050 (24.87 $) or a 2+2 mix with BTT6010 (28.58 $ at 10)?
- **Proposed:** Owner decides from the load list
- **Why it needs you:** reviewer classed it big: Question; a question only the owner can answer; touches decision:7

**Answer:** 

---
