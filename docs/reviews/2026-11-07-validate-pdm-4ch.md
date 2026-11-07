# Validation re-check: pdm-4ch, changes since 619a243 (T-0162)

Date 2026-11-07, unattended. Scope: `git diff 619a24338297 -- hardware lib docs/design-notes.md` on pdm-4ch. Items T-0158 (J10 set, Q30), T-0159 (BOM merge), T-0160 (LEDs, J6), T-0161 (buck input filter position). `lib/` is unchanged. Untouched circuits and earlier findings are not repeated.

## Findings

### MAJOR (ordering, not design) – M1: J10 socket C577772 has no stock
- Location: root sheet, J10 (KF2EDGSRM-7.62-2P C577772).
- Evidence: `jlc_get_part` today: stock 0, min order 18, extended. The T-0158 report says the same. The plug C577752 is in stock (63 per the report). The socket is the only battery input of the board, so the board cannot be assembled or hand-fitted as designed until it is back.
- Fix: re-check stock at order time. If it is still 0, take the socket from another seller (it is hand-soldered, decision 85) or a part with the same drawing. This is a stock matter and no design change.

No CRITICAL findings. No other MAJOR or MINOR findings with a concrete failure mechanism.

## Checked and OK

- **Q30 AGM601LL (C5464765), pins:** facts file (AGM601LL VER2.65 p. 1: pin 1 G, 2–8 S, tab D). Symbol pad 1 G, 2 S, 3 D (tab). The KiCad `Infineon_PG-HSOF-8-1` footprint has pad 1 at the gate position, pad 2 over the source leads, pad 3 as the tab, so the mapping matches. Netlist: G to U30.6, S to VBAT_FL, D to VS. The instance LCSC field is C5464765. The embedded lib symbol still carries the IPT007N06N fields (C122552); the instance overrides them, so this is cosmetic.
- **Q30 ratings:** VDS 60 V, VGS ±20 V (VCAP ≤ 13.9 V), RDS(on) max 1.6 mΩ at 10 V, Vth 2.2 V max (facts p. 1–2). D31 clamp 59.4 V is the same margin as the part before it, accepted in decision 96. By hand: 16 A² × about 2.2 mΩ hot ≈ 0.55 W, 40 + 0.55 × (40…62) = 62…74 °C, below the stated 66–80 °C, so the stated range is conservative.
- **Heat:** `tools/heat_budget.py` 4 × BTT6050 table unchanged (4 A: Tj 101 °C, 4.5 A marginal). Q30's extra 0.55 W raises the enclosure air by about 0.3 K at R_box 0.6 K/W.
- **J10 C577772:** pad 1 = VBAT_IN, pad 2 = GND, same on both rows; footprint `Kefa_KF2EDGSRM-7.62-2P` is unchanged in `lib/` (rows 7.62 mm, drill 1.5 mm, flange holes 22.86 mm apart). The listing says 32 A, 400 V, −40…105 °C. 16 A on a 30 A UL part is about 53 %. Facts: `docs/part-facts/C577772.md`.
- **T-0159 swaps:** R9 68 k (C36871) and R10 22 k (C25768) keep the values and nets of the 3.3 V divider; both ±1 %, 100 ppm/°C. C2 100 nF X7R 50 V (C307331) and C12 1 µF X5R 50 V (C15849, on VCC2 5 V, 0.1 µF is needed) are correct. C13 stays C28323 because C15849 loses 90 % at 29 V and would miss 0.33 µF at the L78M05 input; the check is sound. Old codes C14663, C52923, C31850, C23231 are gone from the schematic (grep).
- **T-0160 LEDs:** D7: U1.17 (IO13) – R59 2.2 k – D7 – GND. D8: +3V3 – R67 2.2 k – D8 – GND. About 0.7 mA each (Vf ≈ 1.85 V), far below the 25 mA rating. IO13 is a plain input with no pull at reset, so D7 is off during start-up. The 0.7 mA D8 draw is small next to the controller budget in ARCHITECTURE line 90 and is recorded there.
- **T-0160 J6 (DNP, not in BOM):** 1 GND, 2 TXD0 (U1.39), 3 RXD0 (U1.40), 4–6 IO35–37 (U1.31–33), 7 IO42 (U1.38), 8 +3V3. The pin numbers are those of the existing U1 symbol; IO35–37 and IO42 were no-connects before, and no other net uses them. IO34, IO45 and IO46 stay open. The ARCHITECTURE pin-map rows match the netlist.
- **T-0161 filter position:** D2.K → JP1 ‖ L2 → Net-(D3-K) with C1, C19, C22, D3.K, U3.4/5 (VIN, EN). D3 is on the buck side, so the USB-only path is unchanged. JP1 is a copper bridge (`SolderJumper-2_P1.3mm_Bridged_Pad1.0x1.5mm`, 0.5 × 0.6 mm bar, current across the 0.6 mm width); DNP, not in BOM. Onderdonk melt: 0.0207 × A², so 35 A²s at 1 oz (41 cmil) against the 9.6 A²s bound. The 2 oz figure of 87 A²s uses 65 cmil, where 70 µm would give about 140, so it is conservative. L2 (C96963), C22 (C170101) and R73 (C17903) are DNP, so the fitted circuit changes only by the bridge. The surge ring-up risk with L2 fitted is documented in the fix report and the scan.
- **ERC (pdm-4ch):** 0 errors, 5 warnings (lib_symbol_mismatch on Q3–Q6 BC817 and J3), as before.
- **Docs:** README line 68 (16 A), ARCHITECTURE pin-map and power rows, STATUS entries agree with the schematic. Stale: ARCHITECTURE line 73 still lists the old J10 (C6394053) and line 89 the old Q30 figures; STATUS "For /system" already lists these for the sync sweep, so they are not findings.

## Not checked

- Rendering of the C577772 drawing and the J10 footprint (checked by T-0158; `lib/` is unchanged and I did not repeat it).
- AGM601LL breakdown voltage at cold and its hot avalanche rating (not in the datasheet; the fixer lists this as a gap).
- C96963 land against the JLCPCB/EasyEDA footprint (only matters if L2 is fitted).
- pdm-hc2 (outside this scope).
- The PDFs themselves; I relied on the facts files for AGM601LL and the Kefa socket.

<!-- findings:begin -->
```json
[
  {
    "id": "V1",
    "kind": "finding",
    "severity": "MAJOR",
    "board": "pdm-4ch",
    "location": "root sheet: J10 KF2EDGSRM-7.62-2P C577772",
    "summary": "J10 socket C577772 is out of stock at JLCPCB (stock 0, min order 18), so the battery input cannot be assembled as designed until restocked.",
    "fix": "Re-check stock at order time; if still 0, buy the socket elsewhere (hand-soldered, decision 85) or use a part with the same drawing.",
    "door": "two-way",
    "reason": "stock check and sourcing, no design change and no money committed yet",
    "touches": [],
    "cost_delta_usd": 0.0
  }
]
```
<!-- findings:end -->
