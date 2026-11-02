# Part facts

Verified facts of the parts used on the boards, one file per part (`<LCSC code>.md`, or the maker part number when
there is no LCSC code). Written by the `part-facts` agent through `tools/part_facts.py`; agents read these before
looking anything up again, so each datasheet is read once. Text only – never a manufacturer PDF (public repo).

A wrong fact here would spread to every later package: when you find one, correct the file and note it in
`docs/design-notes.md`. The validator re-checks critical figures (pinout, absolute maximum ratings) against the cited
page instead of trusting this cache.

## Format

```markdown
# <maker part number> (<LCSC code>)

Maker: … · Package: … · JLCPCB: basic/preferred/extended, stock … (date)
Datasheet: <title>, rev. …, <date>, <URL>
Checked: <date> by <task id>

| Item | Value | Source |
|---|---|---|
| Pinout | 1 = …, 2 = … | p. 3, Fig. 2 |
| Absolute max … | … | p. 4, Table 1 |
| … | … | … |

Notes: conditions, derating, anything UNVERIFIED and why.
```
