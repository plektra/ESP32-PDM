# Cost re-check, system – 2026-11-08 (T-0194)

Scope: `git diff a58f6c897a96 -- hardware lib docs/design-notes.md`. Only the two cost-lever swaps from
`2026-11-07-cost-system-2.md` (L5 → T-0190, L6 → T-0191) changed in the design. Prices: JLCPCB live lookup via pcbparts, 2026-11-08.

## Figures

| Change | Old | New | Part price 1+ | Library type | Where |
|---|---|---|---|---|---|
| C3 (+3V3) | C377773 2.2 µF/50 V X5R 0805 | C170101 2.2 µF/100 V X7R 1206 | 0.0375 → 0.1181 $ (+0.081) | basic → **extended** (already on both BOMs) | both boards, 1 part each |
| R105/R205 (VS→EN) | C26083 1 MΩ 0402 | C17927 1 MΩ 1 % 1206 (200 V) | 0.0012 → 0.0042 $ (+0.003 each) | basic → basic (already R13) | pdm-hc2, 2 parts |

Stock: C170101 121 066; C17927 3 290 910 (both far above 500). Removed: C377773 (985 674), C26083 (2 733 631).
Grep of all sheets: C377773 and C26083 no longer appear anywhere, so each swap really removes one unique line.

Unique parts per board (fix_check figures in STATUS, consistent with my grep):

| Board | Before | After | Change |
|---|---|---|---|
| pdm-4ch | 60 | 59 | −1 (C377773) |
| pdm-hc2 | 65 | 63 | −2 (C377773, C26083) |

Unique extended parts: unchanged (C170101 was already on both BOMs, so no new extended line; the two removed parts were basic).

Order effect, Standard-assembly basis of the last report (1.53 $ per unique line, basic and extended alike):
- pdm-4ch first order (2 assembled): −1.53 + 2 × 0.081 = **−1.37 $**.
- pdm-hc2 per order of n assembled: −3.06 + n × (0.081 + 0.006) = −2.9 $ at n = 2, about −2.6 $ at n = 5 (this basis counts the lines the same way for basic and extended).
- Economic basis (3.07 $ per unique extended part): the swaps save nothing there, since the removed parts are basic and C170101 was already counted; they cost +0.08 $ per part. The saving exists only on the Standard basis, which the last report used.
New first-order pdm-4ch total: about 204 $ − 1.4 $ ≈ 202.6 $ (about 218 $ with the fixture fee). Change since last report: −1.4 $.

## Correctness, completeness, size of each change

- T-0190 (C3): only Value, Footprint and LCSC of C3 changed in the two `power-usb` copies; the file diff is 3 properties per sheet. Nominal 2.2 µF unchanged, ceramic, U3 has no C_OUT maximum or ESR limit per design-notes §8.8. Minimal, complete. The 1206 land is a layout note for the PCB phase.
- T-0191 (R105/R205): only Footprint and LCSC of the two resistors changed, one hc_channel sheet (instances shared by both channels). Value and nets unchanged. Minimal, complete. The design-notes table cell was updated.
- No part was added, no DNP, no other file touched in hardware or lib. No further cheaper equivalent exists: both targets are already the cheapest parts on the BOM for the value (C17927 basic 0.0042 $).

## Levers

None new. A possible small one, not proposed as a change: C3 in basic 0805 (C377773) costs 0.08 $ less per part, but only matters on the Economic basis; keeping C170101 is right on the Standard basis.

## Rule findings

No finding: both new parts are in stock (> 500), standard values (E12/E24), already on the BOM. C170101 is extended (single maker, Samsung, which was already the case before). C17927 and C26083 are both Uniroyal (single source, already so).

## Questions for the owner

None.

## Not checked

- Datasheet/DC-bias of C170101 at 3.3 V (qualitative only in design-notes; validator's job).
- Which assembly basis (Standard vs Economic) the real quote uses; whether the fixture fee applies is for the owner to check on the quote.
- PCB layout footprint room for the two 1206 lands.
- Full BOM re-export: unique counts taken from STATUS (fix_check) and my grep of LCSC fields, not from a fresh kicad-cli export.

<!-- findings:begin -->
```json
[]
```
<!-- findings:end -->
