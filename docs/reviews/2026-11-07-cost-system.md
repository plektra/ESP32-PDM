# Cost re-check, system – changes since 619a24338297 (2026-11-07, T-0164)

Scope: price only the changes of T-0158 (J10, Q30), T-0159 (BOM merges), T-0160 (LEDs, J6) and T-0161 (L2/JP1/C22/R73). BOM
exported with `kicad-cli sch export bom` from the old and the new schematics. Prices from `jlc_get_part` /
`jlc_stock_check`, 2026-11-07 (stock live; price is the LCSC 1-piece or tier price). Earlier reports not repeated.

## Figures

Unique **extended** parts per board (each costs the loading fee per order, 3.07 $ – fee not re-checked today):

| Board | Before | After | Why |
|---|---|---|---|
| pdm-4ch | same | same | Q30 C122552 → C5464765 (extended → extended); J10 C6394053 → C577772 (extended → extended). L2 = C96963 and C22 = C170101, codes already on the BOM |
| pdm-hc2 | same | same | L2, C22 reuse existing codes; no other extended line changed |

System-wide the unique extended count is **one lower**: C577772 (7.62 mm) was already pdm-hc2's J11, and now also 4ch's J10. Whether JLCPCB would
charge it twice depends on whether each board is its own order (they are separate designs, so yes, per order).
Basic/preferred lines: new D7/D8 KT-0603R C2286 (basic, no fee). T-0159 removed 4 lines per board (C14663, C52923, C23231, C31850; all basic) and
moved R9 to C36871 (preferred, no fee). BOM lines: 4ch 71 → 69, hc2 76 → 73. All new parts are basic/preferred or existing extended codes.

Change in cost per board, 1 part set per board (4ch; hc2 only the small items):

| Item | Old → new | at 5 (1+ tier) | at 10 | at 30 |
|---|---|---|---|---|
| Q30 IPT007N06N 3.54/3.05/2.75 $ → AGM601LL 0.85/0.77/0.73 $ | 4ch | -2.69 | -2.29 | -2.02 |
| J10 socket C6394053 1.54/1.27/1.13 → C577772 0.65/0.52/0.52 (10+ tier) | 4ch, hand-soldered | -0.89 | -0.75 | -0.60 |
| J10 plug C6394029 2.45/2.08/1.84 → C577752 1.18/0.98/0.87 | 4ch, owner buys | -1.27 | -1.10 | -0.97 |
| D7, D8, R59, R67 (new) | both | +0.02 | +0.02 | +0.01 |
| T-0159 merges (0603 → 0402, fewer lines) | both | about -0.01 | -0.01 | -0.01 |
| L2, C22, R73 | DNP, not on the assembly BOM | 0 | 0 | 0 |
| **Net per pdm-4ch** | | **about -4.8 $** | **-4.1 $** | **-3.6 $** |
| **Net per pdm-hc2** | | +0.01 $ | +0.01 $ | 0 |

Change since the last report (2026-11-05): the J10/Q30 lever of that report is done and the saving matches the estimate. The 4ch order of
5 PCBs / 2 assembled (decision 99) saves about 10 $ on parts and about 4–5 $ on connector sets in total.

## Levers

### L1 – Q30 swap done: saving confirmed (INFO)
IPT007N06N → AGM601LL saves 2.0–2.7 $ per board, no new fee. Stock 2016 (live), single maker (AGM-Semi), not an Infineon second source. Must-stay: the heat budget was
redone in T-0158 (Tj 66–80 °C at 16 A, STATUS), not re-judged here. Cheaper equivalent: none needed.

### L2 – C577772 is out of stock; pick the J10 source before the order (see F1)
Alternatives at 7.62 mm / 32 A on the JLC catalog, all extended: C7422678 (DORABO DB3ERC-7.62-2P-GN, 394 in stock, 0.73 $; closed socket, different footprint),
C577767 (KF2EDGSR-7.62-2P, 129, 0.45 $; the same maker, the footprint has to be checked against the drawing). No basic or preferred exists.

## Rule findings

- **F1 (MINOR, pdm-4ch, J10 C577772):** JLCPCB/LCSC stock is **0** today (`jlc_get_part`, `jlc_stock_check`, 2026-11-07), the listing shows MOQ 18, reel 40. STATUS and decision 98 note
  say 40 pieces (earlier snapshot). The mating plug C577752 has 63. J10 is hand-soldered and bought by the owner (decision 85), so assembly is not blocked, but the owner's sample/order
  for decision 98 may be. The same code is also pdm-hc2's J11 (hc2 needs 2–3 per board), so the demand doubles on one thin code. Cheapest fix: re-check the stock before the order and name a fallback
  (C577767 or C7422678, both need the footprint checked), no design change now.
- Single-source / low stock (< 500): C577772 (0), C577752 (63), C6394053 (39 for the hc2 J10) and C6394029 (50), AGM601LL (2016, one maker, fine), L1/L2 C96963 (1221). Connector codes are the known thin ones already in decision 98.
- Extended where a basic fits: none new. C96963 and C170101 have no basic equivalent for 8.2 µH 6045 / 2.2 µF 100 V.
- Non-standard values: none new (2.2 k, 22 k, 68 k, 10 Ω, 8.2 µH are E-series).
- T-0161 is no bigger than needed on cost: L2/C22/R73 are DNP, reuse existing codes, add no fee and no placement cost. JP1 is copper. Fine.
- T-0160: two LEDs and two 2.2 k resistors (0.02 $), basic; fine.
- T-0159: the merges lowered the line count and used cheaper 0402; C13 intentionally stays C28323 (documented).

## Questions for the owner

- Q1: Is it OK to treat C577772 as "buy when back in stock" and decide on the fallback (C577767) only if it is still out at order time? Default: yes.

## Not checked

The JLCPCB loading fee (3.07 $) and the PCB price were not re-fetched; this re-check only prices the delta. Footprints, heat budget and the correctness of the changes (validator's job) were not
reviewed. Total board costs are as in `2026-11-05-cost-system.md` (about 218 $ for the 4ch order) minus about 10 $ parts and 4–5 $ connectors if the stock allows.

<!-- findings:begin -->
```json
[
  {
    "id": "C1",
    "kind": "finding",
    "severity": "MINOR",
    "board": "pdm-4ch",
    "location": "J10 KF2EDGSRM-7.62-2P C577772",
    "summary": "C577772 shows stock 0 (MOQ 18) on 2026-11-07; STATUS says 40, and pdm-hc2 J11 uses the same code",
    "fix": "Recheck stock before ordering and name a fallback (C577767 or C7422678, footprint check needed); no design change now",
    "door": "two-way",
    "reason": "a connector code is a BOM and footprint choice, undone by a commit before the order",
    "touches": [],
    "cost_delta_usd": 0.0
  },
  {
    "id": "C2",
    "kind": "lever",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "Q30 AGM601LL C5464765 and J10 C577772 / C577752",
    "summary": "T-0158 saves about 4.8 $ per board at 5 (Q30 2.7 $, J10 set 2.2 $) with no new extended part; confirmed",
    "fix": "none needed",
    "door": "two-way",
    "reason": "done, in git, revertible",
    "touches": [],
    "cost_delta_usd": -4.8
  },
  {
    "id": "C3",
    "kind": "question",
    "severity": "INFO",
    "board": "pdm-4ch",
    "summary": "May C577772 be bought when it is back in stock, with C577767 as fallback after a footprint check?",
    "default": "yes",
    "door": "two-way",
    "reason": "a sensible default exists; the connector can change before the order",
    "touches": []
  }
]
```
<!-- findings:end -->
