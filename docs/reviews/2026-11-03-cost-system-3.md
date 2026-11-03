# Cost re-check, system – 2026-11-03 (T-0124)

Scope: only what changed since commit 1d30964d8974 (`git diff 1d30964d8974 -- hardware lib docs/design-notes.md`). Change only priced; untouched circuits and earlier findings not repeated. Prices from `jlc_get_part` on 2026-11-03 (JLCPCB/LCSC list prices); extended loading fee 3.07 USD per unique extended part per order (JLCPCB blog citing its PCBA price page of 2026-10-09, found by web search; confirm before ordering).

## Figures

Changes since the baseline (packages T-0118, T-0119, T-0120, T-0121; lib = two new symbols only, no cost):

| Change | Parts | Library | Unit price |
|---|---|---|---|
| F1–F4 1812L050/60GR C19078719 (3×) and SMD0805B050TF C269104 (1×) → mSMD050-60V C70113 (4×) | −4 +4 | all extended | 0.0643 / 0.024 → 0.088 (1+), 0.0727 (50+) |
| R54–R56 new 0.2 Ω 2512 FRM252WJR200TK C7420022 (3×) | +3 | extended | 0.0283 (1+) |
| C18 4.7 nF/1 kV C107198 → 1 nF/2 kV C9196 | swap | extended → **basic** | 0.0183 → 0.0228 |
| C104–C404 1 µF/100 V C13832 → 2.2 µF/100 V C170101 (4×, pdm-4ch) | swap | extended → extended (already on BOM as C1/C30) | 0.0645 → 0.1185 (1+) |
| pdm-4ch only: Q30 IPT007N06N C122552 | +1 | extended | 3.5507 / 3.0619 / 2.7569 (1/10/30+) |
| pdm-4ch only: U30 LM74500-Q1 C5219210 | +1 | extended | 1.8155 / 1.5482 / 1.3809 |
| pdm-4ch only: C32 1 µF/50 V C15849 | +1 | basic | 0.0145 |

Unique extended parts (loading fee each, per order):

| Board | Removed | Added | Net | Fee change per order |
|---|---|---|---|---|
| pdm-4ch | C19078719, C269104, C107198, C13832 (4) | C70113, C7420022, C122552, C5219210 (4) | **0** | 0.00 USD |
| pdm-hc2 | C19078719, C269104, C107198 (3) | C70113, C7420022 (2) | **−1** | −3.07 USD |

Absolute counts are not re-derived here (STATUS.md of pdm-4ch reports 61 unique parts in total, +2 from T-0121 before the other swaps).

Cost change per board (parts + loading fee share), at 5 / 10 / 30 boards per order (qty-tier prices; tier effects on the small parts approximated):

| Board | 5 boards | 10 boards | 30 boards | Main driver |
|---|---|---|---|---|
| pdm-4ch parts | +5.83 | +5.07 | +4.54 | Q30 3.55/3.06/2.76 and U30 1.82/1.55/1.38; rest ≈ +0.4–0.5 (PTC +0.14, R54–R56 +0.09, C104–C404 +0.13–0.22, C32/C18 ≈ 0.02) |
| pdm-4ch loading fee | 0 | 0 | 0 | 4 out, 4 in |
| **pdm-4ch total** | **+5.83** | **+5.07** | **+4.54** | |
| pdm-hc2 parts | +0.22 | +0.22 | +0.18 | PTC +0.135, R54–R56 +0.085 |
| pdm-hc2 loading fee | −0.61 | −0.31 | −0.10 | one extended type fewer |
| **pdm-hc2 total** | **−0.39** | **−0.09** | **+0.08** | |

Change since the last cost report: this is the first cost figure after these packages; the baseline is the state at 1d30964. The pdm-4ch increase is almost entirely the reverse-battery blocker (T-0121, owner ruling Q-0054): 4.6–5.4 USD per board for Q30+U30.

Correct and complete? Each swap does what its item needed and no more: T-0118 reuses one PTC type for all four positions (F2 also moves to C70113, which removes C269104, good); T-0119 moves C18 to a part already on the BOM and basic; T-0120 reuses C170101; T-0121 adds exactly three parts. Nothing oversized found except Q30's choice of the most expensive TOLL part (lever L1). Stock: C70113 70011, C7420022 53240, C122552 4707, C5219210 2923, C9196 1.7 M, C170101 134000, C15849 12 M – all above 500; C122552 and C5219210 are the thinnest and single-source (Infineon, TI).

## Levers

| # | Saving per pdm-4ch board | Change | Trade-off | Must-stay check | Effort |
|---|---|---|---|---|---|
| L1 | ≈ 2.2 USD at 10 boards (3.06 → 0.85); ≈ 2.7 at 5; ≈ 1.9 at 30 | Q30 IPT007N06N C122552 → AGM601LL C5464765 (AGM-Semi, TOLL-8L, 60 V, 1.25 mΩ @10 V, stock 2016, extended, 0.85 USD) – same package family, same unique-extended count | R_DS(on) 0.75 → 1.25 mΩ: Q30 dissipation at 40 A rises from ≈ 1.2 W to ≈ 2 W (more hot), Tj 122 °C is not margin enough to assume; heat budget must be rerun (`tools/heat_budget.py --r-path`); second-source brand, no EasyEDA/datasheet check done here; pinout and pad drawing of TOLL-8L must equal the `Infineon_PG-HSOF-8-1` land | Reverse-battery protection kept; heat budget (decision 9) must still pass at 40 °C, otherwise drop the lever | small (symbol/footprint check, heat run) | `jlc_search` 2026-11-03; `jlc_get_part` C122552 |
| L2 | ≈ 0 – 0.8 USD per order | C104–C404 back to 1 µF C13832 only for runs of ≥ 15 pdm-4ch boards per order | break-even: loading fee 3.07 vs +0.216 per board (qty-1 prices) ≈ 14 boards; 30 boards: extra parts ≈ 3.9 > 3.07 | none touched | none now; revisit when run size is known | `jlc_get_part` C13832/C170101 |

No cheaper basic/preferred equivalent exists for C70113, C7420022, C122552, C5219210 (`jlc_search library_type=no_fee`: 0 PTC 60 V ≥ 0.5 A in 1812, 0 current-sense 0.2 Ω 2512, 0 MOSFET 60 V ≤ 2 mΩ ≥ 100 A; 26 / 22 / 343 extended match). The LM74500 has no cheaper drop-in; skipped.

## Rule findings

- All four new parts are extended where no basic/preferred part fits (see above) – accepted, no finding.
- Loading-fee net: pdm-4ch 0, pdm-hc2 −1 extended type.
- Non-standard values: R54–R56 200 mΩ is E24-sensible (0.2 Ω); fine.
- Stock below 500: none. Single-source: Q30, U30 (Infineon, TI).
- Footprint checks before ordering are already in STATUS.md (Fuse_1812, R_2512, PG-HSOF-8-1, TSOT-23-8); not repeated.

## Questions for the owner

- Q1: Is a Q30 with 1.25 mΩ (L1) acceptable if the heat budget passes? Default: yes, if Tj stays within the existing margin.

## Not checked

PCB, panel, enclosure, hand-soldering and setup/stencil figures (re-check scope: change only); datasheet of AGM601LL; heat budget rerun; absolute extended-type counts per board; exact tier prices of small parts at each quantity (approximated).

<!-- findings:begin -->
```json
[
  {
    "id": "L1",
    "kind": "lever",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "root sheet: Q30 IPT007N06N C122552",
    "summary": "Q30 is the most expensive new part (3.06 USD at 10 boards); AGM601LL C5464765 (TOLL-8L, 60 V, 1.25 mΩ, 0.85 USD) would save about 2.2 USD per board if the heat budget still passes",
    "fix": "check TOLL-8L pinout against Infineon_PG-HSOF-8-1, rerun tools/heat_budget.py with Q30 at 1.25 mΩ, swap if it passes",
    "door": "two-way",
    "reason": "part swap before any order, no decision named, reverse-battery protection and heat budget kept (policy: part swaps)",
    "touches": ["protection"],
    "cost_delta_usd": -2.2
  },
  {
    "id": "L2",
    "kind": "lever",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "channel: C104-C404 C170101",
    "summary": "C170101 instead of C13832 saves the loading fee only below about 14 boards per order; above that C13832 is cheaper",
    "fix": "revisit at order time if the run is 15 boards or more",
    "door": "two-way",
    "reason": "capacitor value change within decision 26 range, cheap to revert",
    "touches": []
  },
  {
    "id": "Q1",
    "kind": "question",
    "severity": "INFO",
    "board": "pdm-4ch",
    "summary": "Accept a Q30 with 1.25 mΩ instead of 0.75 mΩ if the heat budget passes (L1)?",
    "default": "yes, if Tj stays within the existing margin",
    "door": "two-way",
    "reason": "a sensible default exists and the swap is a git revert",
    "touches": []
  }
]
```
<!-- findings:end -->
