# Validation pdm-hc2 – re-check of the diff since 619a24338297 (T-0163), 2026-11-07

Scope: `git diff 619a24338297 -- hardware lib docs/design-notes.md`, i.e. T-0159 (BOM merge), T-0160 (LEDs, J6) and T-0161 (buck input filter position). Nothing else was re-reviewed.

## Findings

None (0 CRITICAL, 0 MAJOR, 0 MINOR).

## Checked and OK

- T-0161 net split (`sch_query net`): Net-(D2-K) = D2.1, JP1.1, L2.1 only. Net-(D3-K) = C1, C19, C22, D3.K, JP1.2, L2.2, U3 VIN/EN. D3 (USB) is on the buck side, so USB-only input is unchanged. No other load was left on the D2.K node.
- JP1 footprint, read from the installed KiCad library: `SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm` has an F.Cu bar 0.5 × 0.6 mm and `net_tie_pad_groups "1, 2"`. The netlist is therefore connected with L2 unfitted, and the DNP / not-in-BOM flags do not remove the copper.
- JP1 fusing: I redid Onderdonk at 40 °C, melting at 1083 °C, 0.6 mm wide. 1 oz gives about 35 A²s and 2 oz about 140 A²s, against the 9.6 A²s F1 trip bound (decision 81). The agent's 87 A²s at 2 oz is more conservative. Pass.
- L2/C22/R73 are DNP and use parts already on the BOM or in the report's facts (C96963, C170101, C17903). No unique fitted part was added. The "fit L2 only with C22/R73" rule is in STATUS.
- T-0160 pins: `sch_query ref U1` shows pin 17 IO13 → R59 → D7; pins 38, 39, 40 (IO42, TXD0, RXD0) → J6.7, J6.2, J6.3. IO41 is unrelated. IO13 and IO42 are not otherwise used on pdm-hc2 (the "Spare GPIO" note lists the free pins). J6 pins 4–6 are unconnected, so the FLT nets (IO35–IO37) are untouched.
- LED current: (3.3 − 1.85 V) / 2.2 k ≈ 0.66 mA, far below the 25 mA rating of C2286 (cached facts). D7 sits on an input-without-pull pin, so it is off at reset.
- J6 pin 8 (+3V3) and its pads are on-board only, with the layout rule in STATUS. A probe short resets the ESP32 only and cannot touch the switch path (invariant 1).
- T-0159: R9/R10 keep the values 68 k / 22 k (same tolerance and TCR) and the nets on U3 FB and +3V3 are unchanged. C2 sits between U3 SW and R43 (the boot capacitor) and is 100 nF 50 V. C12 on VCC2 is C15849 (1 µF, 50 V per JLC, X5R); about 0.7 µF at 5 V is more than the 0.1 µF needed. C13 stays on C28323 because of the 29 V DC-bias loss, which is correct.
- C103/C203 (BST) also use C15849. At about 12 V they keep about 0.24 µF worst case against the 162 nC requirement in design-notes (Eq. 4), margin about 1.5×, so this is not a finding.
- ERC (`sch_query erc`): 0 errors, 5 `lib_symbol_mismatch` warnings, the same as before.
- Growth: pdm-hc2 241 parts, 16 DNP, 65 unique per the fixers' `fix_check` runs. T-0159 gave −4 unique, T-0160 +1 (C2286), T-0161 +0. No change is larger than its item required. The CAN LEDs were rightly left out.

## Not checked

- Datasheet pages (L78M05, LMR51610, ESP32-S3-MINI-1) were not re-read; I relied on the cached facts files cited in the fix reports.
- Samsung DC-bias curves (simulated figures, not re-run).
- Middlebrook and surge-ring numbers for L2 (T-0161); the part is DNP and the decision 28 scan settles it.
- CPL rotation of D7/D8 and the C96963 land: already on the STATUS pre-order list.
- `heat_budget.py` was not rerun: no output rating or switch part changed.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
