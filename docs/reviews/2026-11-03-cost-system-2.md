# Cost re-check – system, changes since d6cef248342f (T-0111)

Date: 2026-11-03, unattended. Scope: price the change only (`git diff d6cef248342f -- hardware lib docs/design-notes.md`,
fix rounds T-0104 … T-0108). Baseline: `2026-11-03-cost-system.md` (19 extended types pdm-4ch, 20 pdm-hc2 at that
report's counts, before T-0107). Prices: pcbparts `jlc_get_part`, 1+ tier, 2026-11-03. Loading fee 3.07 $ per unique
extended part and order (unchanged, JLCPCB PCBA price page as quoted in the baseline report). PCB prices remain the
baseline estimates (15 / 20 / 38 $ per order, ±50 %).

## Figures

Part changes (all checked against the BOM from `tools/sch_query.py … parts`):

| Change | Parts | Library | Unit price (1+) | Δ per board |
|---|---|---|---|---|
| R3/R4/R7/R8 4.7 k C17936 → 2 k C17944 (T-0105) | 4 swapped | basic → basic | 0.0077 → 0.0078 | +0.0004 $ |
| R45–R48 2 k C17944 added (T-0105) | +4 | basic | 0.0078 | +0.031 $ (both boards) |
| RIS R103…R403 680 Ω C17975 → 1 k C4410, + R107…R407 (T-0107, 4ch) | 4 swapped, +4 | extended → **basic** | 0.0054 → 0.0085 | +0.046 $ |
| C30 1 µF C13832 → 2.2 µF C170101 (T-0107, both) | 1 | extended → extended (already on both boards as C1) | 0.0645 → 0.1185 | +0.054 $ |
| C102/C202 same swap (HC2) | 2 | extended → extended | same | +0.108 $ |
| R104/R204 10 → 10 k C25744; R115/R215 10 Ω C25077; R116/R216 0 Ω C17168; C114/C214 1 nF/2 kV C9196 (T-0106, HC2) | +6, 2 swapped | all basic | 0.0012–0.0228 | +0.056 $ |

Unique extended parts per order (loading fee):

| Board | Before | After | Removed | Added | Fee change per order |
|---|---|---|---|---|---|
| pdm-4ch | 19 | **18** | C17975 | none (C170101 already present) | −3.07 $ |
| pdm-hc2 | 20 | **19** | C13832 | none | −3.07 $ |

C13832 stays on pdm-4ch (C104–C404, confirmed decision 26; open owner question from T-0107). Part count grew: pdm-4ch
+8, pdm-hc2 +14 parts (all basic), but unique parts did not rise. Stock of every new code is above 130 k (C17975 gone).

Per board, parts Δ and order effect, with the baseline totals corrected (Economic PCBA, 2 oz, PCB estimate):

| Board | Qty | Parts Δ per board | Fee Δ per board | New per-board total | Baseline | Change |
|---|---|---|---|---|---|---|
| pdm-4ch | 5 | +0.13 $ | −0.61 $ | **34.40 $** | 34.88 $ | −0.48 $ |
| pdm-4ch | 10 | +0.13 $ | −0.31 $ | **25.25 $** | 25.42 $ | −0.18 $ |
| pdm-4ch | 30 | +0.13 $ | −0.10 $ | **19.07 $** | 19.04 $ | +0.03 $ |
| pdm-hc2 | 5 | +0.25 $ | −0.61 $ | **40.76 $** | 41.12 $ | −0.36 $ |
| pdm-hc2 | 10 | +0.25 $ | −0.31 $ | **31.13 $** | 31.19 $ | −0.06 $ |
| pdm-hc2 | 30 | +0.25 $ | −0.10 $ | **24.22 $** | 24.07 $ | +0.15 $ |

(Parts Δ uses 1+ prices, so it is slightly high at 30 boards; joint cost change is below 0.01 $ per board.)

## Levers

None new. The saving the changes bring (two fee removals) is already booked above.

## Rule findings

- Fee goal of the round met: two unique extended parts gone (C17975, C13832-on-HC2), no basic part replaced by an
  extended one, no new unique part. C17936 (4.7 k) left the BOM; C17944 was already basic and stock is 1.8 M.
- **C30 swap on pdm-4ch gains nothing.** C13832 stays on pdm-4ch, so C30 → C170101 there only adds 0.054 $ per board
  (about 0.5 $ per order of 10) with no fee saved. C30 is on the shared root sheet; keeping the swap keeps both
  boards identical, which is why it is probably right. Cheaper only if the root sheet were allowed to differ per board:
  not worth it. If the owner approves C104–C404 → C170101 (T-0099 question) this is moot.
- **HC2 C13832 removal pays only up to about 19 boards.** Three swaps cost +0.162 $ per board at 1+ prices against a
  3.07 $ fee, so break-even is about 19 boards at 1+ prices (T-0107 states 15+; tier prices move it a little). For the
  planned 5–30 boards the swap is neutral to positive; above about 20 boards revert C102/C202/C30 to C13832.
- No non-standard value added: 2 k, 1 k, 10 k, 10 Ω, 0 Ω are E24/E12, all 1 % thick film; 1 nF/2 kV, 2.2 µF/100 V standard.
- Single source: C170101 (Samsung) and C9196 (FH) are single-manufacturer parts, as C13832 was. No alternative is
  needed for 100 V X7R at this price.
- Cheaper equivalents checked: the 2 k + 2 k pair (4 × 1206 per board of extra parts, 0.03 $) cannot be one 4 k part
  because of the 0.29 W clamp stress per part (T-0105); RIS 2 × 1 k keeps 0.25 W rating per part. No cheaper
  equivalent exists.
- The T-0104 PTC/series-resistor step changed no part (no cost effect). Its open options would add one extended part
  (alloy shunt C7420022, +3.07 $ per order per board and 0.028 $ per part) or 6 basic parts; already raised as an
  owner question there, not repeated.

## Questions for the owner

- None new. Existing open items: pdm-4ch C104–C404 → C170101 (saves 3.07 $ per order up to about 9 boards) and C18 → C9196.

## Not checked

- Footprints and JLCPCB-side footprint match for new parts (C170101 and C4410 have EasyEDA footprints; not compared).
- design-notes.md diff (text only, 219 lines) was not read beyond what the fix reports say.
- Live quote for PCB 2 oz; shipping, customs, plug halves, enclosure (baseline estimates stand).
- Electrical correctness of the changes (validator's job).

<!-- findings:begin -->
```json
[
  {
    "id": "C1",
    "kind": "finding",
    "severity": "INFO",
    "board": "pdm-4ch",
    "location": "root sheet: C30 (C170101)",
    "summary": "C30 swap to 2.2 uF C170101 adds about 0.054 USD per board on pdm-4ch with no fee saved, because C13832 stays at C104-C404",
    "fix": "none now; becomes free of cost when C104-C404 are also changed to C170101 (open owner question from T-0107)",
    "door": "two-way",
    "reason": "one component value on a shared sheet, easy to change back",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.054
  },
  {
    "id": "C2",
    "kind": "finding",
    "severity": "INFO",
    "board": "pdm-hc2",
    "location": "C30, C102, C202 (C170101)",
    "summary": "C13832 removal costs 0.162 USD per board against a 3.07 USD fee per order, so it pays only up to about 19 boards per order",
    "fix": "for orders above about 20 HC2 boards revert C30/C102/C202 to C13832; no change for 5-30 boards planned now",
    "door": "two-way",
    "reason": "component values, reversible at order time",
    "touches": ["shared-sheet"],
    "cost_delta_usd": 0.162
  },
  {
    "id": "Q1",
    "kind": "question",
    "severity": "INFO",
    "board": "pdm-4ch",
    "summary": "May pdm-4ch C104-C404 change to C170101 (already open from T-0107)? It removes C13832 from the 4ch BOM (-3.07 USD per order) and is cheaper up to about 9 boards",
    "default": "keep 1 uF C13832 at C104-C404 until the owner rules",
    "door": "one-way",
    "reason": "confirmed decision 26 names 1 uF/100 V at each BTT6050 VS tab",
    "touches": []
  }
]
```
<!-- findings:end -->
