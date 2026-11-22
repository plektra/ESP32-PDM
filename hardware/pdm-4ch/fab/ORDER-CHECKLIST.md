# pdm-4ch first order – checklist

Follow top to bottom while quoting and ordering on jlcpcb.com. Basis: decisions 99–103 (5 PCBs, 2 assembled, 2 oz,
Standard PCBA, 16 A only), 122 (all SMT on top), 85 and 127 (connectors hand-soldered, bought with the order), 150
(4 layers). Settings and price detail: `README.md`; what the package contains: `package-report.md`.

Write the result of each step in the record at the end, then copy it into `../STATUS.md`.

## 1 Before uploading

- [ ] `git pull` on `main`, then `python3 tools/jlc_package.py pdm-4ch`. The first line must read
      **DRC gate: 0 errors, … 0 unconnected, 0 parity issues – pass**. Upload only files from this run.
- [ ] Files at hand: `ESP32-PDM-4CH-gerbers.zip`, `ESP32-PDM-4CH-bom-jlc.csv`, `ESP32-PDM-4CH-cpl-jlc.csv`;
      keep `package-report.md` and `ESP32-PDM-4CH-assembly.pdf` open beside the browser.

## 2 PCB step (Add Gerber file)

- [ ] JLCPCB reads the zip as **4 layers, 100 × 75 mm**. If not, stop: wrong zip.
- [ ] Quantity **5**.
- [ ] Thickness **1.6 mm**.
- [ ] Outer copper **2 oz**; inner copper: JLCPCB's default for 4 layers with 2 oz outer.
- [ ] Surface finish **HASL lead-free**.
- [ ] Via covering: leave the default (tented). Smallest drill 0.3 mm, 507 vias – standard capability.
- [ ] Everything else (colour, order number, etc.): leave the default.
- [ ] Gerber viewer: silkscreen top shows OUT1–OUT4, BATTERY + / −, PANEL, CAN; bottom shows the pin legends and
      "ESP32-PDM pdm-4ch", "rev A 2026-11  CERN-OHL-S v2", "github.com/plektra/ESP32-PDM".

## 3 Assembly options

- [ ] PCB Assembly **on**, **Standard** (Economic is not offered with 2 oz, decision 99).
- [ ] Assemble **top side** only (decision 122).
- [ ] PCBA quantity **2**.
- [ ] Tooling holes: "Added by JLCPCB" (the board has none of its own).
- [ ] **Confirm parts placement: yes** (0.45 USD; included in the README price check).

## 4 BOM and CPL upload

- [ ] Upload the BOM and the CPL. Expect **54 BOM lines, 199 placed parts**, all matched to our LCSC numbers.
- [ ] SW_BOOT1/SW_RESET1 may show "Unconfirmed" (value `SW_Push`): confirm **C318884 TS-1187A-B-A-B**.
- [ ] No line shows a shortfall or "out of stock". The thinnest parts on 2026-11-21: L1 C96963 (1173), BTT6050
      C534868 (1604, 8 needed), Q30 C5464765 (1650), U30 C5219203 (1993). If one is short, stop and note it; do
      not accept a substitute JLCPCB suggests.
- [ ] Parts left out on purpose (not in the BOM, do not add): every DNP position, FL1, FL30, H1–H4, J6, JP1, JP30,
      TP1/TP30/TP70–TP72 and the connectors J4, J5, J10, J11 (list in `package-report.md`).

## 5 Placement preview

The CPL is already corrected against JLCPCB's footprints (`CPL_FIX`, 24 parts). Each part should sit square on its
pads with pin 1 / polarity as on the assembly drawing. **Do not rotate the corrected parts again.** Check these:

- [ ] U30, U5, U3, U11–U14: pin-1 dot at the pin-1 mark of `ESP32-PDM-4CH-assembly.pdf`.
- [ ] Q30: the eight leads on the leads' pad row, the large tab on the large drain pad.
- [ ] Q3–Q6, D9, D12–D15, D102–D402 (SOT-23): the single pin on the single pad.
- [ ] U1: module outline over the pads, antenna end at the board edge.
- [ ] J3: USB-C opening at the board edge; U6: tab on the large pad.
- [ ] D7/D8 (red LEDs): anode on the pad joined to R59 / R67, cathode on the GND pad (KiCad pad 1).
- [ ] Spot-check two diodes with a band: D20 (cathode on the SW1 side) and D101 (cathode on the GND side).
- [ ] If anything is off: correct it in the preview, write the part and the angle in the record, and afterwards
      fix `CPL_FIX` in `tools/jlc_package.py` (and re-run `tools/fp_check`) so the next order is right.

## 6 Quote

- [ ] Fixture fee line: **is the 16.42 USD Standard PCBA fixture fee shown? yes / no**.
- [ ] Compare with the README price check: about **205 USD** JLCPCB order (parts ≈ 38, feeder loading 54 × 1.53 ≈ 83,
      setup + stencil + placement ≈ 34, joints ≈ 2, PCB ≈ 49), plus 16.42 if the fixture fee applies; shipping, VAT
      and duty extra. More than about 15 % above that: look for the line that changed before paying.
- [ ] Check the coupon centre for a PCBA coupon (decision 85).

## 7 Connectors (LCSC, same cart or separate order)

Hand-soldered by the owner on the two assembled boards (decisions 85, 121, 127). Stock on 2026-11-22: all over 6000.
Buy at least one set per assembled board; LCSC minimums may round up.

| Ref | Socket (board) | Plug | Per board |
|---|---|---|---|
| J10 battery | Kefa KF135T-10.16-2P **C475108** (screw terminal, no plug) | – | 1 |
| J11 outputs | Kefa KF2EDGRC-5.08-4P **C441238** | KF2EDGK-5.08-4P-AA **C440882** | 1 + 1 |
| J5 panel | Kangnex WJ15EDGRC-3.81-10P **C26895** | WJ15EDGK-3.81-10P **C26865** | 1 + 1 |
| J4 CAN | Kangnex WJ15EDGRC-3.81-04P **C7245** | WJ15EDGK-3.81-04P **C7244** | 1 + 1 |

- [ ] Recheck stock in the cart.
- [ ] Lead-free solder wire for these joints (RoHS note in `../STATUS.md`); J10 needs a powerful iron.

## 8 After ordering

- [ ] Fill in the record below and copy it into `../STATUS.md` (new dated entry at the top).
- [ ] Bring-up plan for the boards when they arrive: `../bring-up.md`. Connector checks of decision 98 happen then
      (decision 127).

## Record

| Item | Value |
|---|---|
| Date ordered | |
| JLCPCB order number | |
| JLCPCB total (USD, before shipping/VAT) | |
| Fixture fee charged (yes/no) | |
| Shipping, VAT, duty | |
| LCSC connector order / total | |
| Parts corrected in the placement preview (ref, angle) | none expected |
| Notes (stock, substitutions declined, anything JLCPCB asked) | |
