# pdm-hc2 status

Updated: 2026-11-03

**Where it stands:** schematic complete (scripted), ERC: 5 `lib_symbol_mismatch` notices only (since T-0066); netlist checked.
TPS48110A-Q1 + 2 × BSC030N08NS5 per channel, values in `docs/design-notes.md` §4a. No PCB. Decisions 1–6, 8–15, 17, 18
apply. Shared `analog_sw` sheet and controller pin map updated on 2026-10-30 (same as `pdm-4ch`): SW_SUPPLY on J5.5,
MMBT5551 LED sinks on IO38–IO41, VBAT_SENSE IO10, NTC TH1 on IO9.

**2026-11-03 (T-0071: T-0056/T-0005/T-0008, unattended, `hc_channel` ×2):** controller pin filtering, all from
parts already on the BOM. C107/C207 1 nF (C1523) DIODE–GND across Q13/Q23 (TI 9.6.1, mandatory). RVS R114/R214 100 Ω
(C25076) VS → new net `VS_CTRL` on U11/U12 pin 20; C102/C202 became the CVS: 1 µF/100 V 1206 (C13832) on `VS_CTRL`
(drop ≤ 70 mV; PWR_FLAG on `VS_CTRL`). CS X cap C108/C208 1 nF (τ 0.1 µs ≪ tSC 4 µs); Y caps C109/C110, C209/C210
100 pF/100 V **DNP** (unbalanced source impedance, fit only with ferrites at Q-0012); C111–C113/C211–C213 1 nF on
EN/UVLO, OV, IWRN (OV reacts in ≤ 0.4 ms; 10 nF rejected at 4 ms). ERC 0 errors, 5 warnings (unchanged); netlist
checked. Values and failure mode: design-notes §4a.1. **For the PCB:** C107/C207 at the MMBT3904, emitter
Kelvin-routed to U11/U12 GND pin 6; RVS/CVS at pin 20; C108/C208 across pins 17/18.

**2026-11-02 (T-0068, shared `analog_sw` – same as `pdm-4ch`):** C14–C17 → 470 nF (C47339, debounce τ ≈ 1.5 ms); new D55
DSK16 (C22466351, already on the BOM) after F4 in the SW_SUPPLY feed (panel-LED reverse protection, −0.3–0.7 V on the
switch supply). ERC 0 errors, 5 warnings (unchanged). The HC2 reverse-battery note in design-notes §8 is still open (P9).

**2026-11-01 (T-0064, decisions 26/27, unattended):** battery input J10 now has D30 + C30 (1 µF/100 V) on the
terminal net `VBAT_IN`, a DNP ferrite position FL30 bridged by the copper net tie JP30 to `VS`, and C31 100 µF/63 V
on VS (same controller part as 4-ch). HC2-only: C106/C206 100 µF/63 V on VS per channel (3 × 100 µF in total), and
D103/D203 SMAJ33CA (C19077549, preferred) from each OUT to GND at J11. ERC unchanged (6 `lib_symbol_mismatch`),
netlist checked. Details, part facts and the bilge-output failure mode: design-notes §8.1/§8.2.

**2026-11-02 (T-0065, decisions 30–32, unattended, shared sheets – same on both boards):** FB1/FB2 → GZ2012D601TF
(C1017, basic); D4–D6 → H5VL10B (C7420372, preferred, SOD-882); U6 TPS7B91 → L78M05ABDT (C58069, basic, DPAK) with C13
1 µF/50 V input capacitor; buck: C19 100 nF/100 V at VIN, R43 0 Ω boot resistor, R44/C20 SW snubber **DNP**; C1 →
2.2 µF/100 V 1206 (C170101); C50–C53 → 1 nF/2 kV 1206 (C9196, basic); J3 shield on the new net `USB_SHIELD` with R13
1 MΩ ‖ C18 4.7 nF/1 kV to GND, R14 0 Ω hard-tie **DNP**. README USB service rule added. ERC unchanged
(6 `lib_symbol_mismatch`), netlist checked. Details: design-notes §8.3.

**2026-11-02 (T-0066, Q-0037, unattended, shared `power-usb`, same on both boards):** U3 LMR51610 now uses
`Package_TO_SOT_SMD:SOT-23-6` (checked against TI DBV0006A and the JLCPCB footprint of C22427220, pin numbering
identical); custom `LMR51610.kicad_mod` removed from `lib/`. ERC 0 errors, warnings 6 → 5 (U3 mismatch cleared);
netlist: only U3's footprint changed. The PG-TDSO-14 paste fix in the same package affects only pdm-4ch. Details: design-notes §8.4.

**2026-11-02 (T-0070, unattended): gate slew control blocked (one-way, owner).** The BSC030N08NS5 SOA (Diagram 3,
30 V, single pulse, Tc 25 °C: ≈ 1.5 A at 1 ms, ≈ 0.4 A at 10 ms) and Zth (Diagram 4) do not allow the ruled
20 A ramp into 1000 µF: 600 W peak, 0.45 J in the input MOSFET over 1.5 ms, ΔTj ≈ 100 K above case (≈ 125 K with a
15 A load attached); even 100 µF at 20 A is above the 100 µs SOA line. No R1/C1 pair meets both targets, so R104/R204
stay 10 Ω PU→gate and no slew parts were added. The owner chooses: a maximum load capacitance, or a linear-mode
MOSFET / pre-charge path (decision 19). Numbers: `docs/reviews/2026-11-02-fix-pdm-hc2-T-0070.md`. T-0059 done: the
bootstrap delay (≈ 76–100 ms) and the 3.8 min retry are in design-notes §4a and the README.

**Rules until bench-measured:** no PWM on HC2 outputs (Q-0001). Prototype test: measure the real load input
capacitance and inrush of every intended HC2 load (Q-0045), and check whether an INP toggle cuts the 3.8 min
auto-retry short.

**2026-11-02 (T-0067, Q-0023/Q-0039/Q-0004, rulings Q-0012/Q-0031, unattended, shared `can`, same on both boards):**
U5 ISO1044 → **Chipanalog CA-IS3050G** (C528763, SOIC-8-WB `Package_SO:SOIC-8_7.5x5.85mm_P1.27mm`, new symbol
`ESP32-PDM:CA-IS3050G`; not pin-compatible, pins 5/6/7 = GND2/CANL/CANH). The datasheet check passed: supplies, ±58 V bus,
210 ns loop, 2–8 ms timeout, 5 kV_RMS; LEN 1 still holds at 49.3 mA worst case. −0.71 USD/board. R70 10 k TXD pull-up
to +3V3. DNP CMC FL1 (FACT4532-510-2P-T) in series with CANH/CANL, bridged by fitted 0 Ω R71/R72 (new nets
CANH/CANL_BUS and _XCVR). DNP Y-cap C70 1 nF/2 kV 1206 GND_CAN–GND (capacitor only). The bus side stays on NET-S (Q-0031);
J4 stays 4-pole with the shield open (Q-0012). ERC unchanged (5 `lib_symbol_mismatch`), netlist checked. Details: design-notes §8.5.

**Blocked (owner, one-way):** the PTC check failed. 1812L050/60GR is rated I_max 40 A, but a hard short behind F1/F3/F4
can draw ≈ 188 A (30 V / 0.16 Ω). F2 therefore stays SMD0805B050TF. Question in the T-0065 report.

**Waiting for the owner:** decision 19 **[proposed]** (21 A MOSFET option, halogen inrush), which depends on the
searchlight choice (decision 16, open). Decision 21 **[proposed]** (SW_SUPPLY sense on IO12).

## Next

0. Gate slew control (T-0054/T-0006, Q-0043/Q-0001): waiting for the owner's answer to the T-0070 SOA question;
   then set R104/R204 (R1), C1 + 10 Ω and a 0 Ω RGATE_PD footprint, recheck SOA, heat budget, short-circuit response.
1. Open in KiCad: tidy the label-wired `hc_channel` sheet and the parts the panel-cable script placed, *Update
   Symbols from Library* (keep Q3–Q6 on the BC817 symbol with value MMBT5551), ERC.
2. `/validate pdm-hc2 deep` (part facts of TPS48110A-Q1, BSC030N08NS5, the equations) and `/emc pdm-hc2`.
3. Verify the custom footprint `Texas_DGX0019A_VSSOP-19_3x5.1mm_P0.5mm` against the JLCPCB footprint (C17556513).
4. Searchlight: if it stays ~21 A, check NTMFS5C612NL (SO-8FL) against the TDSON-8-1 footprint and rerun the heat
   budget; if halogen, decide the short-circuit setting after a MOSFET SOA check.
5. PCB: Kelvin sense on the 1 mΩ shunt, MMBT3904 between the MOSFETs, TH1 next to the MOSFETs, ≥ 25 A output
   terminals, ≈ 50 A input.
   T-0064 rules (design-notes §8.1/§8.2):
   - **D103/D203 next to the J11 terminal, GND return a short, wide path straight to J10.2** (not via the logic
     ground); decision 27.
   - JP30 (VBAT_IN–VS) as a copper bridge as wide as the VS copper for ≈ 50 A (the placeholder footprint
     `NetTie-2_SMD_Pad2.0mm` is far too small); FL30 has no footprint yet, decided at pre-compliance.
   - D30, C30 at the J10 terminals; C31 near J10; C106/C206 at each channel's VS next to RSNS/Q11.
   - C30 (MLCC on the battery input) away from the terminal screws, board edges and bending lines.
   T-0065 layout rules (design-notes §8.3): C19 (100 nF) right at U3 VIN/GND; R44/C20 footprints tight at the SW
   node; R13/C18/R14 at J3 next to the shield tabs; U6 DPAK with copper under the tab (≈ 0.5 W); C1 1206 away from
   board edges and screws.
6. Cost lever: R1/R2 (2.2 k pull-downs on IO8/IO11, left over from the 4-ch drive) have no function here – remove
   in `/cost` or keep the controller part identical to `pdm-4ch`.

**PCB rule 9 – isolation barrier (EMC review 2026-10-30, updated T-0067):** no copper (pour, trace, via) under U5
between pins 1–4 and 5–8. Keep the GND and GND_CAN islands apart around the body by the package creepage (CA-IS3050G
SOIC-8-WB: 8 mm CLR/CPG), at least ≥ 4 mm. **C70 is the only part that crosses the gap**, on its own pads next to
U5. D9, D10, F3, FB2, D11, U6, FL1, R71/R72 sit on the GND_CAN side; U5 pins 1–4 and R70 on the GND side. FL1 and
R71/R72 go between D9 and U5 (D9 at J4).

## Pre-order checklist (T-0065)

- Recheck JLCPCB stock of the thin parts: TPS48110A (HC2), L1 SWPA6045S8R2MT (1231 on 2026-11-02), BTT6050 (4-ch),
  LMR51610YF (only if the scan asks for FPWM), plus the new C170101 and C107198.
- L1 approved alternates (datasheet-checked, same 8.2 µH / 0.056 Ω max / I_sat 3.9 A / I_rms 2.6 A / 6045 land):
  **Sunltech SLW6045S8R2MST C47018494** (no EasyEDA footprint at JLCPCB – map it to the SWPA land) and
  **cjiang FNR6045S8R2MT C168074**.
- H5VL10B has no published TLP curve (8/20 µs clamp only); accepted on that data (design-notes §8.3).
- Check the KiCad footprints `D_SOD-882`, `TO-252-2`, `L_0805_2012Metric` against the JLCPCB footprints of C7420372,
  C58069, C1017.
- Resolve the F1/F3/F4 PTC I_max question before ordering.
- T-0067: check the KiCad footprints `SOIC-8_7.5x5.85mm_P1.27mm` (U5) and `L_CommonModeChoke_Coilank_ACM4532`
  (FL1) against the JLCPCB footprints of C528763 and C20624726. The FL1 pad numbering must match windings 1→2 / 4→3
  before FL1 is ever fitted (design-notes §8.5).

## For /system

- T-0067: ARCHITECTURE `can` row says "ISO1044"; it is now CA-IS3050G (SOIC-8-WB, ≈ 7.5 × 11.5 mm with leads) plus
  DNP FL1/C70 and fitted R70–R72. LEN recheck: 49.3 mA worst case (LEN 1, 0.7 mA margin) / 79.8 mA continuous
  dominant (LEN 2). Measure the NET-S current on the first prototype.
- T-0065: ARCHITECTURE `can` row still says "TPS7B91"; it is now L78M05ABDT (DPAK, ≈ 10.4 × 6.7 mm footprint –
  include in the `/system mechanical` area budget). The NET-S current stays LEN 1 (normal traffic 44.8 mA) / LEN 2
  (continuous dominant 76.8 mA), only 5 mA margin to 50 mA. Recheck if the CAN transceiver changes (T-0030).
- T-0065: the PTC interrupt-rating problem (F1/F3/F4, I_max 40 A vs ≈ 188 A) is a system protection question for the
  owner; F4 feeds the panel switches (bilge forced run, navigation lights), so a competent person reviews it.
- T-0065 unique extended parts: −PESD0402V05, −TPS7B91; +C170101 (2.2 µF/100 V), +C107198 (4.7 nF/1 kV).

- **Bilge output fusing (T-0064 failure mode, needs README/installation rule):** D103/D203 sit outside the
  back-to-back MOSFETs. If a TVS fails short, a float-switch run feeds the short through the PDM output wire. The
  float circuit stays independent (invariant 8) only if the PDM leg has its own fuse, between J11 and the junction
  with the float circuit, that opens before the float fuse. Add this to the README next to the external breaker of
  decision 39; a competent person reviews the bilge wiring before installation.
- T-0064 added two unique extended parts (C487384, C13832); see pdm-4ch STATUS.

- Module width: probably 2 module widths because of the terminals; confirm with the enclosure.
