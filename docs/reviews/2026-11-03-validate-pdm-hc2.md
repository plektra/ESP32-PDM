# Validator re-check – pdm-hc2, 2026-11-03 (T-0075, unattended)

Scope: changes since commit 5cee70e79c0e (T-0064/65/66/67/68/71/73 on pdm-hc2). Question per change: correct, complete,
no bigger than needed. Earlier reports were not repeated.

## Findings

None (0 CRITICAL, 0 MAJOR, 0 MINOR). Nothing found with a concrete failure mechanism.

Open items already owned elsewhere, not re-raised: T-0070 gate-slew SOA question (owner), F1/F3/F4 PTC I_max (owner),
HC2 reverse-battery text (P9).

## Checked and OK

- ERC (`sch_query pdm-hc2 erc`): 0 errors, 5 warnings (BC817 ×4, USB4145), matches STATUS.
- T-0071 `hc_channel` netlist (U11): pin 20 VS on `VS_CTRL` via R114 (100 Ω) from VS, CVS C102 1 µF/100 V on VS_CTRL; RSET R102, R105 divider
  and R101 stay on VS, as required because the CS+ sense current is referenced to the shunt's high side (Eq. 6, `docs/part-facts/C17556513.md`,
  TPS4811-Q1 SLUSEE5E). Drop 100 Ω × 0.7 mA = 70 mV, far above VS POR. Same on U12.
- C107 1 nF DIODE–GND across Q13 (TI 9.6.1, mandatory): present; Q13 B/C tied on DIODE, emitter GND.
- C108 1 nF CS+–CS−: τ 0.1 µs vs tSC 4 µs (p. 10); CS+–CS− abs max ±0.3 V unaffected. C109/C110 DNP (unbalanced source impedance) – reasoning sound.
- C111/C112/C113 1 nF: Thevenin at EN 91 kΩ (τ 91 µs), OV node 38 kΩ (τ 38 µs), IWRN 47 µs – consistent with the stated ≤ 0.4 ms OV delay.
- C13832 (1 µF/100 V X7R 1206, extended, stock 331k, `jlc_get_part`) matches value/package; already a BOM part (C30), no new unique part.
- D103/D203 SMAJ33CA (C19077549): VRWM 33 V, VBR 36.7–40.6 V, VC 53.3 V @ 7.5 A (datasheet rev 2.2 p. 3); below the 80 V MOSFET rating, above 30 V continuous. Nets OUTn–GND correct.
- U5 CA-IS3050G (C528763, v1.10 p. 5–7, 19): schematic pins 1 VCC1/+3V3, 2 TXD/IO17, 3 RXD/IO18, 4 GND1, 5 GND2, 6 CANL, 7 CANH, 8 VCC2 match; VCC2 5 V (abs max 6 V), bus ±58 V. R70 TXD pull-up to 3V3; FL1 DNP bridged by R71/R72, nets consistent. Footprint = KiCad stock `SOIC-8_7.5x5.85mm_P1.27mm`, pad row 10.65 mm vs datasheet land 10.90 mm, pad length 1.8 mm – lead foot still covered.
- U6 L78M05ABDT (C58069, DS0425 rev 24 p. 3, 5, 8): DPAK top-view figure gives tab left, OUTPUT upper, INPUT lower → pin 1 IN, 3 OUT, 2/tab GND as in the symbol and TO-252-2 footprint; VI abs max 35 V vs D10 SMAJ18CA clamp ≤ 29.2 V; input cap C13 1 µF/50 V ≥ 0.33 µF; dropout 2 V OK on 9 V bus after D11.
- U3 LMR51610YDBVR (C22427220, SLUSEY1B p. 3–4): SOT-23-6 pins 1 CB, 2 GND, 3 FB, 4 EN, 5 VIN, 6 SW match the netlist; VIN 70 V abs max; C1 2.2 µF/100 V, C19 100 nF, R43 0 Ω boot (datasheet has none; 0 Ω neutral).
- D55 DSK16 in the SW_SUPPLY feed (C22466351 facts): VRRM 60 V, IF 1 A ≥ F4 trip; anode F4.2, cathode SW_SUPPLY/J5.5/D54/C54 – correct polarity.
- C14–C17 470 nF (C47339), D12/D13 BAT54C (C22466350, pins 1/2 anodes, 3 common cathode – wired as OR into SW_IN1/2 correctly, Vr 30 V vs ≤ 3.3 V node).
- T-0073 LCSC codes spot-checked by `jlc_get_part`: C45783 22 µF/25 V 0805 (3V3), C52923 1 µF/25 V 0402 (5 V), C307331 100 nF/50 V 0402, C28323 1 µF/50 V 0805, C13832 – all fit value, package and net voltage.
- Heat budget not rerun: no output rating or switch part changed on HC2 since the base.

## Not checked

- Package drawings of D_SOD-882, TO-252-2, L_0805 and the Coilank CMC pad numbering against JLCPCB footprints (STATUS pre-order list).
- Remaining T-0073 codes (resistors, C2/C4/C5/C7/C9/C14663 etc.) beyond the spot check.
- Pre-existing R103/C101 ISCP filter (4.7 kΩ × 1 nF ≈ 4.7 µs vs tSC 4 µs) was not part of the diff; not reviewed here.
- 0402 R114 pulse rating (UNVERIFIED in the fix report, bulk C106/C31 and TVS limit the step).
- L78M05 junction temperature at worst-case ICC2 73 mA / 16 V (≈ 0.8 W × 100 °C/W) not computed against real copper area.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
